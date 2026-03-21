#!/usr/bin/env python3
"""
opencode-api 技能核心执行器
通过 HTTP API 与 OpenCode 服务器交互
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error
import urllib.parse
import base64
import uuid
import time

DEFAULT_SERVER_URL = "http://127.0.0.1:4096"
DEFAULT_MODEL = "opencode/mimo-v2-omni-free"
TIMEOUT = 120


class OpenCodeAPIError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class OpenCodeClient:
    def __init__(self, server_url, username=None, password=None):
        self.server_url = server_url.rstrip("/")
        self.auth = None
        if username and password:
            credentials = f"{username}:{password}"
            self.auth = "Basic " + base64.b64encode(credentials.encode()).decode()

    def _request(self, method, path, data=None, stream=False):
        url = f"{self.server_url}{path}"
        headers = {"Content-Type": "application/json"}
        if self.auth:
            headers["Authorization"] = self.auth

        body = json.dumps(data).encode("utf-8") if data else None

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                if stream:
                    return resp
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                raise OpenCodeAPIError(e.code, error_body.get("error", str(e)))
            except:
                raise OpenCodeAPIError(e.code, str(e))
        except urllib.error.URLError as e:
            raise OpenCodeAPIError("CONNECTION", f"无法连接到服务器: {e.reason}")

    def health_check(self):
        return self._request("GET", "/global/health")

    def create_session(self, parent_id=None, title=None):
        data = {}
        if parent_id:
            data["parentID"] = parent_id
        if title:
            data["title"] = title
        return self._request("POST", "/session", data if data else None)

    def get_session(self, session_id):
        return self._request("GET", f"/session/{session_id}")

    def get_session_status(self):
        return self._request("GET", "/session/status")

    def send_message(self, session_id, message, model=None, no_reply=False):
        data = {"parts": [{"type": "text", "text": message}]}
        if model:
            data["model"] = model
        if no_reply:
            self._request("POST", f"/session/{session_id}/prompt_async", data)
            return {"success": True, "async": True}
        result = self._request("POST", f"/session/{session_id}/message", data)
        return result

    def abort_session(self, session_id):
        return self._request("POST", f"/session/{session_id}/abort")

    def delete_session(self, session_id):
        return self._request("DELETE", f"/session/{session_id}")

    def get_project(self):
        return self._request("GET", "/project")

    def get_current_project(self):
        return self._request("GET", "/project/current")

    def read_file(self, path):
        return self._request("GET", f"/file/content?path={urllib.parse.quote(path)}")

    def search_files(self, pattern):
        return self._request("GET", f"/find?pattern={urllib.parse.quote(pattern)}")

    def list_providers(self):
        return self._request("GET", "/provider")

    def list_commands(self):
        return self._request("GET", "/command")

    def list_agents(self):
        return self._request("GET", "/agent")


def run_opencode_task(
    prompt,
    server_url=None,
    model=None,
    session_id=None,
    title=None,
    no_reply=False,
    json_output=False,
):
    if server_url is None:
        server_url = os.environ.get("OPENCODE_SERVER_URL", DEFAULT_SERVER_URL)
    if model is None:
        model = os.environ.get("OPENCODE_MODEL", DEFAULT_MODEL)

    username = os.environ.get("OPENCODE_SERVER_USERNAME")
    password = os.environ.get("OPENCODE_SERVER_PASSWORD")

    client = OpenCodeClient(server_url, username, password)

    try:
        health = client.health_check()
        if not health.get("healthy"):
            return {"success": False, "error": "服务器健康检查失败"}

        if session_id:
            try:
                client.get_session(session_id)
            except OpenCodeAPIError:
                return {"success": False, "error": f"会话 {session_id} 不存在"}
        else:
            session_data = client.create_session(title=title)
            session_id = session_data.get("id") or session_data.get("sessionID")
            if not session_id:
                return {"success": False, "error": "创建会话失败"}

        result = client.send_message(session_id, prompt, model=model, no_reply=no_reply)

        if no_reply:
            return {
                "success": True,
                "session_id": session_id,
                "async": True,
                "message": "消息已发送，不等待响应",
            }

        output = ""
        parts = []
        if isinstance(result, dict):
            parts_data = result.get("parts")
            if isinstance(parts_data, list):
                parts = parts_data
        for part in parts:
            if part.get("type") == "text":
                output += part.get("text", "")
            elif part.get("type") == "tool_call":
                output += f"\n[Tool: {part.get('name', 'unknown')}]\n"

        return {"success": True, "session_id": session_id, "output": output.strip()}

    except OpenCodeAPIError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"执行异常: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description="OpenCode API 执行器")
    parser.add_argument("prompt", help="要执行的任务描述")
    parser.add_argument("--server", help="OpenCode 服务器地址", default=None)
    parser.add_argument("--model", help="使用的模型", default=None)
    parser.add_argument("--session", help="会话 ID（继续已有会话）", default=None)
    parser.add_argument("--title", help="会话标题", default=None)
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出结果")
    parser.add_argument("--no-reply", action="store_true", help="发送消息但不等待响应")

    args = parser.parse_args()

    result = run_opencode_task(
        prompt=args.prompt,
        server_url=args.server,
        model=args.model,
        session_id=args.session,
        title=args.title,
        no_reply=args.no_reply,
    )

    if args.json:
        sys.stdout.buffer.write(
            json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8")
        )
    else:
        if result["success"]:
            sys.stdout.buffer.write(result.get("output", "").encode("utf-8"))
        else:
            sys.stderr.buffer.write(f"错误: {result['error']}".encode("utf-8"))
            sys.exit(1)


if __name__ == "__main__":
    main()
