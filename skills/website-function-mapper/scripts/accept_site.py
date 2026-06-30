#!/usr/bin/env python3
import argparse
import asyncio
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from map_site import ScanConfig, SiteMapper


@dataclass
class AcceptanceConfig:
    reference_url: str | None
    replica_url: str | None
    reference_report: Path | None
    replica_report: Path | None
    out: Path
    reference_storage_state: Path
    replica_storage_state: Path
    reference_cookies: Path | None
    replica_cookies: Path | None
    wait_login: bool
    headless: bool
    max_pages: int
    max_depth: int
    branch_limit: int
    timeout: int
    min_score: int
    fail_under: bool


class ReplicaAcceptance:
    def __init__(self, config: AcceptanceConfig) -> None:
        self.config = config

    async def run(self) -> dict[str, Any]:
        self.config.out.mkdir(parents=True, exist_ok=True)
        reference = await self._load_or_scan("reference")
        replica = await self._load_or_scan("replica")
        result = self._compare(reference, replica)
        self._write(result)
        if self.config.fail_under and result["score"] < self.config.min_score:
            raise SystemExit(2)
        return result

    async def _load_or_scan(self, side: str) -> dict[str, Any]:
        report_path = self.config.reference_report if side == "reference" else self.config.replica_report
        url = self.config.reference_url if side == "reference" else self.config.replica_url
        if report_path:
            return json.loads(report_path.read_text(encoding="utf-8-sig"))
        if not url:
            raise ValueError(f"{side} 需要提供 URL 或 report.json")
        storage_state = (
            self.config.reference_storage_state if side == "reference" else self.config.replica_storage_state
        )
        cookies = self.config.reference_cookies if side == "reference" else self.config.replica_cookies
        scan_out = self.config.out / side
        scan_config = ScanConfig(
            url=url,
            out=scan_out,
            storage_state=storage_state,
            cookies=cookies,
            wait_login=self.config.wait_login,
            headless=self.config.headless,
            max_pages=self.config.max_pages,
            max_depth=self.config.max_depth,
            branch_limit=self.config.branch_limit,
            timeout=self.config.timeout,
            min_acceptance_score=0,
            fail_under_acceptance=False,
        )
        mapper = SiteMapper(scan_config)
        await mapper.run()
        return mapper.report

    def _compare(self, reference: dict[str, Any], replica: dict[str, Any]) -> dict[str, Any]:
        reference_features = self._features(reference)
        replica_features = self._features(replica)
        sections = [
            self._compare_set("pages", reference_features["pages"], replica_features["pages"], 10),
            self._compare_set("buttons", reference_features["buttons"], replica_features["buttons"], 15),
            self._compare_set("forms", reference_features["forms"], replica_features["forms"], 15),
            self._compare_set("fields", reference_features["fields"], replica_features["fields"], 20),
            self._compare_set("constraints", reference_features["constraints"], replica_features["constraints"], 15),
            self._compare_set("dynamic_branches", reference_features["dynamic_branches"], replica_features["dynamic_branches"], 10),
            self._compare_set("documents", reference_features["documents"], replica_features["documents"], 5),
            self._compare_set("api_shapes", reference_features["api_shapes"], replica_features["api_shapes"], 10),
        ]
        score = sum(section["score"] for section in sections)
        missing_total = sum(len(section["missing"]) for section in sections)
        mismatch_total = sum(len(section["mismatched"]) for section in sections)
        status = "passed" if score >= self.config.min_score and missing_total == 0 and mismatch_total == 0 else "needs_review"
        return {
            "status": status,
            "score": score,
            "max_score": sum(section["weight"] for section in sections),
            "min_score": self.config.min_score,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "reference": reference.get("target"),
            "replica": replica.get("target"),
            "sections": sections,
            "recommendations": self._recommendations(sections),
            "metrics": {
                "missing_total": missing_total,
                "mismatch_total": mismatch_total,
                "extra_total": sum(len(section["extra"]) for section in sections),
                "reference": {key: len(value) for key, value in reference_features.items()},
                "replica": {key: len(value) for key, value in replica_features.items()},
            },
        }

    def _features(self, report: dict[str, Any]) -> dict[str, dict[str, Any]]:
        features = {
            "pages": {},
            "buttons": {},
            "forms": {},
            "fields": {},
            "constraints": {},
            "dynamic_branches": {},
            "documents": {},
            "api_shapes": {},
        }
        for page in report.get("pages", []):
            page_key = self._page_key(page)
            features["pages"][page_key] = {"title": page.get("title"), "path": urlparse(page.get("url") or "").path}
            for button in page.get("buttons", []):
                key = self._norm(button.get("text") or button.get("aria_label") or "")
                if key:
                    features["buttons"][f"{page_key}::{key}"] = {
                        "text": button.get("text"),
                        "dangerous": button.get("dangerous"),
                        "disabled": button.get("disabled"),
                    }
            for form in page.get("forms", []):
                form_key = f"{page_key}::{self._norm(form.get('title') or str(form.get('index')))}"
                features["forms"][form_key] = {
                    "title": form.get("title"),
                    "field_count": len(form.get("fields", [])),
                    "button_count": len(form.get("buttons", [])),
                }
                for field in form.get("fields", []):
                    field_key = f"{form_key}::{self._field_key(field)}"
                    features["fields"][field_key] = {
                        "label": field.get("label"),
                        "type": field.get("attributes", {}).get("type") or field.get("tag"),
                        "options": self._option_labels(field),
                    }
                    features["constraints"][field_key] = field.get("constraint", {})
            for branch in page.get("dynamic_form_branches", []):
                control = branch.get("control", {})
                option = branch.get("selected_option", {})
                key = "::".join(
                    [
                        page_key,
                        self._field_key(control),
                        self._norm(str(option.get("label") or option.get("value") or "")),
                    ]
                )
                if key.strip(":"):
                    features["dynamic_branches"][key] = {"changed": branch.get("changed")}
        for doc in report.get("documents", []):
            key = self._norm(doc.get("title") or doc.get("label") or doc.get("url") or "")
            if key:
                features["documents"][key] = {
                    "kind": doc.get("kind"),
                    "path": urlparse(doc.get("url") or "").path,
                }
        for endpoint in report.get("api_endpoints", []):
            key = self._api_key(endpoint)
            if key:
                features["api_shapes"][key] = {
                    "request_fields": sorted(endpoint.get("request_fields", [])),
                    "response_fields": sorted(endpoint.get("response_fields", [])),
                }
        return features

    def _compare_set(
        self,
        name: str,
        reference: dict[str, Any],
        replica: dict[str, Any],
        weight: int,
    ) -> dict[str, Any]:
        reference_keys = set(reference)
        replica_keys = set(replica)
        missing = sorted(reference_keys - replica_keys)
        extra = sorted(replica_keys - reference_keys)
        common = sorted(reference_keys & replica_keys)
        mismatched = []
        for key in common:
            diff = self._diff_value(reference[key], replica[key])
            if diff:
                mismatched.append({"key": key, "diff": diff})
        if not reference_keys:
            score = weight
        else:
            matched = len(common) - len(mismatched)
            score = max(0, round(weight * (matched / len(reference_keys))))
        return {
            "name": name,
            "weight": weight,
            "score": score,
            "passed": not missing and not mismatched,
            "reference_count": len(reference_keys),
            "replica_count": len(replica_keys),
            "missing": missing[:200],
            "extra": extra[:200],
            "mismatched": mismatched[:200],
        }

    def _diff_value(self, reference: Any, replica: Any) -> dict[str, Any]:
        if not isinstance(reference, dict) or not isinstance(replica, dict):
            return {} if reference == replica else {"reference": reference, "replica": replica}
        diff = {}
        for key, value in reference.items():
            if key not in replica:
                diff[key] = {"reference": value, "replica": "<missing>"}
                continue
            if self._stable(value) != self._stable(replica[key]):
                diff[key] = {"reference": value, "replica": replica[key]}
        return diff

    def _stable(self, value: Any) -> Any:
        if isinstance(value, list):
            return sorted(str(item) for item in value)
        return value

    def _recommendations(self, sections: list[dict[str, Any]]) -> list[str]:
        messages = {
            "pages": "新系统缺少参考系统的页面或入口，先补齐导航和路由。",
            "buttons": "新系统按钮/动作入口不一致，核对按钮文案、启用状态和危险动作标记。",
            "forms": "新系统表单数量或分组不一致，核对弹窗、抽屉、分步表单和 Tab 表单。",
            "fields": "新系统字段不一致，优先补齐缺失字段、字段类型和选项。",
            "constraints": "新系统字段约束不一致，补齐必填、长度、范围、格式、文件类型和只读/禁用规则。",
            "dynamic_branches": "新系统动态表单联动不一致，复查下拉、单选、开关、级联选择后的字段变化。",
            "documents": "新系统帮助/API 文档入口不一致，确认是否需要同步用户手册或开发文档。",
            "api_shapes": "新系统接口线索不一致，核对请求字段、响应字段和接口路径。",
        }
        return [messages[section["name"]] for section in sections if not section["passed"]]

    def _write(self, result: dict[str, Any]) -> None:
        json_path = self.config.out / "replica-acceptance.json"
        md_path = self.config.out / "replica-acceptance.md"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(self._render_markdown(result), encoding="utf-8")
        print(f"复刻验收报告: {md_path}")
        print(f"复刻验收数据: {json_path}")
        print(f"复刻验收状态: {result['status']} {result['score']}/{result['max_score']}")

    def _render_markdown(self, result: dict[str, Any]) -> str:
        lines = [
            "# 复刻系统验收报告",
            "",
            f"- 参考系统: {result.get('reference')}",
            f"- 新系统: {result.get('replica')}",
            f"- 生成时间: {result.get('generated_at')}",
            f"- 状态: {result.get('status')}",
            f"- 分数: {result.get('score')}/{result.get('max_score')}，最低要求 {result.get('min_score')}",
            "",
            "## 对比结果",
        ]
        for section in result["sections"]:
            lines.extend(
                [
                    "",
                    f"### {section['name']}",
                    f"- 得分: {section['score']}/{section['weight']}",
                    f"- 参考数量: {section['reference_count']}，新系统数量: {section['replica_count']}",
                    f"- 缺失: {len(section['missing'])}，新增: {len(section['extra'])}，不一致: {len(section['mismatched'])}",
                ]
            )
            for item in section["missing"][:30]:
                lines.append(f"- 缺失项: {item}")
            for item in section["mismatched"][:30]:
                lines.append(f"- 不一致: {item['key']} => {json.dumps(item['diff'], ensure_ascii=False)}")
        if result["recommendations"]:
            lines.extend(["", "## 修复建议"])
            for recommendation in result["recommendations"]:
                lines.append(f"- {recommendation}")
        return "\n".join(lines) + "\n"

    def _field_key(self, field: dict[str, Any]) -> str:
        attrs = field.get("attributes", {})
        return self._norm(
            field.get("label")
            or attrs.get("name")
            or attrs.get("id")
            or attrs.get("placeholder")
            or field.get("text")
            or ""
        )

    def _page_key(self, page: dict[str, Any]) -> str:
        path = urlparse(page.get("url") or "").path.strip("/")
        return self._norm(path or page.get("title") or "home")

    def _api_key(self, endpoint: dict[str, Any]) -> str:
        parsed = urlparse(endpoint.get("url") or "")
        path = re.sub(r"/\d+(\b|/)", "/:id\\1", parsed.path)
        return f"{endpoint.get('method')} {self._norm(path)}"

    def _option_labels(self, field: dict[str, Any]) -> list[str]:
        return sorted(
            self._norm(str(option.get("label") or option.get("value") or ""))
            for option in field.get("options", [])
            if option.get("label") or option.get("value")
        )

    def _norm(self, value: str) -> str:
        value = re.sub(r"https?://[^/\s]+", "", str(value).lower())
        value = re.sub(r"\s+", " ", value)
        return value.strip(" /#?&")


def default_out(reference: str | None, replica: str | None) -> Path:
    host = urlparse(replica or reference or "acceptance").netloc.replace(":", "_") or "acceptance"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("outputs") / f"replica-acceptance-{host}-{stamp}"


def parse_args() -> AcceptanceConfig:
    parser = argparse.ArgumentParser(description="对照参考系统和新系统，验收功能是否一比一复刻。")
    parser.add_argument("--reference-url", help="参考系统 URL")
    parser.add_argument("--replica-url", help="新系统 URL")
    parser.add_argument("--reference-report", type=Path, help="参考系统 report.json")
    parser.add_argument("--replica-report", type=Path, help="新系统 report.json")
    parser.add_argument("--out", type=Path, help="输出目录")
    parser.add_argument("--reference-storage-state", type=Path, default=Path("reference-storageState.json"))
    parser.add_argument("--replica-storage-state", type=Path, default=Path("replica-storageState.json"))
    parser.add_argument("--reference-cookies", type=Path, help="参考系统 cookie JSON")
    parser.add_argument("--replica-cookies", type=Path, help="新系统 cookie JSON")
    parser.add_argument("--wait-login", action="store_true", help="扫描前等待用户分别完成登录")
    parser.add_argument("--headless", action="store_true", help="使用无头浏览器")
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--max-depth", type=int, default=2)
    parser.add_argument("--branch-limit", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=30000)
    parser.add_argument("--min-score", type=int, default=95, help="复刻验收最低分")
    parser.add_argument("--fail-under", action="store_true", help="低于最低分时返回退出码 2")
    args = parser.parse_args()
    if not (args.reference_url or args.reference_report):
        parser.error("必须提供 --reference-url 或 --reference-report")
    if not (args.replica_url or args.replica_report):
        parser.error("必须提供 --replica-url 或 --replica-report")
    return AcceptanceConfig(
        reference_url=args.reference_url,
        replica_url=args.replica_url,
        reference_report=args.reference_report,
        replica_report=args.replica_report,
        out=args.out or default_out(args.reference_url, args.replica_url),
        reference_storage_state=args.reference_storage_state,
        replica_storage_state=args.replica_storage_state,
        reference_cookies=args.reference_cookies,
        replica_cookies=args.replica_cookies,
        wait_login=args.wait_login,
        headless=args.headless,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        branch_limit=args.branch_limit,
        timeout=args.timeout,
        min_score=args.min_score,
        fail_under=args.fail_under,
    )


def main() -> None:
    config = parse_args()
    acceptance = ReplicaAcceptance(config)
    asyncio.run(acceptance.run())


if __name__ == "__main__":
    main()
