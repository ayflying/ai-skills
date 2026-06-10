#!/usr/bin/env python3
"""通过 Teambition 官方 OpenAPI 管理 bug/缺陷任务。"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import requests
except ImportError:  # pragma: no cover - exercised by users without deps
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # optional, script falls back to regex extraction
    BeautifulSoup = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GATEWAY = "https://open.teambition.com/api"
WRITE_COMMANDS = {
    "comment",
    "reply",
    "quick-reply",
    "ask",
    "start",
    "update-status",
    "update-title",
    "update-note",
    "update-executor",
    "update-priority",
    "update-due-date",
    "create-bug-group",
}


class ConfigError(RuntimeError):
    pass


class ApiError(RuntimeError):
    pass


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env(name: str, required: bool = False, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise ConfigError(f"缺少环境变量: {name}")
    return value


def parse_teambition_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    result: dict[str, str] = {}

    project_match = re.search(r"(?:^|/)project/([0-9a-fA-F]{24})(?:/|$)", path)
    if project_match:
        result["projectId"] = project_match.group(1)

    task_match = re.search(r"(?:^|/)task/([0-9a-fA-F]{24})(?:/|$)", path)
    if task_match:
        result["taskId"] = task_match.group(1)

    view_match = re.search(r"(?:^|/)tasks/view/([0-9a-fA-F]{24})(?:/|$)", path)
    if view_match:
        result["viewId"] = view_match.group(1)

    return result


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def confirm_or_exit(message: str, yes: bool = False) -> None:
    if yes:
        return
    try:
        answer = input(f"{message} 输入 yes 确认: ").strip().lower()
    except EOFError:
        raise SystemExit("未收到确认输入，已取消操作。") from None
    if answer != "yes":
        raise SystemExit("已取消操作。")


class TeambitionClient:
    def __init__(self) -> None:
        if requests is None:
            raise ConfigError("缺少 requests 依赖，请先执行: pip install -r requirements.txt")

        self.gateway = (env("TEAMBITION_GATEWAY", default=DEFAULT_GATEWAY) or DEFAULT_GATEWAY).rstrip("/")
        self.tenant_id = env("TEAMBITION_TENANT_ID", required=True) or ""
        self.token = env("TEAMBITION_USER_TOKEN", required=True) or ""

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-Id": self.tenant_id,
            "X-Tenant-Type": "organization",
            "Content-Type": "application/json",
        }

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = self.gateway + (path if path.startswith("/") else f"/{path}")
        response = requests.request(
            method,
            url,
            headers=self.headers(),
            params={k: v for k, v in (params or {}).items() if v is not None},
            json=json_body,
            timeout=30,
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise ApiError(f"响应不是 JSON: HTTP {response.status_code} {response.text[:300]}") from exc

        if response.status_code >= 400 or data.get("success") is False or data.get("code") not in (None, 0, 200):
            message = data.get("errorMessage") or data.get("message") or response.text[:300]
            request_id = data.get("requestId") or data.get("traceId")
            suffix = f" requestId={request_id}" if request_id else ""
            raise ApiError(f"API 请求失败: HTTP {response.status_code} {message}{suffix}")
        return data.get("result", data)


def extract_links_from_html(text: str) -> dict[str, list[str]]:
    if not text:
        return {"images": [], "attachments": [], "links": []}

    images: list[str] = []
    links: list[str] = []
    attachments: list[str] = []

    if BeautifulSoup is not None:
        soup = BeautifulSoup(text, "html.parser")
        images = [img.get("src") for img in soup.find_all("img") if img.get("src")]
        links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
    else:
        images = re.findall(r"<img[^>]+src=[\"']([^\"']+)[\"']", text, flags=re.I)
        links = re.findall(r"<a[^>]+href=[\"']([^\"']+)[\"']", text, flags=re.I)

    for link in links:
        lowered = link.lower()
        if any(part in lowered for part in ("download", "attachment", "file", "oss", "alicdn")):
            attachments.append(link)

    return {
        "images": sorted(set(images)),
        "attachments": sorted(set(attachments)),
        "links": sorted(set(links)),
    }


def summarize_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task.get("id") or task.get("taskId"),
        "title": task.get("content"),
        "note": task.get("note"),
        "projectId": task.get("projectId"),
        "statusId": task.get("tfsId") or task.get("taskflowstatusId"),
        "executorId": task.get("executorId"),
        "priority": task.get("priority"),
        "dueDate": task.get("dueDate"),
        "url": f"https://www.teambition.com/task/{task.get('id') or task.get('taskId')}",
    }


def first_task(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        if not result:
            raise ApiError("未找到任务。")
        return result[0]
    if isinstance(result, dict) and isinstance(result.get("result"), list):
        if not result["result"]:
            raise ApiError("未找到任务。")
        return result["result"][0]
    if isinstance(result, dict):
        return result
    raise ApiError("无法识别任务响应格式。")


def cmd_parse_url(args: argparse.Namespace) -> None:
    parsed = parse_teambition_url(args.url)
    if not parsed:
        raise SystemExit("未从链接中解析到 projectId、taskId 或 viewId。")
    print_json(parsed)


def cmd_search(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    result = client.request(
        "GET",
        f"/v3/project/{args.project_id}/task/query",
        params={
            "q": args.tql,
            "includeArchived": str(args.include_archived).lower(),
            "pageToken": args.page_token,
            "pageSize": args.page_size,
        },
    )
    print_json(result)


def get_task(client: TeambitionClient, task_id: str) -> dict[str, Any]:
    result = client.request("GET", "/v3/task/query", params={"taskId": task_id})
    return first_task(result)


def cmd_get(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    task = get_task(client, args.task_id)
    output: dict[str, Any] = {"task": summarize_task(task), "rawTask": task if args.raw else None}
    if args.with_activities:
        output["activities"] = list_activities(client, args.task_id, page_size=args.page_size)
    if args.with_rich_text:
        output["richTextLinks"] = extract_links_from_html(task.get("note") or "")
    if output.get("rawTask") is None:
        output.pop("rawTask", None)
    print_json(output)


def list_activities(client: TeambitionClient, task_id: str, page_size: int = 50, actions: str | None = None) -> Any:
    return client.request(
        "GET",
        f"/v3/task/{task_id}/activity/list",
        params={"pageSize": page_size, "actions": actions},
    )


def cmd_activities(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    print_json(list_activities(client, args.task_id, page_size=args.page_size, actions=args.actions))


def cmd_comments(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    activities = list_activities(client, args.task_id, page_size=args.page_size)
    items = activities if isinstance(activities, list) else activities.get("result", []) if isinstance(activities, dict) else []
    comments = []
    for item in items:
        action = str(item.get("action") or "")
        if "comment" in action or action in {"task.comment", "comment"}:
            comments.append(item)
    print_json(comments)


def cmd_traces(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    result = client.request("GET", f"/v3/task/{args.task_id}/traces")
    print_json(result)


def cmd_context(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    task = get_task(client, args.task_id)
    activities = list_activities(client, args.task_id, page_size=args.page_size)
    try:
        traces = client.request("GET", f"/v3/task/{args.task_id}/traces")
    except ApiError as exc:
        traces = {"error": str(exc)}

    rich_text_sources = [task.get("note") or ""]
    trace_items = traces if isinstance(traces, list) else traces.get("result", []) if isinstance(traces, dict) else []
    for item in trace_items:
        if isinstance(item, dict):
            rich_text_sources.append(str(item.get("content") or item.get("note") or ""))

    rich_text = {"images": [], "attachments": [], "links": []}
    for source in rich_text_sources:
        extracted = extract_links_from_html(source)
        for key in rich_text:
            rich_text[key].extend(extracted[key])
    rich_text = {key: sorted(set(value)) for key, value in rich_text.items()}

    print_json(
        {
            "task": summarize_task(task),
            "activities": activities,
            "traces": traces,
            "richTextLinks": rich_text,
            "missingInfoHints": guess_missing_info(task, activities),
        }
    )


def guess_missing_info(task: dict[str, Any], activities: Any) -> list[str]:
    text = " ".join(
        [
            str(task.get("content") or ""),
            str(task.get("note") or ""),
            json.dumps(activities, ensure_ascii=False)[:5000],
        ]
    )
    checks = [
        ("复现步骤", ("复现", "步骤", "操作路径")),
        ("期望结果", ("期望", "应该", "预期")),
        ("实际结果", ("实际", "报错", "现象", "错误")),
        ("环境信息", ("环境", "版本", "浏览器", "系统", "设备")),
    ]
    missing = []
    for label, keywords in checks:
        if not any(keyword in text for keyword in keywords):
            missing.append(label)
    return missing


def cmd_render_rich_text(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    if args.rtf_fields_file:
        rtf_fields = Path(args.rtf_fields_file).read_text(encoding="utf-8")
    else:
        rtf_fields = args.rtf_fields
    result = client.request("GET", "/v3/task/rtf/render", params={"rtfFields": rtf_fields})
    rendered = json.dumps(result, ensure_ascii=False)
    print_json({"result": result, "links": extract_links_from_html(html.unescape(rendered))})


def cmd_comment(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    confirm_or_exit(f"将向任务 {args.task_id} 留言。", args.yes)
    body: dict[str, Any] = {"content": args.content, "renderMode": args.render_mode}
    if args.mention_user_id:
        body["mentionUserIds"] = args.mention_user_id
    result = client.request("POST", f"/v3/task/{args.task_id}/comment", json_body=body)
    print_json(result)


def cmd_reply(args: argparse.Namespace) -> None:
    content = args.content
    if args.reply_to:
        content = f"回复动态 {args.reply_to}：\n\n{content}"
    args.content = content
    args.render_mode = args.render_mode
    cmd_comment(args)


REPLY_TEMPLATES = {
    "need-info": "信息还不够定位，请补充：1. 复现步骤；2. 期望结果；3. 实际结果或报错；4. 环境信息；5. 相关截图或录屏。",
    "received": "已收到，我先看一下问题上下文和复现路径。",
    "investigating": "我已经开始排查，会先确认复现路径和相关日志，有进展后同步。",
    "fixed": "问题已处理，请帮忙重新验证。如仍有异常，请补充最新现象和截图。",
    "cannot-reproduce": "当前信息下暂未复现，请补充更完整的操作路径、账号/环境、期望结果和实际结果。",
    "done": "已处理完成，麻烦确认验收。",
}


def cmd_quick_reply(args: argparse.Namespace) -> None:
    content = REPLY_TEMPLATES.get(args.template)
    if not content:
        raise ConfigError(f"未知模板: {args.template}。可用模板: {', '.join(REPLY_TEMPLATES)}")
    if args.extra:
        content = f"{content}\n\n{args.extra}"
    args.content = content
    args.render_mode = "markdown"
    args.mention_user_id = args.mention_user_id
    cmd_comment(args)


def cmd_ask(args: argparse.Namespace) -> None:
    args.content = args.question
    args.render_mode = "markdown"
    args.mention_user_id = args.mention_user_id
    cmd_comment(args)


def list_statuses(client: TeambitionClient, task_id: str) -> Any:
    return client.request("GET", f"/v3/task/{task_id}/tfs")


def pick_status(statuses: Any, status_name: str | None, status_id: str | None) -> dict[str, Any]:
    items = statuses if isinstance(statuses, list) else statuses.get("result", []) if isinstance(statuses, dict) else []
    if status_id:
        for item in items:
            if item.get("id") == status_id:
                return item
        return {"id": status_id, "name": status_name or status_id}
    if not status_name:
        raise ConfigError("请提供 --status-name 或 --status-id")
    for item in items:
        if str(item.get("name", "")).strip() == status_name:
            return item
    candidates = [item.get("name") for item in items if item.get("name")]
    raise ApiError(f"没有找到状态名称: {status_name}。可用状态: {', '.join(candidates)}")


def cmd_list_status(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    print_json(list_statuses(client, args.task_id))


def cmd_start(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    task = get_task(client, args.task_id)
    statuses = list_statuses(client, args.task_id)
    status = pick_status(statuses, args.status_name, args.status_id)
    confirm_or_exit(f"将任务《{task.get('content')}》状态改为 {status.get('name') or status.get('id')}。", args.yes)
    body = {"taskflowstatusId": status.get("id"), "tfsUpdateNote": args.note}
    result = client.request(
        "PUT",
        f"/v3/task/{args.task_id}/taskflowstatus",
        json_body={k: v for k, v in body.items() if v is not None},
    )
    print_json(result)


def cmd_update_status(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    task = get_task(client, args.task_id)
    statuses = list_statuses(client, args.task_id)
    status = pick_status(statuses, args.status_name, args.status_id)
    confirm_or_exit(f"将任务《{task.get('content')}》状态改为 {status.get('name') or status.get('id')}。", args.yes)
    body = {"taskflowstatusId": status.get("id"), "tfsName": args.status_name, "tfsUpdateNote": args.note}
    result = client.request(
        "PUT",
        f"/v3/task/{args.task_id}/taskflowstatus",
        json_body={k: v for k, v in body.items() if v is not None},
    )
    print_json(result)


def cmd_update_title(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    confirm_or_exit(f"将更新任务 {args.task_id} 标题。", args.yes)
    print_json(client.request("PUT", f"/v3/task/{args.task_id}/content", json_body={"content": args.title}))


def cmd_update_note(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    confirm_or_exit(f"将更新任务 {args.task_id} 备注。", args.yes)
    print_json(
        client.request(
            "PUT",
            f"/v3/task/{args.task_id}/note",
            json_body={"note": args.note, "renderMode": args.render_mode},
        )
    )


def cmd_update_executor(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    confirm_or_exit(f"将更新任务 {args.task_id} 执行人。", args.yes)
    print_json(
        client.request(
            "PUT",
            f"/v3/task/{args.task_id}/executor",
            json_body={"executorId": args.executor_id},
        )
    )


def cmd_list_priorities(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    print_json(client.request("GET", "/v3/project/priority/list", params={"organizationId": args.organization_id}))


def cmd_update_priority(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    confirm_or_exit(f"将更新任务 {args.task_id} 优先级。", args.yes)
    value: dict[str, Any] = {}
    try:
        value["priority"] = int(args.priority)
    except ValueError:
        value["priorityName"] = args.priority
    print_json(client.request("PUT", f"/v3/task/{args.task_id}/priority", json_body=value))


def cmd_update_due_date(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    confirm_or_exit(f"将更新任务 {args.task_id} 截止时间。", args.yes)
    print_json(
        client.request(
            "PUT",
            f"/v3/task/{args.task_id}/dueDate",
            json_body={"dueDate": args.due_date},
        )
    )


def cmd_list_bug_groups(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    print_json(
        client.request(
            "GET",
            f"/v3/project/{args.project_id}/bug/commongroup",
            params={"pageSize": args.page_size, "pageToken": args.page_token},
        )
    )


def cmd_create_bug_group(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    confirm_or_exit(f"将在项目 {args.project_id} 创建缺陷分类 {args.name}。", args.yes)
    body = {"name": args.name, "parentId": args.parent_id, "description": args.description}
    print_json(
        client.request(
            "POST",
            f"/v3/project/{args.project_id}/bug/commongroup/create",
            json_body={k: v for k, v in body.items() if v is not None},
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Teambition Bug OpenAPI helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("parse-url", help="解析 Teambition 链接")
    p.add_argument("--url", required=True)
    p.set_defaults(func=cmd_parse_url)

    p = sub.add_parser("search", help="查询项目任务")
    p.add_argument("--project-id", required=True)
    p.add_argument("--tql", default="")
    p.add_argument("--page-size", type=int, default=10)
    p.add_argument("--page-token")
    p.add_argument("--include-archived", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("get", help="查询任务详情")
    p.add_argument("--task-id", required=True)
    p.add_argument("--with-activities", action="store_true")
    p.add_argument("--with-rich-text", action="store_true")
    p.add_argument("--page-size", type=int, default=50)
    p.add_argument("--raw", action="store_true")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("context", help="聚合 bug 上下文")
    p.add_argument("--task-id", required=True)
    p.add_argument("--page-size", type=int, default=50)
    p.set_defaults(func=cmd_context)

    p = sub.add_parser("activities", help="列出任务动态")
    p.add_argument("--task-id", required=True)
    p.add_argument("--page-size", type=int, default=50)
    p.add_argument("--actions")
    p.set_defaults(func=cmd_activities)

    p = sub.add_parser("comments", help="从任务动态中过滤评论")
    p.add_argument("--task-id", required=True)
    p.add_argument("--page-size", type=int, default=50)
    p.set_defaults(func=cmd_comments)

    p = sub.add_parser("traces", help="读取任务进展")
    p.add_argument("--task-id", required=True)
    p.set_defaults(func=cmd_traces)

    p = sub.add_parser("render-rich-text", help="渲染富文本并提取链接")
    p.add_argument("--rtf-fields")
    p.add_argument("--rtf-fields-file")
    p.set_defaults(func=cmd_render_rich_text)

    p = sub.add_parser("comment", help="评论任务")
    p.add_argument("--task-id", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--render-mode", default="markdown")
    p.add_argument("--mention-user-id", action="append")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_comment)

    p = sub.add_parser("reply", help="回复任务，可引用动态或评论 ID")
    p.add_argument("--task-id", required=True)
    p.add_argument("--content", required=True)
    p.add_argument("--reply-to")
    p.add_argument("--render-mode", default="markdown")
    p.add_argument("--mention-user-id", action="append")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_reply)

    p = sub.add_parser("quick-reply", help="使用常用模板回复任务")
    p.add_argument("--task-id", required=True)
    p.add_argument("--template", required=True, choices=sorted(REPLY_TEMPLATES))
    p.add_argument("--extra")
    p.add_argument("--mention-user-id", action="append")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_quick_reply)

    p = sub.add_parser("ask", help="留言追问")
    p.add_argument("--task-id", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--mention-user-id", action="append")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("list-status", help="列出任务可用状态")
    p.add_argument("--task-id", required=True)
    p.set_defaults(func=cmd_list_status)

    p = sub.add_parser("start", help="将任务推进到指定状态，默认修改中")
    p.add_argument("--task-id", required=True)
    p.add_argument("--status-name", default="修改中")
    p.add_argument("--status-id")
    p.add_argument("--note")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("update-status", help="按状态名称或 ID 更新任务状态")
    p.add_argument("--task-id", required=True)
    p.add_argument("--status-name")
    p.add_argument("--status-id")
    p.add_argument("--note")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_update_status)

    p = sub.add_parser("update-title", help="更新任务标题")
    p.add_argument("--task-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_update_title)

    p = sub.add_parser("update-note", help="更新任务备注")
    p.add_argument("--task-id", required=True)
    p.add_argument("--note", required=True)
    p.add_argument("--render-mode", default="markdown")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_update_note)

    p = sub.add_parser("update-executor", help="更新任务执行人")
    p.add_argument("--task-id", required=True)
    p.add_argument("--executor-id", required=True)
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_update_executor)

    p = sub.add_parser("list-priorities", help="查询企业优先级")
    p.add_argument("--organization-id")
    p.set_defaults(func=cmd_list_priorities)

    p = sub.add_parser("update-priority", help="更新任务优先级")
    p.add_argument("--task-id", required=True)
    p.add_argument("--priority", required=True)
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_update_priority)

    p = sub.add_parser("update-due-date", help="更新任务截止时间")
    p.add_argument("--task-id", required=True)
    p.add_argument("--due-date", required=True)
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_update_due_date)

    p = sub.add_parser("list-bug-groups", help="查询缺陷分类")
    p.add_argument("--project-id", required=True)
    p.add_argument("--page-size", type=int, default=50)
    p.add_argument("--page-token")
    p.set_defaults(func=cmd_list_bug_groups)

    p = sub.add_parser("create-bug-group", help="创建缺陷分类")
    p.add_argument("--project-id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--parent-id")
    p.add_argument("--description")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_create_bug_group)

    return parser


def main() -> int:
    load_dotenv(ROOT / ".env")
    args = build_parser().parse_args()
    try:
        args.func(args)
        return 0
    except (ConfigError, ApiError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
