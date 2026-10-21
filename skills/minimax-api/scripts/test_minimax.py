"""MiniMax 离线回归测试；所有网络与付费生成均使用模拟。"""

import asyncio
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import ssl
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import requests

import minimax


class MiniMaxTests(unittest.TestCase):
    def setUp(self):
        self.client = minimax.MiniMaxAPI(api_key="test-placeholder")

    def test_http_error_closes_response(self):
        response = MagicMock(status_code=200)
        response.raise_for_status.side_effect = requests.HTTPError("敏感原始错误")
        with patch.object(minimax.requests, "post", return_value=response):
            with self.assertRaises(requests.HTTPError):
                self.client.image_generate("测试")
        response.close.assert_called_once()

    def test_business_error_and_invalid_json_close_response(self):
        for payload in ({"base_resp": {"status_code": 1004}}, []):
            response = MagicMock(status_code=200)
            response.json.return_value = payload
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                minimax._response_json(response)
            response.close.assert_called_once()
        response = MagicMock(status_code=200)
        response.json.side_effect = ValueError("原始响应")
        with self.assertRaises(ValueError):
            minimax._response_json(response)
        response.close.assert_called_once()

    def test_success_closes_response_and_keeps_result(self):
        response = MagicMock(status_code=200)
        response.json.return_value = {"content": []}
        with patch.object(minimax.requests, "post", return_value=response) as post:
            self.assertEqual(self.client.text_chat("测试"), {"content": []})
        self.assertGreater(post.call_args.kwargs["timeout"], 0)
        response.close.assert_called_once()

    def test_api_requests_reject_redirects_without_parsing_body(self):
        calls = [
            lambda: self.client.text_chat("测试"),
            lambda: self.client.tts("测试"),
            lambda: self.client.voice_clone("file-id", "voice-id", "测试"),
            lambda: self.client.image_generate("测试"),
            lambda: self.client.video_generate(prompt="测试"),
            lambda: self.client.video_query("task-id"),
            lambda: self.client.music_generate("测试"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.wav"
            source.write_bytes(b"placeholder")
            calls += [
                lambda: self.client.voice_clone_upload_file(source),
                lambda: self.client.voice_clone_upload_prompt(source),
                lambda: self.client.image_i2i(source, "测试"),
            ]
            for status in (301, 302, 307, 308):
                for call in calls:
                    response = MagicMock(status_code=status)
                    with self.subTest(status=status, call=call), patch.object(minimax.requests, "post", return_value=response) as post, patch.object(minimax.requests, "get", return_value=response) as get:
                        with self.assertRaises(requests.HTTPError):
                            call()
                        request = post if post.called else get
                        self.assertFalse(request.call_args.kwargs["allow_redirects"])
                        response.json.assert_not_called()
                        response.close.assert_called_once()

    def test_download_is_atomic_and_closes_response_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "result.png"
            destination.write_bytes(b"original")
            response = MagicMock(status_code=200)
            response.__enter__.return_value = response

            def chunks(**kwargs):
                yield b"partial"
                raise requests.Timeout("包含签名和凭证的错误")

            response.iter_content.side_effect = chunks
            with patch.object(minimax.requests, "get", return_value=response) as get:
                with self.assertRaises(requests.Timeout):
                    minimax._download_file("https://example.test/image", destination)
            self.assertEqual(destination.read_bytes(), b"original")
            self.assertEqual(list(Path(directory).iterdir()), [destination])
            self.assertEqual(get.call_args.kwargs["timeout"], (10, 60))
            self.assertTrue(get.call_args.kwargs["stream"])
            response.__exit__.assert_called_once()

    def test_download_http_error_does_not_create_output(self):
        response = MagicMock(status_code=200)
        response.__enter__.return_value = response
        response.raise_for_status.side_effect = requests.HTTPError("失败")
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "output.mp3"
            with patch.object(minimax.requests, "get", return_value=response):
                with self.assertRaises(requests.HTTPError):
                    minimax._download_music({"data": {"audio_url": "https://example.test/a"}}, destination)
            self.assertFalse(destination.exists())
        response.__exit__.assert_called_once()

    def test_missing_url_and_invalid_scheme_fail(self):
        with self.assertRaises(ValueError):
            minimax._download_image({})
        with self.assertRaises(ValueError):
            minimax._download_music({})
        with self.assertRaises(ValueError):
            minimax._download_music({"data": {"audio": "deadbeef"}})
        with patch.object(minimax.requests, "get") as get:
            with self.assertRaises(ValueError):
                minimax._download_file("file:///secret", "unused")
            get.assert_not_called()

    def test_download_empty_body_does_not_replace_existing_file(self):
        response = MagicMock(status_code=200)
        response.__enter__.return_value = response
        response.iter_content.return_value = [b""]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "output.png"
            destination.write_bytes(b"original")
            with patch.object(minimax.requests, "get", return_value=response):
                with self.assertRaises(ValueError):
                    minimax._download_file("https://example.test/a", destination)
            self.assertEqual(destination.read_bytes(), b"original")
            self.assertEqual(list(Path(directory).iterdir()), [destination])

    def test_download_success_writes_complete_content(self):
        response = MagicMock(status_code=200)
        response.__enter__.return_value = response
        response.iter_content.return_value = [b"first", b"", b"second"]
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "output.png"
            with patch.object(minimax.requests, "get", return_value=response), redirect_stdout(io.StringIO()):
                minimax._download_file("https://example.test/a", destination)
            self.assertEqual(destination.read_bytes(), b"firstsecond")
        response.__exit__.assert_called_once()

    def run_cli(self, argv):
        output = io.StringIO()
        with patch.object(sys, "argv", ["minimax.py", *argv]), redirect_stderr(output), redirect_stdout(output):
            return minimax.main(), output.getvalue()

    def test_cli_requires_subcommand(self):
        with patch.object(sys, "argv", ["minimax.py"]), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                minimax.main()
        self.assertEqual(error.exception.code, 2)

    def test_cli_missing_config_has_no_traceback(self):
        with patch.dict(os.environ, {}, clear=True):
            status, output = self.run_cli(["chat", "测试"])
        self.assertEqual(status, 1)
        self.assertIn("MINIMAX_API_KEY", output)
        self.assertNotIn("Traceback", output)

    def test_cli_http_error_redacts_raw_response(self):
        response = MagicMock(status_code=403, text="private-token-and-body")
        error = requests.HTTPError("private-url-and-key", response=response)
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "placeholder"}), patch.object(minimax.MiniMaxAPI, "text_chat", side_effect=error):
            status, output = self.run_cli(["chat", "测试"])
        self.assertEqual(status, 1)
        self.assertIn("403", output)
        self.assertNotIn("private", output)

    def test_cli_download_failure_returns_nonzero(self):
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "placeholder"}), patch.object(minimax.MiniMaxAPI, "image_generate", return_value={"data": {"image_urls": ["https://example.test/a"]}}), patch.object(minimax.requests, "get", side_effect=requests.Timeout("secret-url")):
            status, output = self.run_cli(["image", "测试", "--download"])
        self.assertEqual(status, 1)
        self.assertIn("超时", output)
        self.assertNotIn("secret", output)
        self.assertNotIn("已保存", output)


class WebSocketTests(unittest.IsolatedAsyncioTestCase):
    def fake_websockets(self, ws):
        context = MagicMock()
        context.__aenter__ = AsyncMock(return_value=ws)
        context.__aexit__ = AsyncMock(return_value=False)
        module = types.SimpleNamespace(connect=MagicMock(return_value=context))
        return module, context

    async def test_tls_enabled_and_success_closes_socket(self):
        ws = types.SimpleNamespace(send=AsyncMock(), recv=AsyncMock(side_effect=[
            json.dumps({"event": "connected_success"}),
            json.dumps({"event": "task_started"}),
            json.dumps({"data": {"audio": "0102"}, "is_final": True}),
        ]))
        module, context = self.fake_websockets(ws)
        with patch.dict(sys.modules, {"websockets": module}):
            result = await minimax.MiniMaxAPI(api_key="placeholder").tts_websocket("测试")
        self.assertEqual(result, b"\x01\x02")
        ssl_context = module.connect.call_args.kwargs["ssl"]
        self.assertTrue(ssl_context.check_hostname)
        self.assertEqual(ssl_context.verify_mode, ssl.CERT_REQUIRED)
        context.__aexit__.assert_awaited_once()

    async def test_receive_timeout_closes_socket(self):
        ws = types.SimpleNamespace(send=AsyncMock(), recv=AsyncMock(side_effect=asyncio.TimeoutError))
        module, context = self.fake_websockets(ws)
        with patch.dict(sys.modules, {"websockets": module}):
            with self.assertRaises(asyncio.TimeoutError):
                await minimax.MiniMaxAPI(api_key="placeholder").tts_websocket("测试", recv_timeout=0.1)
        context.__aexit__.assert_awaited_once()

    async def test_total_timeout_limits_sending(self):
        async def blocked_send(*args):
            await asyncio.Event().wait()

        ws = types.SimpleNamespace(send=blocked_send, recv=AsyncMock(return_value=json.dumps({"event": "connected_success"})))
        module, context = self.fake_websockets(ws)
        with patch.dict(sys.modules, {"websockets": module}):
            with self.assertRaises(asyncio.TimeoutError):
                await minimax.MiniMaxAPI(api_key="placeholder").tts_websocket("测试", recv_timeout=1, total_timeout=0.2)
        context.__aexit__.assert_awaited_once()

    async def test_bad_start_never_exposes_raw_response(self):
        ws = types.SimpleNamespace(send=AsyncMock(), recv=AsyncMock(side_effect=[
            json.dumps({"event": "connected_success"}),
            json.dumps({"event": "error", "secret": "do-not-print"}),
        ]))
        module, _ = self.fake_websockets(ws)
        with patch.dict(sys.modules, {"websockets": module}):
            with self.assertRaisesRegex(ValueError, "^语音任务启动失败$"):
                await minimax.MiniMaxAPI(api_key="placeholder").tts_websocket("测试")


if __name__ == "__main__":
    unittest.main()
