#!/usr/bin/env python3
import argparse
import asyncio
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse

from playwright.async_api import BrowserContext, Page, async_playwright


DANGEROUS_TEXT = re.compile(
    r"(提交|保存|确认|确定|删除|移除|清空|支付|付款|下单|发送|发布|上线|禁用|启用|退款|充值|转账|导入|批量|submit|save|confirm|delete|remove|clear|pay|send|publish|deploy|refund|charge|transfer|import)",
    re.I,
)
DOC_TEXT = re.compile(
    r"(帮助|手册|文档|说明|指南|开发者|接口|api|swagger|openapi|docs|doc|help|manual|guide|faq|reference)",
    re.I,
)
LOGIN_TEXT = re.compile(r"(登录|登陆|sign in|login|账号|密码|验证码)", re.I)
SENSITIVE_HEADER = re.compile(r"(authorization|cookie|token|secret|key|set-cookie)", re.I)


@dataclass
class ScanConfig:
    url: str
    out: Path
    storage_state: Path
    cookies: Path | None
    wait_login: bool
    headless: bool
    max_pages: int
    max_depth: int
    branch_limit: int
    timeout: int
    min_acceptance_score: int
    fail_under_acceptance: bool


class SiteMapper:
    def __init__(self, config: ScanConfig) -> None:
        self.config = config
        parsed = urlparse(config.url)
        self.base_host = parsed.netloc
        self.base_origin = f"{parsed.scheme}://{parsed.netloc}"
        self.visited: set[str] = set()
        self.queue: list[tuple[str, int]] = [(config.url, 0)]
        self.network: list[dict[str, Any]] = []
        self.report: dict[str, Any] = {
            "target": config.url,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "mode": "safe reconnaissance",
            "pages": [],
            "documents": [],
            "api_endpoints": [],
            "coverage_notes": [],
            "acceptance": {},
            "safety": {
                "submitted_forms": False,
                "dangerous_actions_clicked": False,
                "sensitive_values_redacted": True,
            },
        }

    async def run(self) -> None:
        self.config.out.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.config.headless, args=["--start-maximized"])
            context_kwargs: dict[str, Any] = {"viewport": {"width": 1440, "height": 1000}}
            if self.config.storage_state.exists():
                context_kwargs["storage_state"] = str(self.config.storage_state)
            context = await browser.new_context(**context_kwargs)
            await self._add_cookies(context)
            context.on("request", self._on_request)
            context.on("response", self._on_response)

            page = await context.new_page()
            await self._open_initial_page(page)
            await self._crawl(context, page)
            await context.storage_state(path=str(self.config.storage_state))
            self.report["api_endpoints"] = self._summarize_network()
            self.report["acceptance"] = self._build_acceptance()
            self._write_reports()
            await browser.close()
        if self.config.fail_under_acceptance and self.report["acceptance"]["score"] < self.config.min_acceptance_score:
            raise SystemExit(2)

    async def _add_cookies(self, context: BrowserContext) -> None:
        if not self.config.cookies:
            return
        raw = json.loads(self.config.cookies.read_text(encoding="utf-8"))
        cookies = raw if isinstance(raw, list) else raw.get("cookies", [])
        normalized = []
        for cookie in cookies:
            item = dict(cookie)
            if "url" not in item and "domain" not in item:
                item["url"] = self.base_origin
            normalized.append(item)
        if normalized:
            await context.add_cookies(normalized)

    async def _open_initial_page(self, page: Page) -> None:
        await self._goto(page, self.config.url)
        if self.config.wait_login or await self._looks_like_login(page):
            print("检测到可能需要登录。请在打开的浏览器中完成登录，然后回到终端按 Enter 继续。")
            await asyncio.to_thread(input)
            await page.context.storage_state(path=str(self.config.storage_state))
            await page.reload(wait_until="domcontentloaded", timeout=self.config.timeout)

    async def _crawl(self, context: BrowserContext, page: Page) -> None:
        while self.queue and len(self.visited) < self.config.max_pages:
            url, depth = self.queue.pop(0)
            clean = self._clean_url(url)
            if clean in self.visited or not self._same_host(clean):
                continue
            self.visited.add(clean)
            await self._goto(page, clean)
            page_record = await self._scan_page(page, depth)
            self.report["pages"].append(page_record)
            for link in page_record["links"]:
                href = link.get("href")
                if not href:
                    continue
                if DOC_TEXT.search(" ".join([link.get("text", ""), href])):
                    await self._scan_document(context, href, link.get("text", ""))
                if depth < self.config.max_depth and self._same_host(href):
                    normalized = self._clean_url(href)
                    if normalized not in self.visited:
                        self.queue.append((normalized, depth + 1))

    async def _scan_page(self, page: Page, depth: int) -> dict[str, Any]:
        await self._expand_safe_controls(page)
        baseline_forms = await self._collect_forms(page)
        dynamics = await self._explore_dynamic_forms(page, baseline_forms)
        page_text = await self._visible_text(page)
        return {
            "url": page.url,
            "depth": depth,
            "title": await page.title(),
            "summary_text": page_text[:4000],
            "navigation": await self._collect_navigation(page),
            "links": await self._collect_links(page),
            "buttons": await self._collect_buttons(page),
            "forms": baseline_forms,
            "dynamic_form_branches": dynamics,
            "tables": await self._collect_tables(page),
            "document_entry_candidates": await self._collect_doc_candidates(page),
        }

    async def _expand_safe_controls(self, page: Page) -> None:
        selectors = [
            "button",
            "[role=button]",
            "[aria-expanded=false]",
            "[data-toggle]",
            ".dropdown-toggle",
            "summary",
            "[role=tab]",
        ]
        handles = await page.query_selector_all(",".join(selectors))
        for handle in handles[:80]:
            try:
                text = await self._element_text(handle)
                if DANGEROUS_TEXT.search(text):
                    continue
                if not await handle.is_visible():
                    continue
                await handle.click(timeout=1200, trial=True)
                await handle.click(timeout=1200)
                await page.wait_for_timeout(250)
            except Exception:
                continue

    async def _explore_dynamic_forms(self, page: Page, baseline_forms: list[dict[str, Any]]) -> list[dict[str, Any]]:
        branches: list[dict[str, Any]] = []
        controls = await page.query_selector_all("select,input[type=radio],input[type=checkbox]")
        for index, control in enumerate(controls[:40]):
            try:
                if not await control.is_visible() or await control.is_disabled():
                    continue
                descriptor = await self._field_descriptor(control)
                options = await self._control_options(control)
                if not options:
                    continue
                covered = 0
                for option in options[: self.config.branch_limit]:
                    before = await self._field_fingerprint(page)
                    await self._apply_option(control, option)
                    await page.wait_for_timeout(350)
                    after_forms = await self._collect_forms(page)
                    after = await self._field_fingerprint(page)
                    branches.append(
                        {
                            "control_index": index,
                            "control": descriptor,
                            "selected_option": option,
                            "changed": before != after,
                            "new_or_changed_forms": after_forms,
                        }
                    )
                    covered += 1
                if len(options) > covered:
                    self.report["coverage_notes"].append(
                        {
                            "type": "dynamic_options_truncated",
                            "control": descriptor,
                            "covered": covered,
                            "total": len(options),
                        }
                    )
            except Exception as exc:
                self.report["coverage_notes"].append({"type": "dynamic_scan_error", "error": str(exc)})
        return branches

    async def _collect_forms(self, page: Page) -> list[dict[str, Any]]:
        forms = await page.query_selector_all("form, [role=form], .form, .ant-form, .el-form, .modal, .drawer")
        if not forms:
            forms = [await page.query_selector("body")]
        records: list[dict[str, Any]] = []
        for index, form in enumerate([item for item in forms if item is not None][:30]):
            try:
                fields = []
                field_handles = await form.query_selector_all(
                    "input, textarea, select, [contenteditable=true], [role=combobox], [role=spinbutton], [role=switch], [role=checkbox], [role=radio]"
                )
                for field in field_handles:
                    fields.append(await self._field_descriptor(field))
                buttons = []
                for button in await form.query_selector_all("button,input[type=button],input[type=submit],[role=button]"):
                    text = await self._element_text(button)
                    buttons.append(
                        {
                            "text": text,
                            "type": await button.get_attribute("type"),
                            "dangerous": bool(DANGEROUS_TEXT.search(text)),
                            "disabled": await button.is_disabled(),
                        }
                    )
                records.append(
                    {
                        "index": index,
                        "title": await self._nearby_heading(form),
                        "action": await form.get_attribute("action"),
                        "method": await form.get_attribute("method"),
                        "visible": await form.is_visible(),
                        "fields": fields,
                        "buttons": buttons,
                        "validation_messages": await self._collect_validation_messages(form),
                    }
                )
            except Exception:
                continue
        return records

    async def _field_descriptor(self, field: Any) -> dict[str, Any]:
        attrs = {}
        for attr in [
            "name",
            "id",
            "type",
            "placeholder",
            "value",
            "required",
            "min",
            "max",
            "minlength",
            "maxlength",
            "pattern",
            "step",
            "accept",
            "multiple",
            "readonly",
            "disabled",
            "aria-label",
            "aria-required",
            "aria-invalid",
            "autocomplete",
        ]:
            attrs[attr] = await field.get_attribute(attr)
        tag = await field.evaluate("el => el.tagName.toLowerCase()")
        label = await self._label_for(field)
        options = await self._control_options(field)
        return {
            "tag": tag,
            "label": label,
            "text": await self._element_text(field),
            "attributes": self._redact_dict(attrs),
            "visible": await field.is_visible(),
            "disabled": await field.is_disabled(),
            "options": options,
            "constraint": {
                "required": attrs.get("required") is not None or attrs.get("aria-required") == "true",
                "readonly": attrs.get("readonly") is not None,
                "multiple": attrs.get("multiple") is not None,
                "min": attrs.get("min"),
                "max": attrs.get("max"),
                "minlength": attrs.get("minlength"),
                "maxlength": attrs.get("maxlength"),
                "pattern": attrs.get("pattern"),
                "step": attrs.get("step"),
                "accept": attrs.get("accept"),
            },
        }

    async def _control_options(self, field: Any) -> list[dict[str, Any]]:
        tag = await field.evaluate("el => el.tagName.toLowerCase()")
        field_type = (await field.get_attribute("type") or "").lower()
        if tag == "select":
            return await field.evaluate(
                """el => Array.from(el.options).map(o => ({label: o.textContent.trim(), value: o.value, selected: o.selected, disabled: o.disabled}))"""
            )
        if field_type in {"radio", "checkbox"}:
            name = await field.get_attribute("name")
            if name:
                return await field.evaluate(
                    """el => Array.from(document.querySelectorAll(`input[name="${CSS.escape(el.name)}"]`)).map(o => ({label: (document.querySelector(`label[for="${CSS.escape(o.id)}"]`)?.textContent || o.closest('label')?.textContent || o.value || '').trim(), value: o.value, checked: o.checked, disabled: o.disabled}))"""
                )
            return [{"label": await self._label_for(field), "value": await field.get_attribute("value")}]
        role = await field.get_attribute("role")
        if role in {"combobox", "listbox"}:
            text = await self._element_text(field)
            return [{"label": text, "value": text}] if text else []
        return []

    async def _apply_option(self, field: Any, option: dict[str, Any]) -> None:
        tag = await field.evaluate("el => el.tagName.toLowerCase()")
        field_type = (await field.get_attribute("type") or "").lower()
        if tag == "select":
            await field.select_option(value=option.get("value"))
            return
        if field_type == "radio":
            value = option.get("value")
            await field.evaluate(
                """(el, value) => {
                    const target = Array.from(document.querySelectorAll(`input[name="${CSS.escape(el.name)}"]`)).find(o => o.value === value);
                    if (target) { target.click(); }
                }""",
                value,
            )
            return
        if field_type == "checkbox":
            await field.check(timeout=1000)
            return
        await field.click(timeout=1000)

    async def _collect_links(self, page: Page) -> list[dict[str, Any]]:
        return await page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href]')).slice(0, 300).map(a => ({
                text: (a.innerText || a.textContent || '').trim().slice(0, 160),
                href: new URL(a.getAttribute('href'), location.href).href,
                title: a.getAttribute('title') || '',
                target: a.getAttribute('target') || ''
            }))"""
        )

    async def _collect_buttons(self, page: Page) -> list[dict[str, Any]]:
        items = []
        for button in await page.query_selector_all("button,input[type=button],input[type=submit],[role=button]"):
            try:
                text = await self._element_text(button)
                items.append(
                    {
                        "text": text,
                        "type": await button.get_attribute("type"),
                        "aria_label": await button.get_attribute("aria-label"),
                        "dangerous": bool(DANGEROUS_TEXT.search(text)),
                        "disabled": await button.is_disabled(),
                    }
                )
            except Exception:
                continue
        return items[:300]

    async def _collect_navigation(self, page: Page) -> list[dict[str, Any]]:
        return await page.evaluate(
            """() => Array.from(document.querySelectorAll('nav a, [role=navigation] a, aside a, header a, .menu a, .nav a')).slice(0, 200).map(a => ({
                text: (a.innerText || a.textContent || '').trim().slice(0, 160),
                href: a.href
            }))"""
        )

    async def _collect_tables(self, page: Page) -> list[dict[str, Any]]:
        return await page.evaluate(
            """() => Array.from(document.querySelectorAll('table')).slice(0, 20).map((table, index) => ({
                index,
                headers: Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim()),
                sample_rows: Array.from(table.querySelectorAll('tr')).slice(0, 5).map(tr => Array.from(tr.children).map(td => td.innerText.trim()))
            }))"""
        )

    async def _collect_doc_candidates(self, page: Page) -> list[dict[str, Any]]:
        links = await self._collect_links(page)
        return [link for link in links if DOC_TEXT.search(" ".join([link.get("text", ""), link.get("href", "")]))][:50]

    async def _scan_document(self, context: BrowserContext, href: str, label: str) -> None:
        clean = self._clean_url(href)
        if any(item["url"] == clean for item in self.report["documents"]):
            return
        page = await context.new_page()
        try:
            await self._goto(page, clean)
            text = await self._visible_text(page)
            doc = {
                "url": clean,
                "label": label,
                "title": await page.title(),
                "kind": self._document_kind(clean, text),
                "summary_text": text[:8000],
                "links": await self._collect_links(page),
            }
            swagger = await self._extract_openapi(page)
            if swagger:
                doc["openapi"] = swagger
            self.report["documents"].append(doc)
        except Exception as exc:
            self.report["documents"].append({"url": clean, "label": label, "error": str(exc)})
        finally:
            await page.close()

    async def _extract_openapi(self, page: Page) -> dict[str, Any] | None:
        data = await page.evaluate(
            """() => {
                const scripts = Array.from(document.scripts).map(s => s.src || s.textContent || '').join('\\n');
                const text = document.body ? document.body.innerText : '';
                return {text: text.slice(0, 20000), scripts: scripts.slice(0, 20000)};
            }"""
        )
        combined = f"{data.get('text', '')}\n{data.get('scripts', '')}"
        if not re.search(r"(swagger|openapi|GET\s+/|POST\s+/|PUT\s+/|DELETE\s+/)", combined, re.I):
            return None
        endpoints = []
        for method, path in re.findall(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s,;\"']+)", combined, re.I):
            endpoints.append({"method": method.upper(), "path": path})
        return {
            "detected": True,
            "endpoints": self._dedupe_dicts(endpoints)[:200],
            "raw_text_excerpt": combined[:4000],
        }

    async def _collect_validation_messages(self, root: Any) -> list[str]:
        messages = await root.evaluate(
            """el => Array.from(el.querySelectorAll('[role=alert], .error, .invalid-feedback, .ant-form-item-explain, .el-form-item__error, [aria-live]'))
                .map(x => (x.innerText || x.textContent || '').trim())
                .filter(Boolean)
                .slice(0, 80)"""
        )
        return messages

    async def _field_fingerprint(self, page: Page) -> str:
        forms = await self._collect_forms(page)
        payload = json.dumps(forms, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    async def _looks_like_login(self, page: Page) -> bool:
        text = await self._visible_text(page)
        password = await page.query_selector("input[type=password]")
        return bool(password and LOGIN_TEXT.search(text[:3000]))

    async def _goto(self, page: Page, url: str) -> None:
        await page.goto(url, wait_until="domcontentloaded", timeout=self.config.timeout)
        try:
            await page.wait_for_load_state("networkidle", timeout=3000)
        except Exception:
            pass

    async def _visible_text(self, page: Page) -> str:
        text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    async def _element_text(self, element: Any) -> str:
        text = await element.evaluate(
            """el => (el.innerText || el.textContent || el.value || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim()"""
        )
        return re.sub(r"\s+", " ", text)[:300]

    async def _label_for(self, element: Any) -> str:
        return await element.evaluate(
            """el => {
                const id = el.id;
                const label = id ? document.querySelector(`label[for="${CSS.escape(id)}"]`) : null;
                if (label) return label.innerText.trim();
                const wrapped = el.closest('label');
                if (wrapped) return wrapped.innerText.trim();
                const aria = el.getAttribute('aria-label');
                if (aria) return aria;
                const parent = el.closest('.form-item,.form-group,.ant-form-item,.el-form-item,.field');
                if (parent) {
                    const text = Array.from(parent.querySelectorAll('label,.label,.ant-form-item-label,.el-form-item__label')).map(x => x.innerText.trim()).filter(Boolean)[0];
                    if (text) return text;
                }
                return '';
            }"""
        )

    async def _nearby_heading(self, element: Any) -> str:
        return await element.evaluate(
            """el => {
                const heading = el.querySelector('h1,h2,h3,h4,legend,.title,.modal-title,.drawer-title');
                if (heading) return heading.innerText.trim();
                const prev = el.previousElementSibling;
                if (prev && /H[1-4]|LEGEND/.test(prev.tagName)) return prev.innerText.trim();
                return '';
            }"""
        )

    def _on_request(self, request: Any) -> None:
        if request.resource_type not in {"xhr", "fetch"}:
            return
        self.network.append(
            {
                "method": request.method,
                "url": self._clean_url(request.url),
                "resource_type": request.resource_type,
                "request_fields": self._safe_payload_keys(request.post_data),
                "headers": self._safe_headers(request.headers),
            }
        )

    async def _on_response(self, response: Any) -> None:
        try:
            request = response.request
            if request.resource_type not in {"xhr", "fetch"}:
                return
            self.network.append(
                {
                    "method": request.method,
                    "url": self._clean_url(response.url),
                    "status": response.status,
                    "resource_type": request.resource_type,
                    "response_fields": await self._response_fields(response),
                    "headers": self._safe_headers(response.headers),
                }
            )
        except Exception:
            return

    async def _response_fields(self, response: Any) -> list[str]:
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type:
            return []
        try:
            data = await response.json()
            return self._extract_keys(data)[:200]
        except Exception:
            return []

    def _safe_payload_keys(self, data: str | None) -> list[str]:
        if not data:
            return []
        try:
            payload = json.loads(data)
            return self._extract_keys(payload)[:200]
        except Exception:
            return re.findall(r"([A-Za-z0-9_.$-]+)=", data)[:100]

    def _extract_keys(self, value: Any, prefix: str = "") -> list[str]:
        keys: list[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                name = f"{prefix}.{key}" if prefix else str(key)
                if not SENSITIVE_HEADER.search(name):
                    keys.append(name)
                keys.extend(self._extract_keys(item, name))
        elif isinstance(value, list) and value:
            keys.extend(self._extract_keys(value[0], prefix))
        return keys

    def _safe_headers(self, headers: dict[str, str]) -> dict[str, str]:
        return {key: value for key, value in headers.items() if not SENSITIVE_HEADER.search(key)}

    def _redact_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for key, value in data.items():
            if value is None:
                result[key] = value
            elif SENSITIVE_HEADER.search(key):
                result[key] = "<redacted>"
            else:
                result[key] = str(value)[:500]
        return result

    def _summarize_network(self) -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for item in self.network:
            key = (item.get("method", ""), item.get("url", ""))
            current = grouped.setdefault(
                key,
                {
                    "method": item.get("method"),
                    "url": item.get("url"),
                    "statuses": set(),
                    "request_fields": set(),
                    "response_fields": set(),
                },
            )
            if item.get("status"):
                current["statuses"].add(item["status"])
            current["request_fields"].update(item.get("request_fields", []))
            current["response_fields"].update(item.get("response_fields", []))
        result = []
        for item in grouped.values():
            result.append(
                {
                    "method": item["method"],
                    "url": item["url"],
                    "statuses": sorted(item["statuses"]),
                    "request_fields": sorted(item["request_fields"]),
                    "response_fields": sorted(item["response_fields"]),
                    "dangerous_guess": bool(DANGEROUS_TEXT.search(item["url"] or "")),
                }
            )
        return result

    def _write_reports(self) -> None:
        json_path = self.config.out / "report.json"
        md_path = self.config.out / "report.md"
        acceptance_path = self.config.out / "acceptance.json"
        json_path.write_text(json.dumps(self.report, ensure_ascii=False, indent=2), encoding="utf-8")
        acceptance_path.write_text(
            json.dumps(self.report["acceptance"], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        md_path.write_text(self._render_markdown(), encoding="utf-8")
        print(f"报告已生成: {md_path}")
        print(f"结构化数据: {json_path}")
        print(f"验收结果: {acceptance_path}")
        print(f"登录态已保存: {self.config.storage_state}")

    def _build_acceptance(self) -> dict[str, Any]:
        pages = self.report["pages"]
        forms = [form for page in pages for form in page.get("forms", [])]
        fields = [field for form in forms for field in form.get("fields", [])]
        dynamic_branches = [branch for page in pages for branch in page.get("dynamic_form_branches", [])]
        dangerous_buttons = [
            button
            for page in pages
            for button in page.get("buttons", [])
            if button.get("dangerous")
        ]
        constrained_fields = [
            field
            for field in fields
            if any(value for value in field.get("constraint", {}).values())
            or field.get("options")
            or field.get("attributes", {}).get("placeholder")
        ]
        document_count = len(self.report["documents"])
        endpoint_count = len(self.report["api_endpoints"])
        checks = [
            self._acceptance_check("pages_scanned", len(pages) > 0, 15, f"已扫描页面 {len(pages)} 个"),
            self._acceptance_check("forms_collected", bool(forms), 15, f"已采集表单 {len(forms)} 个"),
            self._acceptance_check("fields_collected", bool(fields), 15, f"已采集字段 {len(fields)} 个"),
            self._acceptance_check(
                "constraints_collected",
                bool(constrained_fields) or not fields,
                15,
                f"含约束/选项/占位符字段 {len(constrained_fields)} 个",
            ),
            self._acceptance_check(
                "dynamic_branches_checked",
                bool(dynamic_branches) or not self._has_branchable_fields(fields),
                15,
                f"动态分支记录 {len(dynamic_branches)} 条",
            ),
            self._acceptance_check(
                "docs_or_api_found",
                bool(document_count or endpoint_count),
                10,
                f"文档 {document_count} 个，接口线索 {endpoint_count} 个",
            ),
            self._acceptance_check(
                "dangerous_actions_marked",
                all(button.get("dangerous") for button in dangerous_buttons),
                10,
                f"高风险动作入口 {len(dangerous_buttons)} 个",
            ),
            self._acceptance_check(
                "coverage_notes_recorded",
                self._coverage_notes_are_actionable(),
                5,
                f"覆盖说明 {len(self.report['coverage_notes'])} 条",
            ),
        ]
        score = sum(check["weight"] for check in checks if check["passed"])
        gaps = [check for check in checks if not check["passed"]]
        return {
            "status": "passed" if score >= self.config.min_acceptance_score else "needs_review",
            "score": score,
            "max_score": sum(check["weight"] for check in checks),
            "min_score": self.config.min_acceptance_score,
            "checks": checks,
            "gaps": gaps,
            "recommendations": self._acceptance_recommendations(gaps),
            "metrics": {
                "pages": len(pages),
                "forms": len(forms),
                "fields": len(fields),
                "constrained_fields": len(constrained_fields),
                "dynamic_branches": len(dynamic_branches),
                "documents": document_count,
                "api_endpoints": endpoint_count,
                "dangerous_actions": len(dangerous_buttons),
            },
        }

    def _acceptance_check(self, name: str, passed: bool, weight: int, detail: str) -> dict[str, Any]:
        return {"name": name, "passed": passed, "weight": weight, "detail": detail}

    def _has_branchable_fields(self, fields: list[dict[str, Any]]) -> bool:
        for field in fields:
            attrs = field.get("attributes", {})
            field_type = (attrs.get("type") or "").lower()
            if field.get("options") or field_type in {"radio", "checkbox"}:
                return True
        return False

    def _coverage_notes_are_actionable(self) -> bool:
        notes = self.report["coverage_notes"]
        if not notes:
            return True
        return all("type" in note for note in notes)

    def _acceptance_recommendations(self, gaps: list[dict[str, Any]]) -> list[str]:
        mapping = {
            "pages_scanned": "检查目标网址是否可访问，必要时使用 --wait-login 或 --cookies。",
            "forms_collected": "提高 --max-pages 和 --max-depth，或从具体功能页 URL 开始扫描。",
            "fields_collected": "确认表单是否在弹窗、抽屉或登录后页面内，必要时先登录再扫。",
            "constraints_collected": "补扫字段聚焦页面，或人工打开表单触发校验提示后再运行。",
            "dynamic_branches_checked": "提高 --branch-limit，并从包含级联/多级表单的页面开始扫描。",
            "docs_or_api_found": "提供帮助中心/API 文档入口 URL，或提高 --max-depth 读取文档页。",
            "dangerous_actions_marked": "复查按钮关键词和业务文案，必要时扩展危险动作词表。",
            "coverage_notes_recorded": "查看 report.json 的 coverage_notes，确认是否存在未穷尽组合。",
        }
        return [mapping.get(gap["name"], gap["detail"]) for gap in gaps]

    def _render_markdown(self) -> str:
        lines = [
            f"# 网站功能侦察报告",
            "",
            f"- 目标: {self.report['target']}",
            f"- 生成时间: {self.report['generated_at']}",
            f"- 模式: 安全侦察，不提交表单，不执行危险动作",
            "",
            "## 验收结果",
            f"- 状态: {self.report['acceptance'].get('status')}",
            f"- 分数: {self.report['acceptance'].get('score')}/{self.report['acceptance'].get('max_score')}，最低要求 {self.report['acceptance'].get('min_score')}",
        ]
        if self.report["acceptance"].get("gaps"):
            lines.append("- 未满足项:")
            for gap in self.report["acceptance"]["gaps"]:
                lines.append(f"  - {gap['name']}: {gap['detail']}")
        if self.report["acceptance"].get("recommendations"):
            lines.append("- 补扫建议:")
            for recommendation in self.report["acceptance"]["recommendations"]:
                lines.append(f"  - {recommendation}")
        lines.extend(
            [
                "",
            "## 页面与功能",
            ]
        )
        for page in self.report["pages"]:
            lines.extend(
                [
                    "",
                    f"### {page.get('title') or page.get('url')}",
                    f"- URL: {page.get('url')}",
                    f"- 深度: {page.get('depth')}",
                    f"- 按钮数: {len(page.get('buttons', []))}",
                    f"- 表单数: {len(page.get('forms', []))}",
                    f"- 动态分支记录: {len(page.get('dynamic_form_branches', []))}",
                ]
            )
            dangerous = [button for button in page.get("buttons", []) if button.get("dangerous")]
            if dangerous:
                lines.append("- 高风险动作入口:")
                for button in dangerous[:30]:
                    lines.append(f"  - {button.get('text') or button.get('aria_label') or '<无文本>'}")
            for form in page.get("forms", [])[:20]:
                lines.extend(["", f"#### 表单 {form.get('index')}: {form.get('title') or '<未命名>'}"])
                if form.get("action") or form.get("method"):
                    lines.append(f"- action/method: {form.get('action') or ''} {form.get('method') or ''}".strip())
                for field in form.get("fields", [])[:120]:
                    attrs = field.get("attributes", {})
                    constraint = field.get("constraint", {})
                    option_text = ""
                    if field.get("options"):
                        option_text = "；选项: " + ", ".join(
                            [str(opt.get("label") or opt.get("value")) for opt in field["options"][:20]]
                        )
                    lines.append(
                        f"- 字段: {field.get('label') or attrs.get('name') or attrs.get('id') or field.get('text') or '<未命名>'}"
                        f"；类型: {attrs.get('type') or field.get('tag')}"
                        f"；必填: {constraint.get('required')}"
                        f"；约束: min={constraint.get('min')}, max={constraint.get('max')}, minlength={constraint.get('minlength')}, maxlength={constraint.get('maxlength')}, pattern={constraint.get('pattern')}, accept={constraint.get('accept')}"
                        f"{option_text}"
                    )
                if form.get("validation_messages"):
                    lines.append("- 校验提示: " + " | ".join(form["validation_messages"][:20]))
            if page.get("dynamic_form_branches"):
                lines.extend(["", "#### 动态表单分支"])
                for branch in page["dynamic_form_branches"][:40]:
                    control = branch.get("control", {})
                    option = branch.get("selected_option", {})
                    lines.append(
                        f"- 控件 {control.get('label') or control.get('attributes', {}).get('name') or branch.get('control_index')}: "
                        f"选择 {option.get('label') or option.get('value')} 后 changed={branch.get('changed')}"
                    )
        lines.extend(["", "## 文档与 API 说明"])
        for doc in self.report["documents"][:80]:
            lines.extend(
                [
                    "",
                    f"### {doc.get('title') or doc.get('label') or doc.get('url')}",
                    f"- URL: {doc.get('url')}",
                    f"- 类型: {doc.get('kind', 'document')}",
                    f"- 摘要: {(doc.get('summary_text') or doc.get('error') or '')[:1000]}",
                ]
            )
            if doc.get("openapi"):
                lines.append(f"- OpenAPI/Swagger 端点数: {len(doc['openapi'].get('endpoints', []))}")
        lines.extend(["", "## 网络接口线索"])
        for endpoint in self.report["api_endpoints"][:200]:
            lines.append(
                f"- {endpoint.get('method')} {endpoint.get('url')} status={endpoint.get('statuses')} "
                f"request={endpoint.get('request_fields')} response={endpoint.get('response_fields')}"
            )
        if self.report["coverage_notes"]:
            lines.extend(["", "## 覆盖说明"])
            for note in self.report["coverage_notes"]:
                lines.append(f"- {json.dumps(note, ensure_ascii=False)}")
        return "\n".join(lines) + "\n"

    def _document_kind(self, url: str, text: str) -> str:
        target = f"{url}\n{text[:2000]}"
        if re.search(r"(swagger|openapi)", target, re.I):
            return "openapi"
        if re.search(r"(api|接口|endpoint)", target, re.I):
            return "api-doc"
        if re.search(r"(faq|常见问题)", target, re.I):
            return "faq"
        return "manual"

    def _same_host(self, url: str) -> bool:
        parsed = urlparse(url)
        return not parsed.netloc or parsed.netloc == self.base_host

    def _clean_url(self, url: str) -> str:
        absolute = urljoin(self.config.url, url)
        clean, _fragment = urldefrag(absolute)
        return clean

    def _dedupe_dicts(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        result = []
        for item in items:
            key = json.dumps(item, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result


def default_out(url: str) -> Path:
    host = urlparse(url).netloc.replace(":", "_") or "site"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path("outputs") / f"{host}-{stamp}"


def parse_args() -> ScanConfig:
    parser = argparse.ArgumentParser(description="使用 Playwright 安全侦察网站功能、表单、文档和接口线索。")
    parser.add_argument("url", help="目标网址")
    parser.add_argument("--out", type=Path, help="输出目录")
    parser.add_argument("--storage-state", type=Path, default=Path("storageState.json"), help="Playwright 登录态文件")
    parser.add_argument("--cookies", type=Path, help="cookie JSON 文件")
    parser.add_argument("--wait-login", action="store_true", help="等待用户手动登录后继续")
    parser.add_argument("--headless", action="store_true", help="使用无头浏览器")
    parser.add_argument("--max-pages", type=int, default=20, help="最大扫描页面数")
    parser.add_argument("--max-depth", type=int, default=2, help="同域链接最大深度")
    parser.add_argument("--branch-limit", type=int, default=8, help="每个动态控件最多尝试选项数")
    parser.add_argument("--timeout", type=int, default=30000, help="页面加载超时毫秒")
    parser.add_argument("--min-acceptance-score", type=int, default=80, help="验收最低分")
    parser.add_argument("--fail-under-acceptance", action="store_true", help="验收低于最低分时以退出码 2 失败")
    args = parser.parse_args()
    return ScanConfig(
        url=args.url,
        out=args.out or default_out(args.url),
        storage_state=args.storage_state,
        cookies=args.cookies,
        wait_login=args.wait_login,
        headless=args.headless,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        branch_limit=args.branch_limit,
        timeout=args.timeout,
        min_acceptance_score=args.min_acceptance_score,
        fail_under_acceptance=args.fail_under_acceptance,
    )


def main() -> None:
    config = parse_args()
    mapper = SiteMapper(config)
    asyncio.run(mapper.run())


if __name__ == "__main__":
    main()
