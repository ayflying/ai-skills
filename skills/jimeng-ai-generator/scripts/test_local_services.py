"""仅用模拟下载和回环 HTTP 服务验证安全边界，不调用浏览器或线上生成。"""

import http.client
import io
import json
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import agent_jimeng_server
import local_support
import task_server


class DownloadTests(unittest.TestCase):
    def test_rejects_protocol_credentials_ports_and_private_addresses(self):
        for url in ("file:///etc/passwd", "ftp://example.com/a", "http://u:p@example.com/a", "https://example.com:8443/a"):
            with self.subTest(url=url), self.assertRaises(local_support.InputError):
                local_support.public_target(url)
        for ip in ("127.0.0.1", "10.0.0.1", "169.254.169.254", "::1", "192.168.1.1"):
            with self.subTest(ip=ip), patch.object(local_support.socket, "getaddrinfo", return_value=[(0, 0, 0, "", (ip, 80))]):
                with self.assertRaises(local_support.InputError):
                    local_support.public_target("http://example.com/a")

    def test_rejects_task_path_escape(self):
        for task_id in ("../bad", "a/b", "C:\\bad", "", None):
            with self.subTest(task_id=task_id), self.assertRaises(local_support.InputError):
                local_support.validate_task_id(task_id)

    def response(self, body=b"png", status=200, headers=None):
        response = MagicMock()
        response.status = status
        response.isclosed.return_value = False
        response.getheader.side_effect = lambda key, default=None: (headers or {"Content-Type": "image/png", "Content-Length": str(len(body))}).get(key, default)
        stream = io.BytesIO(body)
        response.read1.side_effect = stream.read
        return response

    def download(self, folder, responses):
        connection = MagicMock()
        connection.getresponse.side_effect = responses
        patches = (
            patch.object(local_support.socket, "getaddrinfo", return_value=[(0, 0, 0, "", ("8.8.8.8", 80))]),
            patch.object(local_support.socket, "create_connection", return_value=MagicMock()),
            patch.object(local_support.http.client, "HTTPConnection", return_value=connection),
        )
        with patches[0], patches[1], patches[2]:
            result = local_support.download_image("http://example.com/image", "test", Path(folder))
        return result, connection

    def test_download_success_and_closes_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            result, connection = self.download(folder, [self.response()])
            self.assertEqual(result.read_bytes(), b"png")
            self.assertEqual(result.parent, Path(folder).resolve())
            connection.close.assert_called_once()

    def test_rejects_redirect_to_local_file(self):
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(local_support.InputError):
            self.download(folder, [self.response(status=302, headers={"Location": "file:///etc/passwd"})])

    def test_rejects_excessive_redirects(self):
        redirects = [self.response(status=302, headers={"Location": "/again"}) for _ in range(4)]
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(local_support.InputError):
            self.download(folder, redirects)

    def test_rejects_redirect_to_private_address(self):
        addresses = [[(0, 0, 0, "", ("8.8.8.8", 80))], [(0, 0, 0, "", ("127.0.0.1", 80))]]
        connection = MagicMock()
        connection.getresponse.return_value = self.response(status=302, headers={"Location": "http://localhost/a"})
        with tempfile.TemporaryDirectory() as folder, patch.object(local_support.socket, "getaddrinfo", side_effect=addresses), patch.object(local_support.socket, "create_connection", return_value=MagicMock()), patch.object(local_support.http.client, "HTTPConnection", return_value=connection):
            with self.assertRaises(local_support.InputError):
                local_support.download_image("http://example.com/a", "test", Path(folder))

    def test_rejects_oversized_non_image_and_error_responses(self):
        responses = [self.response(headers={"Content-Type": "text/html"}), self.response(status=404), self.response(headers={"Content-Type": "image/png", "Content-Length": str(local_support.MAX_IMAGE_BYTES + 1)})]
        for response in responses:
            with tempfile.TemporaryDirectory() as folder, self.assertRaises(local_support.InputError):
                self.download(folder, [response])

    def test_enforces_stream_limit_and_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(local_support, "MAX_IMAGE_BYTES", 2):
            with self.assertRaises(local_support.InputError):
                self.download(folder, [self.response(body=b"abcd", headers={"Content-Type": "image/png"})])
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_timeout_removes_partial_file(self):
        response = self.response(headers={"Content-Type": "image/png"})
        response.read1.side_effect = [b"p", TimeoutError("模拟超时")]
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(TimeoutError):
                self.download(folder, [response])
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_slow_chunks_recheck_body_deadline(self):
        response = self.response(headers={"Content-Type": "image/png"})
        # 每次读取仅前进一步；下一次读取前必须重新计算剩余总预算。
        response.read1.side_effect = [b"p", b"n", b"g"]
        with tempfile.TemporaryDirectory() as folder, patch.object(local_support.time, "monotonic", side_effect=[0, 1, 2, 31]):
            with self.assertRaises(TimeoutError):
                self.download(folder, [response])
            self.assertEqual(response.read1.call_count, 1)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_exclusive_create_does_not_remove_existing_file(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(local_support.uuid, "uuid4") as uuid:
            uuid.return_value.hex = "fixed"
            existing = Path(folder) / "test_fixed.png"
            existing.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                self.download(folder, [self.response()])
            self.assertEqual(existing.read_bytes(), b"existing")

    def test_connection_uses_checked_ip(self):
        with patch.object(local_support.socket, "getaddrinfo", return_value=[(0, 0, 0, "", ("8.8.8.8", 80))]):
            self.assertEqual(local_support.public_target("http://example.com/a?q=1"), ("http", "example.com", 80, "8.8.8.8", "/a?q=1"))


class LocalServiceTests(unittest.TestCase):
    def setUp(self):
        self.original_tasks = task_server.TASKS[:]
        task_server.TASKS[:] = [{"id": "test", "prompt": "测试"}]
        task_server.IN_FLIGHT.clear()
        self.server = socketserver.TCPServer(("127.0.0.1", 0), task_server.AtomicTaskHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        task_server.TASKS[:] = self.original_tasks
        task_server.IN_FLIGHT.clear()

    def request(self, path, method="GET", data=None, headers=None):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        body = json.dumps(data) if data is not None else None
        request_headers = {"Origin": "https://jimeng.jianying.com", "Content-Type": "application/json"}
        request_headers.update(headers or {})
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally:
            connection.close()

    def claim(self):
        return self.request(f"/get_task?v={task_server.VERSION}")

    def test_claim_once_and_json_headers(self):
        status, headers, data = self.claim()
        self.assertEqual((status, data["id"]), (200, "test"))
        self.assertEqual(headers["Access-Control-Allow-Origin"], "https://jimeng.jianying.com")
        self.assertIn("application/json", headers["Content-Type"])
        self.assertEqual(self.claim()[2], {})

    def test_rejects_bad_host_origin_and_version(self):
        self.assertEqual(self.request("/get_task", headers={"Host": "evil.test"})[0], 403)
        self.assertEqual(self.request("/get_task", headers={"Origin": "https://evil.test"})[0], 403)
        self.assertEqual(self.request("/get_task?v=old")[0], 409)

    def test_preflight_and_unknown_path(self):
        self.assertEqual(self.request("/save_image", "OPTIONS")[0], 200)
        self.assertEqual(self.request("/unknown")[0], 404)
        self.assertEqual(self.request("/save_image_evil", "POST", {})[0], 404)

    def test_cannot_finish_before_successful_save(self):
        self.claim()
        self.assertEqual(self.request("/finish_task?id=test&status=done", "POST")[0], 400)
        with patch.object(task_server, "download_image", return_value=Path("saved.png")):
            self.assertEqual(self.request("/save_image", "POST", {"taskId": "test", "url": "http://example.com/a"})[2]["success"], True)
        self.assertEqual(self.request("/finish_task?id=test&status=done", "POST")[0], 200)

    def test_download_failure_not_success(self):
        self.claim()
        with patch.object(task_server, "download_image", side_effect=TimeoutError):
            self.assertEqual(self.request("/save_image", "POST", {"taskId": "test", "url": "http://example.com/a"})[0], 502)
        self.assertFalse(task_server.IN_FLIGHT["test"]["saved"])
        self.assertEqual(self.request("/finish_task?id=test&status=failed", "POST")[0], 200)
        self.assertEqual(task_server.TASKS, [])

    def test_rejects_json_shape_and_body_limit(self):
        self.assertEqual(self.request("/save_image", "POST", [1])[0], 400)
        self.assertEqual(self.request("/save_image", "POST", {"x": "a" * local_support.MAX_BODY_BYTES})[0], 400)


class AgentCommandTests(unittest.TestCase):
    def test_prompt_json_escaped(self):
        prompt = '\"; bad(); //\n中文 & echo bad'
        script = agent_jimeng_server.prompt_script(prompt)
        self.assertIn(json.dumps(prompt, ensure_ascii=True), script)
        self.assertNotIn('el.innerText = ""; bad()', script)

    def test_command_uses_array_without_shell(self):
        with patch.object(local_support.shutil, "which", return_value="/bin/agent-browser"), patch.object(local_support.subprocess, "run") as run:
            run.return_value.stdout = "ok"
            local_support.run_browser_command(["fill", "@e1", 'a & b " c'])
            self.assertFalse(run.call_args.kwargs["shell"])
            self.assertEqual(run.call_args.args[0][-1], 'a & b " c')
            self.assertTrue(run.call_args.kwargs["check"])

    def test_missing_command_reports_configuration(self):
        with patch.object(local_support.shutil, "which", return_value=None), self.assertRaisesRegex(RuntimeError, "找不到"):
            local_support.run_browser_command(["open"])


if __name__ == "__main__":
    unittest.main()
