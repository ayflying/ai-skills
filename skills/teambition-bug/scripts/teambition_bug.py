#!/usr/bin/env python3
"""通过 Teambition 官方 OpenAPI 管理 bug/缺陷任务。"""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlsplit

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
    "finish",
    "update-status",
    "update-title",
    "update-note",
    "update-executor",
    "update-priority",
    "update-due-date",
    "create-bug-group",
}

URL_RE = re.compile(r"https?://[^\s\"'<>\\)\\]]+")
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg")
IMAGE_URL_HINTS = ("image", "img", "screenshot", "thumbnail", "preview", "pic", "photo")
FILE_URL_KEYS = {
    "url",
    "src",
    "href",
    "downloadUrl",
    "downloadURL",
    "fileUrl",
    "fileURL",
    "thumbnail",
    "thumbnailUrl",
    "previewUrl",
    "previewURL",
    "imageUrl",
    "imageURL",
}


class ConfigError(RuntimeError):
    pass


class ApiError(RuntimeError):
    pass


def env(name: str, required: bool = False, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if required and not value:
        raise ConfigError(f"缺少环境变量: {name}")
    return value


def set_runtime_env(args: argparse.Namespace) -> None:
    mapping = {
        "tenant_id": "TEAMBITION_TENANT_ID",
        "user_token": "TEAMBITION_USER_TOKEN",
    }
    for arg_name, env_name in mapping.items():
        value = getattr(args, arg_name, None)
        if value:
            os.environ[env_name] = value


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
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def first_executor_id(task: dict[str, Any]) -> str | None:
    executor_id = task.get("executorId") or task.get("executor_id")
    if executor_id:
        return str(executor_id)

    executor_ids = task.get("executorIds") or task.get("executor_ids")
    if isinstance(executor_ids, list) and executor_ids:
        return str(executor_ids[0])

    executors = task.get("executors")
    if isinstance(executors, list) and executors:
        first = executors[0]
        if isinstance(first, dict):
            value = first.get("id") or first.get("userId") or first.get("_id")
            return str(value) if value else None
        return str(first)

    executor = task.get("executor")
    if isinstance(executor, dict):
        value = executor.get("id") or executor.get("userId") or executor.get("_id")
        return str(value) if value else None

    return None


def user_id_from_profile(profile: Any) -> str | None:
    if not isinstance(profile, dict):
        return None
    value = profile.get("userId") or profile.get("_userId") or profile.get("id") or profile.get("_id")
    return str(value) if value else None


def mask_value(value: str | None, *, head: int = 6, tail: int = 4) -> str | None:
    if not value:
        return value
    if len(value) <= head + tail:
        return value[:2] + "..." if len(value) > 2 else "***"
    return f"{value[:head]}...{value[-tail:]}"


def ensure_first_executor_is_self(client: "TeambitionClient", task: dict[str, Any], *, action: str = "读取") -> None:
    self_id = client.current_user_id()
    executor_id = first_executor_id(task)
    task_id = task.get("id") or task.get("taskId") or "<unknown>"
    if not executor_id:
        raise ApiError(f"无法确认任务 {task_id} 的第一执行者，为避免多人争抢，已停止{action}。")
    if executor_id != self_id:
        raise ApiError(
            f"任务 {task_id} 的第一执行者是 {executor_id}，不是当前账号 {self_id}。"
            f"为避免多人争抢，已跳过{action}。"
        )


def filter_first_executor_self(client: "TeambitionClient", result: Any) -> Any:
    self_id = client.current_user_id()

    def keep(task: Any) -> bool:
        return isinstance(task, dict) and first_executor_id(task) == self_id

    if isinstance(result, list):
        return [task for task in result if keep(task)]
    if isinstance(result, dict) and isinstance(result.get("result"), list):
        filtered = dict(result)
        filtered["result"] = [task for task in result["result"] if keep(task)]
        filtered["filteredByCurrentUserId"] = self_id
        filtered["filteredOutCount"] = len(result["result"]) - len(filtered["result"])
        return filtered
    if isinstance(result, dict):
        ensure_first_executor_is_self(client, result)
    return result


def confirm_or_exit(message: str, yes: bool = False) -> None:
    if yes:
        return
    try:
        answer = input(f"{message} 输入 yes 确认: ").strip().lower()
    except EOFError:
        raise SystemExit("未收到确认输入，已取消操作。") from None
    if answer != "yes":
        raise SystemExit("已取消操作。")


def require_project_id(value: str | None) -> str:
    if value:
        return value
    raise ConfigError(
        "缺少产品/项目 ID。请让用户复制 Teambition 产品/项目分享链接给 AI，"
        "由 AI 执行 parse-url 从链接里的 /project/<id> 提取 projectId，"
        "再用 --project-id <projectId> 重试。"
    )


class TeambitionClient:
    def __init__(self) -> None:
        if requests is None:
            raise ConfigError("缺少 requests 依赖，请先执行: pip install -r requirements.txt")

        self.gateway = (env("TEAMBITION_GATEWAY", default=DEFAULT_GATEWAY) or DEFAULT_GATEWAY).rstrip("/")
        self.tenant_id = env("TEAMBITION_TENANT_ID", required=True) or ""
        self.token = env("TEAMBITION_USER_TOKEN", required=True) or ""
        self._current_user: dict[str, Any] | None = None

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

    def current_user(self) -> dict[str, Any]:
        if self._current_user is None:
            result = self.request("GET", "/users/me")
            if not isinstance(result, dict):
                raise ApiError("无法识别当前用户信息响应。")
            if not user_id_from_profile(result):
                raise ApiError("当前用户信息中没有 userId，无法校验第一执行者。")
            self._current_user = result
        return self._current_user

    def current_user_id(self) -> str:
        user_id = user_id_from_profile(self.current_user())
        if not user_id:
            raise ApiError("当前用户信息中没有 userId，无法校验第一执行者。")
        return user_id


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


def classify_media_url(url: str, key_hint: str = "") -> str:
    lowered = url.lower()
    key_lowered = key_hint.lower()
    path = urlsplit(url).path.lower()
    if path.endswith(IMAGE_EXTENSIONS) or any(hint in lowered for hint in IMAGE_URL_HINTS):
        return "images"
    if any(hint in key_lowered for hint in IMAGE_URL_HINTS):
        return "images"
    if any(part in lowered for part in ("download", "attachment", "file", "oss", "alicdn")):
        return "attachments"
    return "links"


def add_media_url(resources: dict[str, list[str]], url: str, key_hint: str = "") -> None:
    cleaned = html.unescape(url.strip().rstrip(".,;"))
    if cleaned.startswith(("http://", "https://")):
        resources[classify_media_url(cleaned, key_hint)].append(cleaned)


def extract_media_resources(value: Any, key_hint: str = "") -> dict[str, list[str]]:
    resources = {"images": [], "attachments": [], "links": []}

    def visit(item: Any, current_key: str = "") -> None:
        if isinstance(item, str):
            stripped = item.strip()
            if stripped.startswith(("{", "[")):
                try:
                    visit(json.loads(stripped), current_key)
                    return
                except ValueError:
                    pass
            for url in URL_RE.findall(item):
                add_media_url(resources, url, current_key)
            if "<" in item and ">" in item:
                extracted = extract_links_from_html(item)
                for bucket, urls in extracted.items():
                    resources[bucket].extend(urls)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if key in FILE_URL_KEYS and isinstance(child, str):
                    add_media_url(resources, child, key)
                visit(child, key)
            return
        if isinstance(item, list):
            for child in item:
                visit(child, current_key)

    visit(value, key_hint)
    return {key: sorted(set(urls)) for key, urls in resources.items()}


def merge_media_resources(*groups: dict[str, list[str]]) -> dict[str, list[str]]:
    merged = {"images": [], "attachments": [], "links": []}
    for group in groups:
        for key in merged:
            merged[key].extend(group.get(key, []))
    return {key: sorted(set(value)) for key, value in merged.items()}


def count_image_placeholders(value: Any) -> int:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text.count("[图片]")


def safe_download_name(url: str, index: int, content_type: str | None = None) -> str:
    suffix = Path(urlsplit(url).path).suffix.lower()
    if not suffix or len(suffix) > 8:
        suffix = mimetypes.guess_extension((content_type or "").split(";")[0].strip()) or ".img"
    return f"image-{index:02d}{suffix}"


def parse_json_maybe(value: Any) -> Any:
    current = value
    for _ in range(3):
        if not isinstance(current, str):
            return current
        stripped = current.strip()
        if not stripped or stripped[0] not in "{[\"":
            return current
        try:
            current = json.loads(stripped)
        except ValueError:
            return current
    return current


def rtf_field_ids(task: dict[str, Any], traces: Any = None, *, include_custom_fields: bool = True) -> list[str]:
    task_id = str(task.get("id") or task.get("taskId") or "")
    if not task_id:
        return []

    fields: list[str] = []
    if task.get("note"):
        fields.append(f"{task_id}:note")

    trace_items = traces if isinstance(traces, list) else traces.get("result", []) if isinstance(traces, dict) else []
    for item in trace_items:
        if isinstance(item, dict):
            trace_id = item.get("id") or item.get("_id") or item.get("traceId")
            if trace_id:
                fields.append(f"{task_id}:trace:{trace_id}")

    if include_custom_fields:
        custom_fields = task.get("customfields") or task.get("customFields")
        if isinstance(custom_fields, dict):
            for cf_id, value in custom_fields.items():
                if re.fullmatch(r"[0-9a-fA-F]{24}", str(cf_id)) and value not in (None, "", [], {}):
                    fields.append(f"{task_id}:cf:{cf_id}")

    return fields[:50]


def parse_rtf_value_token(value: Any) -> dict[str, Any]:
    parsed = parse_json_maybe(value)
    if not isinstance(parsed, dict):
        return {}

    attachments = parsed.get("attachments")
    if not isinstance(attachments, dict):
        attachment_json = parse_json_maybe(parsed.get("attachmentJson"))
        if isinstance(attachment_json, dict):
            attachments = attachment_json
    if isinstance(attachments, dict):
        parsed["attachments"] = attachments
    return parsed


def extract_rtf_resources(rendered: Any) -> dict[str, Any]:
    items = rendered if isinstance(rendered, list) else rendered.get("result", []) if isinstance(rendered, dict) else []
    resources = {"images": [], "attachments": [], "links": []}
    fields: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        field = str(item.get("rtfField") or "")
        if field:
            fields.append(field)
        token = parse_rtf_value_token(item.get("rtfValueToken"))
        attachments = token.get("attachments") if isinstance(token, dict) else None
        if isinstance(attachments, dict):
            for name, url in attachments.items():
                if isinstance(url, str):
                    add_media_url(resources, url, str(name))
        extracted = extract_media_resources({"html": item.get("html"), "rtfValueToken": token})
        resources = merge_media_resources(resources, extracted)
    return {"rtfFields": sorted(set(fields)), "resources": merge_media_resources(resources)}


def render_rich_text_fields(
    client: TeambitionClient,
    fields: list[str],
    *,
    html_expire_seconds: int = 3600,
) -> list[dict[str, Any]]:
    if not fields:
        return []
    result = client.request(
        "GET",
        "/v3/task/rtf/render",
        params={"rtfFields": ",".join(fields[:50]), "htmlExpireSeconds": html_expire_seconds},
    )
    return result if isinstance(result, list) else result.get("result", []) if isinstance(result, dict) else []


def render_task_rich_text(client: TeambitionClient, task: dict[str, Any], traces: Any = None) -> dict[str, Any]:
    fields = rtf_field_ids(task, traces)
    if not fields:
        return {"rtfFields": [], "items": [], "resources": {"images": [], "attachments": [], "links": []}}
    try:
        items = render_rich_text_fields(client, fields)
    except ApiError as exc:
        fallback_fields = [field for field in fields if ":cf:" not in field]
        if not fallback_fields or fallback_fields == fields:
            return {"rtfFields": fields, "items": [], "resources": {"images": [], "attachments": [], "links": []}, "error": str(exc)}
        try:
            items = render_rich_text_fields(client, fallback_fields)
            fields = fallback_fields
        except ApiError as fallback_exc:
            return {
                "rtfFields": fields,
                "items": [],
                "resources": {"images": [], "attachments": [], "links": []},
                "error": str(fallback_exc),
            }
    extracted = extract_rtf_resources(items)
    compact_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        token = parse_rtf_value_token(item.get("rtfValueToken"))
        compact_items.append(
            {
                "taskId": item.get("taskId"),
                "rtfField": item.get("rtfField"),
                "htmlText": BeautifulSoup(item.get("html") or "", "html.parser").get_text("\n", strip=True)
                if BeautifulSoup is not None
                else "",
                "attachments": token.get("attachments", {}) if isinstance(token, dict) else {},
            }
        )
    return {"rtfFields": fields, "items": compact_items, "resources": extracted["resources"]}


def summarize_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task.get("id") or task.get("taskId"),
        "title": task.get("content"),
        "note": task.get("note"),
        "projectId": task.get("projectId"),
        "statusId": task.get("tfsId") or task.get("taskflowstatusId"),
        "executorId": task.get("executorId"),
        "firstExecutorId": first_executor_id(task),
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


def cmd_check_config(args: argparse.Namespace) -> None:
    params = {
        "TEAMBITION_TENANT_ID": env("TEAMBITION_TENANT_ID"),
        "TEAMBITION_USER_TOKEN": env("TEAMBITION_USER_TOKEN"),
    }
    result = {"configured": {}, "missing": []}
    for name, value in params.items():
        if value:
            display = mask_value(value, head=8, tail=4)
            result["configured"][name] = display
        else:
            result["missing"].append(name)

    if result["missing"]:
        result["status"] = "incomplete"
        result["hint"] = (
            "缺少参数: " + ", ".join(result["missing"])
            + "。请按以下方式获取：\n"
            "1. TENANT_ID: 浏览器地址栏 /organization/<id>/my 中的 id\n"
            "2. USER_TOKEN: 登录 https://open.teambition.com/user-mcp 后创建或查看 userToken\n"
            "当前用户 ID 会通过 GET /users/me 自动获取，不需要单独配置。\n"
            "获取后可通过 --tenant-id / --user-token 命令行参数传入，"
            "或保存到系统环境变量。"
        )
    else:
        result["status"] = "ok"
        client = TeambitionClient()
        profile = client.current_user()
        result["currentUser"] = {
            "userId": mask_value(user_id_from_profile(profile), head=6, tail=4),
            "profileLoaded": True,
            "source": "GET /users/me",
        }
    print_json(result)


def cmd_parse_url(args: argparse.Namespace) -> None:
    parsed = parse_teambition_url(args.url)
    if not parsed:
        raise SystemExit("未从链接中解析到 projectId、taskId 或 viewId。")
    print_json(parsed)


def cmd_search(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    project_id = require_project_id(args.project_id)
    result = client.request(
        "GET",
        f"/v3/project/{project_id}/task/query",
        params={
            "q": args.tql,
            "includeArchived": str(args.include_archived).lower(),
            "pageToken": args.page_token,
            "pageSize": args.page_size,
        },
    )
    print_json(filter_first_executor_self(client, result))


def summarize_project(project: dict[str, Any]) -> dict[str, Any]:
    project_id = project.get("id") or project.get("projectId")
    return {
        "id": project_id,
        "name": project.get("name"),
        "organizationId": project.get("organizationId"),
        "creatorId": project.get("creatorId"),
        "visibility": project.get("visibility"),
        "isArchived": project.get("isArchived"),
        "isDeleted": project.get("isDeleted"),
        "created": project.get("created"),
        "updated": project.get("updated"),
        "url": f"https://www.teambition.com/project/{project_id}" if project_id else None,
    }


def first_project(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        if not result:
            raise ApiError("未找到项目。")
        project = result[0]
        if isinstance(project, dict):
            return project
    if isinstance(result, dict) and isinstance(result.get("result"), list):
        if not result["result"]:
            raise ApiError("未找到项目。")
        project = result["result"][0]
        if isinstance(project, dict):
            return project
    if isinstance(result, dict):
        return result
    raise ApiError("无法识别项目响应格式。")


def cmd_project(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    project_id = args.project_id
    if not project_id and args.url:
        project_id = parse_teambition_url(args.url).get("projectId")
    project_id = require_project_id(project_id)
    result = client.request("GET", "/v3/project/query", params={"projectIds": project_id})
    project = first_project(result)
    output: dict[str, Any] = {"project": summarize_project(project)}
    if args.raw:
        output["rawProject"] = project
    print_json(output)


def get_task(client: TeambitionClient, task_id: str, *, action: str = "读取") -> dict[str, Any]:
    result = client.request("GET", "/v3/task/query", params={"taskId": task_id})
    task = first_task(result)
    ensure_first_executor_is_self(client, task, action=action)
    return task


def cmd_get(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    task = get_task(client, args.task_id)
    output: dict[str, Any] = {"task": summarize_task(task), "rawTask": task if args.raw else None}
    activities = None
    if args.with_activities:
        activities = list_activities(client, args.task_id, page_size=args.page_size)
        output["activities"] = activities
    if args.with_rich_text:
        traces = None
        try:
            traces = client.request("GET", f"/v3/task/{args.task_id}/traces")
        except ApiError:
            traces = None
        output["richTextRender"] = render_task_rich_text(client, task, traces)
    output["mediaResources"] = merge_media_resources(
        extract_media_resources(task),
        output.get("richTextRender", {}).get("resources", {}) if isinstance(output.get("richTextRender"), dict) else {},
    )
    output["imagePlaceholders"] = count_image_placeholders(task)
    output["imageAnalysisRequired"] = bool(output["mediaResources"]["images"] or output["imagePlaceholders"])
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
    get_task(client, args.task_id, action="读取动态")
    print_json(list_activities(client, args.task_id, page_size=args.page_size, actions=args.actions))


def cmd_comments(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    get_task(client, args.task_id, action="读取评论")
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
    get_task(client, args.task_id, action="读取进展")
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
    rich_text_render = render_task_rich_text(client, task, traces)
    media_resources = merge_media_resources(
        rich_text,
        extract_media_resources(task),
        extract_media_resources(activities),
        extract_media_resources(traces),
        rich_text_render.get("resources", {}),
    )
    image_placeholders = count_image_placeholders(task) + count_image_placeholders(activities) + count_image_placeholders(traces)

    print_json(
        {
            "task": summarize_task(task),
            "activities": activities,
            "traces": traces,
            "richTextLinks": rich_text,
            "richTextRender": rich_text_render,
            "mediaResources": media_resources,
            "imagePlaceholders": image_placeholders,
            "imageAnalysisRequired": bool(media_resources["images"] or image_placeholders),
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
    result = client.request(
        "GET",
        "/v3/task/rtf/render",
        params={"rtfFields": rtf_fields, "htmlExpireSeconds": args.html_expire_seconds},
    )
    rendered = json.dumps(result, ensure_ascii=False)
    print_json(
        {
            "result": result,
            "links": extract_links_from_html(html.unescape(rendered)),
            "rtfResources": extract_rtf_resources(result),
        }
    )


def cmd_download_images(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    task = get_task(client, args.task_id, action="下载图片")
    activities = list_activities(client, args.task_id, page_size=args.page_size)
    try:
        traces = client.request("GET", f"/v3/task/{args.task_id}/traces")
    except ApiError:
        traces = []
    rich_text_render = render_task_rich_text(client, task, traces)
    resources = merge_media_resources(
        extract_media_resources(task),
        extract_media_resources(activities),
        extract_media_resources(traces),
        rich_text_render.get("resources", {}),
    )
    image_urls = resources["images"]
    output_dir = Path(args.output_dir or ROOT / "outputs" / "teambition-images" / args.task_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for index, url in enumerate(image_urls, start=1):
        response = requests.get(url, timeout=(5, 30), stream=True)
        if response.status_code >= 400:
            downloaded.append({"url": url, "error": f"HTTP {response.status_code}", "body": response.text[:300]})
            continue
        file_path = output_dir / safe_download_name(url, index, response.headers.get("Content-Type"))
        total = 0
        with file_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 256):
                if chunk:
                    handle.write(chunk)
                    total += len(chunk)
        downloaded.append({"url": url, "path": str(file_path), "bytes": total})

    placeholders = count_image_placeholders(task) + count_image_placeholders(activities) + count_image_placeholders(traces)
    print_json(
        {
            "task": summarize_task(task),
            "outputDir": str(output_dir),
            "downloaded": downloaded,
            "richTextFields": rich_text_render.get("rtfFields", []),
            "imagePlaceholders": placeholders,
            "note": "下载后必须查看图片内容再判断 bug；如果富文本渲染后仍没有可访问 URL，请留言要求补充可访问截图。",
        }
    )


def cmd_comment(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    get_task(client, args.task_id, action="留言")
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
    "need-info": "我这边还缺少复现方式，暂时不能准确定位。请补充：从哪个页面进入、具体怎么操作、用的账号/数据、期望看到什么、实际出现了什么，最好再补一张能看清的截图。",
    "received": "已收到，我先确认复现路径和截图信息，有进展后同步。",
    "investigating": "我已开始排查，会先按你提供的步骤复现问题，有结果后同步。",
    "fixed": "问题已处理，请按原来的操作步骤重新验证一下。如还有异常，麻烦补充最新截图和现象。",
    "cannot-reproduce": "我按现有信息还没复现出来。请补充更完整的操作步骤、使用账号/数据、期望结果和实际现象。",
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


ACTIVE_STATUS_KEYWORDS = (
    "修改中",
    "修复中",
    "处理中",
    "进行中",
    "开发中",
    "已认领",
    "已领取",
    "已接收",
    "已开始",
    "排查中",
    "定位中",
    "修改",
    "修复",
    "处理",
    "认领",
    "领取",
    "接收",
    "开始",
    "进行",
    "开发",
    "排查",
    "定位",
)
INACTIVE_STATUS_KEYWORDS = (
    "完成",
    "关闭",
    "解决",
    "验收",
    "测试",
    "发布",
    "上线",
    "取消",
    "归档",
    "搁置",
    "挂起",
)
REVIEW_STATUS_KEYWORDS = (
    "待验收",
    "待验证",
    "待测试",
    "待确认",
    "待审核",
    "待检查",
    "验收中",
    "验证中",
    "测试中",
    "提测",
    "验收",
    "验证",
    "测试",
    "确认",
    "审核",
)
TERMINAL_STATUS_KEYWORDS = (
    "已完成",
    "完成",
    "关闭",
    "已关闭",
    "解决",
    "已解决",
    "已验收",
    "验收通过",
    "验证通过",
    "测试通过",
    "发布",
    "上线",
    "取消",
    "归档",
    "搁置",
    "挂起",
)


def is_active_status_request(status_name: str | None) -> bool:
    if not status_name:
        return False
    return any(keyword in status_name for keyword in ACTIVE_STATUS_KEYWORDS)


def is_review_status_request(status_name: str | None) -> bool:
    if not status_name:
        return False
    return any(keyword in status_name for keyword in REVIEW_STATUS_KEYWORDS)


def active_status_score(name: str) -> tuple[int, int]:
    if any(keyword in name for keyword in INACTIVE_STATUS_KEYWORDS):
        return (0, 0)
    matches = [index for index, keyword in enumerate(ACTIVE_STATUS_KEYWORDS) if keyword in name]
    if not matches:
        return (0, 0)
    return (1, -min(matches))


def review_status_score(name: str) -> tuple[int, int]:
    if any(keyword in name for keyword in TERMINAL_STATUS_KEYWORDS):
        return (0, 0)
    matches = [index for index, keyword in enumerate(REVIEW_STATUS_KEYWORDS) if keyword in name]
    if not matches:
        return (0, 0)
    return (1, -min(matches))


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
    if is_active_status_request(status_name):
        scored = sorted(
            (
                (active_status_score(str(item.get("name") or "")), item)
                for item in items
                if item.get("name")
            ),
            key=lambda pair: pair[0],
            reverse=True,
        )
        if scored and scored[0][0][0] > 0:
            return scored[0][1]
    if is_review_status_request(status_name):
        scored = sorted(
            (
                (review_status_score(str(item.get("name") or "")), item)
                for item in items
                if item.get("name")
            ),
            key=lambda pair: pair[0],
            reverse=True,
        )
        if scored and scored[0][0][0] > 0:
            return scored[0][1]
    candidates = [item.get("name") for item in items if item.get("name")]
    if is_active_status_request(status_name):
        raise ApiError(
            f"没有找到表示正在处理的近义状态: {status_name}。可用状态: {', '.join(candidates)}。"
            "请先确认该产品工作流中哪个状态表示已认领/修复中/处理中。"
        )
    if is_review_status_request(status_name):
        raise ApiError(
            f"没有找到表示待验收的近义状态: {status_name}。可用状态: {', '.join(candidates)}。"
            "请先确认该产品工作流中哪个状态表示待验收/待测试/待确认。"
        )
    raise ApiError(f"没有找到状态名称: {status_name}。可用状态: {', '.join(candidates)}")


def cmd_list_status(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    get_task(client, args.task_id, action="读取状态")
    print_json(list_statuses(client, args.task_id))


def cmd_start(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    task = get_task(client, args.task_id, action="更新状态")
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
    task = get_task(client, args.task_id, action="更新状态")
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


def cmd_finish(args: argparse.Namespace) -> None:
    if not args.note:
        args.note = "已处理完成，请验收。"
    cmd_update_status(args)


def cmd_update_title(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    get_task(client, args.task_id, action="更新标题")
    confirm_or_exit(f"将更新任务 {args.task_id} 标题。", args.yes)
    print_json(client.request("PUT", f"/v3/task/{args.task_id}/content", json_body={"content": args.title}))


def cmd_update_note(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    get_task(client, args.task_id, action="更新备注")
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
    get_task(client, args.task_id, action="更新执行人")
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
    get_task(client, args.task_id, action="更新优先级")
    confirm_or_exit(f"将更新任务 {args.task_id} 优先级。", args.yes)
    value: dict[str, Any] = {}
    try:
        value["priority"] = int(args.priority)
    except ValueError:
        value["priorityName"] = args.priority
    print_json(client.request("PUT", f"/v3/task/{args.task_id}/priority", json_body=value))


def cmd_update_due_date(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    get_task(client, args.task_id, action="更新截止时间")
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
    project_id = require_project_id(args.project_id)
    print_json(
        client.request(
            "GET",
            f"/v3/project/{project_id}/bug/commongroup",
            params={"pageSize": args.page_size, "pageToken": args.page_token},
        )
    )


def cmd_create_bug_group(args: argparse.Namespace) -> None:
    client = TeambitionClient()
    project_id = require_project_id(args.project_id)
    confirm_or_exit(f"将在项目 {project_id} 创建缺陷分类 {args.name}。", args.yes)
    body = {"name": args.name, "parentId": args.parent_id, "description": args.description}
    print_json(
        client.request(
            "POST",
            f"/v3/project/{project_id}/bug/commongroup/create",
            json_body={k: v for k, v in body.items() if v is not None},
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Teambition Bug OpenAPI helper")
    parser.add_argument("--tenant-id", dest="tenant_id", help="TEAMBITION_TENANT_ID，企业 ID")
    parser.add_argument("--user-token", dest="user_token", help="TEAMBITION_USER_TOKEN，个人账号 token")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-config", help="检测参数配置是否完整")
    p.set_defaults(func=cmd_check_config)

    p = sub.add_parser("parse-url", help="解析 Teambition 链接")
    p.add_argument("--url", required=True)
    p.set_defaults(func=cmd_parse_url)

    p = sub.add_parser("search", help="查询项目任务")
    p.add_argument("--project-id", help="项目/产品 ID，可从 Teambition 项目链接解析")
    p.add_argument("--tql", default="")
    p.add_argument("--page-size", type=int, default=10)
    p.add_argument("--page-token")
    p.add_argument("--include-archived", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("project", help="查询项目/产品详情")
    p.add_argument("--project-id", help="项目/产品 ID，可从 Teambition 项目链接解析")
    p.add_argument("--url", help="Teambition 项目分享链接，可自动提取 projectId")
    p.add_argument("--raw", action="store_true")
    p.set_defaults(func=cmd_project)

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
    p.add_argument("--html-expire-seconds", type=int, default=3600)
    p.set_defaults(func=cmd_render_rich_text)

    p = sub.add_parser("download-images", help="下载任务上下文中的图片，供 AI 识别截图内容")
    p.add_argument("--task-id", required=True)
    p.add_argument("--output-dir")
    p.add_argument("--page-size", type=int, default=50)
    p.set_defaults(func=cmd_download_images)

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
    p.add_argument("--status-name", default="修改中", help="优先精确匹配；找不到时匹配修复中/处理中/已认领等近义状态")
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

    p = sub.add_parser("finish", help="修复并验证完成后推进到待验收或近义状态")
    p.add_argument("--task-id", required=True)
    p.add_argument("--status-name", default="待验收", help="优先精确匹配；找不到时匹配待测试/待确认/待审核等近义状态")
    p.add_argument("--status-id")
    p.add_argument("--note")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_finish)

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
    p.add_argument("--project-id", help="项目/产品 ID，可从 Teambition 项目链接解析")
    p.add_argument("--page-size", type=int, default=50)
    p.add_argument("--page-token")
    p.set_defaults(func=cmd_list_bug_groups)

    p = sub.add_parser("create-bug-group", help="创建缺陷分类")
    p.add_argument("--project-id", help="项目/产品 ID，可从 Teambition 项目链接解析")
    p.add_argument("--name", required=True)
    p.add_argument("--parent-id")
    p.add_argument("--description")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_create_bug_group)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    set_runtime_env(args)
    try:
        args.func(args)
        return 0
    except (ConfigError, ApiError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
