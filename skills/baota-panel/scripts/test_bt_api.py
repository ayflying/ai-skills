"""宝塔客户端的离线请求及授权边界回归。"""
import os
import unittest
from unittest.mock import MagicMock, patch

import requests

from bt_api import BTPanelAPI


class BTPanelAPITests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.api = BTPanelAPI("https://panel.example", "test-secret")

    def response(self, status=200, data=None, content=b"{}"):
        response = MagicMock(status_code=status, content=content)
        response.json.return_value = data if data is not None else {"status": True}
        response.__enter__.return_value = response
        return response

    def test_default_tls_parameters_unchanged_and_response_closed(self):
        response = self.response()
        params = {"path": "/tmp"}
        with patch("bt_api.requests.post", return_value=response) as post:
            self.assertEqual(self.api.request("/files?action=GetDir", params), {"status": True})
        self.assertEqual(params, {"path": "/tmp"})
        self.assertIs(post.call_args.kwargs["verify"], True)
        self.assertFalse(post.call_args.kwargs["allow_redirects"])
        self.assertEqual(post.call_args.kwargs["timeout"], 30)
        response.__exit__.assert_called_once()

    def test_custom_ca_from_constructor_and_environment(self):
        with patch.dict(os.environ, {"BT_CA_BUNDLE": "trusted-ca.pem"}):
            self.assertEqual(BTPanelAPI("https://panel.example", "key").verify, "trusted-ca.pem")
            self.assertEqual(BTPanelAPI("https://panel.example", "key", ca_bundle="explicit.pem").verify, "explicit.pem")

    def test_http_and_redirect_errors_do_not_return_raw_data(self):
        for status in (307, 308, 401, 500):
            with self.subTest(status=status):
                response = self.response(status=status, data={"secret": "test-secret"})
                with patch("bt_api.requests.post", return_value=response):
                    result = self.api.request("/system")
                self.assertFalse(result["status"])
                self.assertIn(str(status), result["msg"])
                self.assertNotIn("test-secret", str(result))
                response.json.assert_not_called()

    def test_invalid_json_and_empty_response(self):
        response = self.response()
        response.json.side_effect = ValueError("test-secret")
        with patch("bt_api.requests.post", return_value=response):
            self.assertIn("无效 JSON", self.api.request("/system")["msg"])
        with patch("bt_api.requests.post", return_value=self.response(content=b"")):
            self.assertEqual(self.api.request("/system")["error"], "empty_response")

    def test_network_errors_are_specific_and_redacted(self):
        for error, expected in ((requests.exceptions.SSLError, "证书"), (requests.exceptions.Timeout, "超时"), (requests.exceptions.ConnectionError, "ConnectionError")):
            with self.subTest(error=error), patch("bt_api.requests.post", side_effect=error("test-secret")):
                result = self.api.request("/system")
                self.assertFalse(result["status"])
                self.assertIn(expected, result["msg"])
                self.assertNotIn("test-secret", str(result))

    def test_session_requires_authorization_without_network(self):
        with patch("bt_api.requests.post") as post, self.assertLogs("bt_api", level="WARNING"):
            result = self.api.docker_request("container", "get_list")
        self.assertFalse(result["status"])
        self.assertIn("授权", result["msg"])
        post.assert_not_called()

    def test_crontab_requires_explicit_authorization(self):
        with patch.object(self.api, "exec_shell", return_value={"status": False, "error": "empty_response"}), patch.object(self.api, "request") as request:
            result = self.api.robust_exec_shell("echo test")
        self.assertIn("未授权", result["msg"])
        request.assert_not_called()

    def test_authorized_session_can_be_loaded(self):
        self.api.allow_session_access = True
        with patch.object(self.api, "get_file_content", side_effect=[{"status": True, "data": "sid"}, {"data": '{"x-http-token": "session-token"}'}]), patch.object(self.api, "request", return_value={"FILES": ["session;file;123"]}):
            self.assertTrue(self.api.refresh_x_token())
        self.assertEqual(self.api.x_http_token, "session-token")
        self.assertEqual(self.api._session_cookie, "sid")

    def test_authorized_crontab_fallback_uses_expected_lifecycle(self):
        self.api.allow_crontab_fallback = True
        with patch.object(self.api, "exec_shell", return_value={"status": False, "error": "empty_response"}), patch.object(self.api, "request", side_effect=[{"status": True, "id": 7}, {"status": True}, {"status": True, "msg": "=" * 42}, {"status": True}]) as request, patch("bt_api.time.sleep"):
            result = self.api.robust_exec_shell("echo test")
        self.assertTrue(result["status"])
        self.assertEqual([call.args[0] for call in request.call_args_list], ["/crontab?action=AddCrontab", "/crontab?action=StartTask", "/crontab?action=GetLogs", "/crontab?action=DelCrontab"])

    def test_malformed_session_logs_error_without_values(self):
        self.api.allow_session_access = True
        with patch.object(self.api, "get_file_content", return_value={}), patch.object(self.api, "request", return_value={"FILES": ["test-secret"]}), self.assertLogs("bt_api", level="WARNING") as logs:
            self.assertFalse(self.api.refresh_x_token())
        self.assertNotIn("test-secret", str(logs.output))


if __name__ == "__main__":
    unittest.main()
