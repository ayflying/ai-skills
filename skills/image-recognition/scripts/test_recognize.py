"""识图请求的离线异常与批处理回归。"""
import io
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

import requests

import recognize


class RecognizeTests(unittest.TestCase):
    def setUp(self):
        self.config = {"api_key": "test-secret", "base_url": "https://vision.example/v1", "model": "test-model"}
        self.args = recognize.build_parser().parse_args(["https://images.example/a.png"])

    def response(self, data=None, status=200):
        response = MagicMock(status_code=status)
        response.json.return_value = data if data is not None else {"choices": [{"message": {"content": " 图片描述 "}}]}
        response.__enter__.return_value = response
        return response

    def test_success_closes_response_and_disables_redirects(self):
        response = self.response()
        with patch("recognize.requests.post", return_value=response) as post:
            result = recognize.recognize_one(self.config, self.args.image[0], self.args)
        self.assertEqual(result, "图片描述")
        self.assertFalse(post.call_args.kwargs["allow_redirects"])
        self.assertEqual(post.call_args.kwargs["timeout"], 120)
        response.__exit__.assert_called_once()

    def test_http_and_redirect_errors_redacted(self):
        for status in (307, 308, 400, 500):
            with self.subTest(status=status):
                response = self.response({"error": {"message": "test-secret"}}, status=status)
                with patch("recognize.requests.post", return_value=response), self.assertRaises(RuntimeError) as error:
                    recognize.recognize_one(self.config, self.args.image[0], self.args)
                self.assertIn(str(status), str(error.exception))
                self.assertNotIn("test-secret", str(error.exception))
                response.json.assert_not_called()
                response.__exit__.assert_called_once()

    def test_network_errors_normalized_and_redacted(self):
        for error in (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.SSLError):
            with self.subTest(error=error), patch("recognize.requests.post", side_effect=error("test-secret")), self.assertRaises(RuntimeError) as caught:
                recognize.recognize_one(self.config, self.args.image[0], self.args)
            self.assertNotIn("test-secret", str(caught.exception))

    def test_invalid_json(self):
        response = self.response()
        response.json.side_effect = ValueError("test-secret")
        with patch("recognize.requests.post", return_value=response), self.assertRaisesRegex(RuntimeError, "无效 JSON"):
            recognize.recognize_one(self.config, self.args.image[0], self.args)
        response.__exit__.assert_called_once()

    def test_malformed_response_structures(self):
        for data in ([], "text", {}, {"choices": {}}, {"choices": [None]}, {"choices": [{}]}, {"choices": [{"message": []}]}, {"choices": [{"message": {"content": ["not-text"]}}]}, {"choices": [{"message": {"content": " "}}]}):
            with self.subTest(data=data), patch("recognize.requests.post", return_value=self.response(data)), self.assertRaises(RuntimeError):
                recognize.recognize_one(self.config, self.args.image[0], self.args)

    def test_positive_parameters(self):
        for option in ("--timeout", "--max-tokens"):
            for value in ("0", "-1", "not-number"):
                with self.subTest(option=option, value=value), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    recognize.build_parser().parse_args(["image.png", option, value])

    def test_missing_config_lists_variables_without_network(self):
        with patch.dict(os.environ, {}, clear=True), patch("recognize.requests.post") as post, self.assertRaises(RuntimeError) as error:
            recognize.resolve_config(None)
        self.assertIn(recognize.API_KEY_ENV, str(error.exception))
        self.assertIn(recognize.BASE_URL_ENV, str(error.exception))
        self.assertIn(recognize.MODEL_ENV, str(error.exception))
        post.assert_not_called()

    def test_local_read_failure_normalized(self):
        with patch("recognize.Path.is_file", return_value=True), patch("recognize.Path.read_bytes", side_effect=PermissionError("test-secret")), self.assertRaisesRegex(RuntimeError, "无法读取本地图片"):
            recognize.build_image_url("image.png")

    def test_batch_continues_after_timeout(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch("sys.argv", ["recognize.py", "https://images.example/a.png", "https://images.example/b.png"]), patch("recognize.resolve_config", return_value=self.config), patch("recognize.requests.post", side_effect=[requests.exceptions.Timeout("test-secret"), self.response()]) as post, redirect_stdout(output), redirect_stderr(errors):
            code = recognize.main()
        self.assertEqual(code, 1)
        self.assertEqual(post.call_count, 2)
        self.assertIn("识别失败", output.getvalue())
        self.assertIn("图片描述", output.getvalue())
        self.assertNotIn("test-secret", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
