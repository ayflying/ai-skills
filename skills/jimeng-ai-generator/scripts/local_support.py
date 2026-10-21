"""即梦本地服务共用的请求边界、受限下载和命令执行工具。"""

from __future__ import annotations

import http.client
import http.server
import ipaddress
import json
import os
import re
import shutil
import socket
import ssl
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit

SKILL_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = SKILL_DIR / "outputs"
BROWSER_PROFILE = SKILL_DIR / "browser-profile"
ALLOWED_ORIGINS = frozenset({"https://jimeng.jianying.com"})
MAX_BODY_BYTES = 64 * 1024
MAX_IMAGE_BYTES = 25 * 1024 * 1024
DOWNLOAD_TIMEOUT = 30
MAX_REDIRECTS = 3


class InputError(ValueError):
    """客户端输入不符合安全边界。"""


def validate_task_id(value: object) -> str:
    """任务标识仅允许不构成路径的 ASCII 字符。"""
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value):
        raise InputError("任务 ID 必须为 1 至 100 个字母、数字、下划线或连字符")
    return value


def validate_task(data: dict) -> dict:
    task_id = validate_task_id(data.get("id", f"task_{uuid.uuid4().hex}"))
    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 10000:
        raise InputError("提示词必须为 1 至 10000 个字符")
    return {"id": task_id, "prompt": prompt}


def public_target(url: str) -> tuple[str, str, int, str, str]:
    """校验每一跳 URL 和全部 DNS 地址，返回用于固定连接的公网 IP。"""
    if not isinstance(url, str) or len(url) > 8192 or any(ord(c) < 32 for c in url):
        raise InputError("图片 URL 无效")
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise InputError("图片 URL 只允许无用户凭证的 HTTP(S) 地址")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    if port != (443 if parts.scheme == "https" else 80):
        raise InputError("图片 URL 只允许标准 HTTP(S) 端口")
    host = parts.hostname.encode("idna").decode("ascii")
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ips = [item[4][0] for item in addresses]
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise InputError("图片地址不得指向本机、内网或其他非公网地址")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return parts.scheme, host, port, ips[0], path


def download_image(url: str, task_id: str, output_dir: Path = OUTPUT_DIR) -> Path:
    """固定已校验的公网 IP，逐跳检查重定向，限时限量保存图片。"""
    task_id = validate_task_id(task_id)
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{task_id}_{uuid.uuid4().hex}.png"
    # 文件名不接受路径；目录解析后再次确认边界，临时文件使用独占创建。
    if destination.resolve().parent != output_dir:
        raise InputError("图片输出路径越界")
    deadline = time.monotonic() + DOWNLOAD_TIMEOUT
    for redirect in range(MAX_REDIRECTS + 1):
        scheme, host, port, ip, path = public_target(url)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("图片下载超时")
        connection = http.client.HTTPConnection(host, port, timeout=remaining)
        try:
            # 不再对 host 进行二次 DNS 解析，避免 DNS 重绑定绕过地址检查。
            connection.sock = socket.create_connection((ip, port), timeout=remaining)
            if scheme == "https":
                connection.sock = ssl.create_default_context().wrap_socket(
                    connection.sock, server_hostname=host
                )
            download_socket = connection.sock
            connection.request("GET", path, headers={"Host": host, "Accept": "image/*"})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location or redirect == MAX_REDIRECTS:
                    raise InputError("图片重定向无效或次数过多")
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise InputError(f"图片下载失败，HTTP {response.status}")
            if not response.getheader("Content-Type", "").lower().startswith("image/"):
                raise InputError("下载响应不是图片")
            length = response.getheader("Content-Length")
            if length is not None and (not length.isdigit() or int(length) > MAX_IMAGE_BYTES):
                raise InputError("图片大小无效或超过 25 MiB")
            size = 0
            created = False
            try:
                with destination.open("xb") as target:
                    created = True
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError("图片下载超时")
                        download_socket.settimeout(remaining)
                        chunk = response.read1(min(64 * 1024, MAX_IMAGE_BYTES - size + 1))
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > MAX_IMAGE_BYTES:
                            raise InputError("图片超过 25 MiB")
                        target.write(chunk)
                        if response.isclosed():
                            break
                if not size or (length is not None and size != int(length)):
                    raise InputError("图片下载为空或未完整接收")
            except Exception:
                # 只清理本次独占创建的失败下载，绝不清理既有产物。
                if created:
                    destination.unlink(missing_ok=True)
                raise
            return destination
        finally:
            connection.close()
    raise InputError("图片下载失败")


class LocalHandler(http.server.BaseHTTPRequestHandler):
    """仅信任回环 Host 与即梦 Origin；无 Origin 的本机 CLI 仍可调用。"""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def trusted_request(self) -> bool:
        port = self.server.server_address[1]
        allowed_hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
        origin = self.headers.get("Origin")
        fetch_site = self.headers.get("Sec-Fetch-Site")
        return (
            self.headers.get("Host", "").lower() in allowed_hosts
            and (origin is None or origin in ALLOWED_ORIGINS)
            and not (origin is None and fetch_site not in {None, "none", "same-origin"})
        )

    def send_json(self, status: int, data: dict) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def require_trusted(self) -> bool:
        if not self.trusted_request():
            self.close_connection = True
            self.send_json(403, {"success": False, "error": "不允许的 Host 或 Origin"})
            return False
        return True

    def read_json(self) -> dict:
        if self.headers.get("Transfer-Encoding"):
            raise InputError("不支持分块请求体")
        length = self.headers.get("Content-Length", "0")
        if not length.isdigit() or not 0 < int(length) <= MAX_BODY_BYTES:
            raise InputError("请求体必须为 1 至 65536 字节")
        if self.headers.get_content_type() != "application/json":
            raise InputError("请求体必须为 application/json")
        body = self.rfile.read(int(length))
        if len(body) != int(length):
            raise InputError("请求体不完整")
        try:
            data = json.loads(body)
        except (ValueError, UnicodeError) as exc:
            raise InputError("JSON 格式无效") from exc
        if not isinstance(data, dict):
            raise InputError("JSON 请求体必须为对象")
        return data

    def do_OPTIONS(self) -> None:
        if self.require_trusted():
            self.send_json(200, {"success": True})

    def log_message(self, format: str, *args: object) -> None:
        # 不记录查询参数、下载签名 URL 或提示词。
        return


def run_browser_command(args: list[str], timeout: int = 30) -> str:
    """直接执行可执行文件，不经过 Shell；Windows .cmd 通过 Node 入口运行。"""
    executable = shutil.which("agent-browser")
    if not executable:
        raise RuntimeError("找不到 agent-browser，请先安装并加入 PATH")
    command = [executable]
    if Path(executable).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        node = shutil.which("node")
        entry = Path(executable).parent / "node_modules" / "agent-browser" / "bin" / "agent-browser.js"
        if not node or not entry.is_file():
            raise RuntimeError("无法定位 agent-browser 的 Node 入口，请安装原生命令或标准 npm 包")
        command = [node, str(entry)]
    result = subprocess.run(
        command + args, shell=False, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout, check=True,
        cwd=SKILL_DIR,
    )
    return result.stdout
