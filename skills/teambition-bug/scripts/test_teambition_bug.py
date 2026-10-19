import unittest
import json
import tempfile
from unittest.mock import Mock, patch
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import teambition_bug


class TeambitionBugHelperTests(unittest.TestCase):
    def test_success_code_accepts_empty_error_code(self) -> None:
        self.assertTrue(teambition_bug.is_success_code(""))
        self.assertTrue(teambition_bug.is_success_code("  "))
        self.assertTrue(teambition_bug.is_success_code("0"))
        self.assertTrue(teambition_bug.is_success_code(200))

    def test_success_code_rejects_business_error_code(self) -> None:
        self.assertFalse(teambition_bug.is_success_code("10020"))

    def test_start_rejects_terminal_status(self) -> None:
        with self.assertRaisesRegex(teambition_bug.ApiError, "只能抢占到处理中状态"):
            teambition_bug.ensure_start_status_is_active({"id": "done", "name": "已完成"})

    def test_start_allows_active_status(self) -> None:
        teambition_bug.ensure_start_status_is_active({"id": "doing", "name": "修改中"})

    def test_finish_rejects_terminal_status(self) -> None:
        with self.assertRaisesRegex(teambition_bug.ApiError, "只能推进到待验收"):
            teambition_bug.ensure_finish_status_is_review({"id": "done", "name": "已完成"})

    def test_finish_allows_review_status(self) -> None:
        teambition_bug.ensure_finish_status_is_review({"id": "review", "name": "待验收"})

    def test_finish_requires_verification(self) -> None:
        with self.assertRaisesRegex(teambition_bug.ConfigError, "--verification"):
            teambition_bug.require_finish_verification("  ")

    def test_finish_accepts_verification(self) -> None:
        self.assertEqual(teambition_bug.require_finish_verification("远程容器验证通过"), "远程容器验证通过")

    def test_summarize_task_includes_status_name_and_panel_fields(self) -> None:
        task = {
            "id": "task1",
            "content": "测试任务",
            "tfsId": "review",
            "stageId": "stage-a",
            "sfcId": "sfc-b",
            "tasklistId": "list-c",
            "isDone": False,
            "customfields": [{"id": "cf1", "name": "类型", "value": "需求", "ignored": "x"}],
            "tagIds": ["tag1"],
        }

        summary = teambition_bug.summarize_task(task, [{"id": "review", "name": "待验收"}])

        self.assertEqual(summary["statusName"], "待验收")
        self.assertEqual(summary["panelFields"]["stageId"], "stage-a")
        self.assertEqual(summary["panelFields"]["sfcId"], "sfc-b")
        self.assertEqual(summary["panelFields"]["tasklistId"], "list-c")
        self.assertEqual(summary["panelFields"]["customfields"], [{"id": "cf1", "name": "类型", "value": "需求"}])

    def test_status_items_accepts_result_wrapper(self) -> None:
        statuses = {"result": [{"id": "todo", "name": "未完成"}, "bad"]}

        self.assertEqual(teambition_bug.status_items(statuses), [{"id": "todo", "name": "未完成"}])

    def test_parse_expected_custom_fields_requires_key_value(self) -> None:
        with self.assertRaisesRegex(teambition_bug.ConfigError, "字段=值"):
            teambition_bug.parse_expected_custom_fields(["类型"])

    def test_finish_parser_requires_verification(self) -> None:
        parser = teambition_bug.build_parser()

        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                parser.parse_args(["finish", "--task-id", "task1", "--yes"])

        args = parser.parse_args(["finish", "--task-id", "task1", "--verification", "构建通过", "--yes"])
        self.assertEqual(args.verification, "构建通过")

    def test_custom_field_lookup_and_value(self) -> None:
        task = {
            "customfields": [
                {"id": "cf1", "name": "类型", "displayValue": "Bug"},
                {"id": "cf2", "title": "优先级", "value": "高"},
            ]
        }

        field = teambition_bug.find_custom_field(task, "类型")

        self.assertIsNotNone(field)
        self.assertEqual(teambition_bug.custom_field_value(field), "Bug")
        self.assertEqual(teambition_bug.find_custom_field(task, "不存在"), None)

    def test_normalize_check_value_handles_structured_values(self) -> None:
        self.assertEqual(teambition_bug.normalize_check_value(["Bug"]), '["Bug"]')

    def test_comment_render_mode_uses_text_when_mentioning(self) -> None:
        self.assertEqual(teambition_bug.resolve_comment_render_mode(None, ["u1"]), "text")
        self.assertEqual(teambition_bug.resolve_comment_render_mode(None, None), "markdown")
        self.assertEqual(teambition_bug.resolve_comment_render_mode(None, []), "markdown")

    def test_comment_render_mode_lets_explicit_value_win(self) -> None:
        self.assertEqual(teambition_bug.resolve_comment_render_mode("markdown", ["u1"]), "markdown")

    def test_comment_parser_defaults_render_mode_to_auto(self) -> None:
        args = teambition_bug.build_parser().parse_args(
            ["comment", "--task-id", "t1", "--content", "正文", "--mention-user-id", "u1", "--yes"]
        )
        self.assertIsNone(args.render_mode)

    def test_quick_reply_and_ask_keep_render_mode_auto(self) -> None:
        parser = teambition_bug.build_parser()
        quick = parser.parse_args(["quick-reply", "--task-id", "t1", "--template", "fixed", "--yes"])
        ask = parser.parse_args(["ask", "--task-id", "t1", "--question", "怎么复现？", "--yes"])
        self.assertFalse(hasattr(quick, "render_mode") and quick.render_mode)
        self.assertFalse(hasattr(ask, "render_mode") and ask.render_mode)


class ActivityFileTests(unittest.TestCase):
    def activities(self, count=1):
        return [{"id": "reply1", "action": "comment", "content": json.dumps({"files": [f"{i:024x}" for i in range(count)]})}]

    def test_resolves_comment_file_scope_and_classifies_mime(self):
        client = Mock()
        rid = "task:t1/activity:reply1/file:" + "0" * 24
        client.request.return_value = [{"id": "0" * 24, "resourceId": rid, "fileName": "截图", "mimeType": "image/png", "downloadUrl": "https://files.example/blob", "fileToken": "secret"}]
        result = teambition_bug.resolve_activity_files(client, "t1", self.activities())
        client.request.assert_called_once_with("POST", "/v3/file/query/by-resource-ids", json_body={"resourceIds": [rid], "needSign": True})
        self.assertEqual(result["resources"]["images"], ["https://files.example/blob"])
        self.assertEqual(result["files"][0]["activityId"], "reply1")
        self.assertNotIn("fileToken", result["files"][0])

    def test_empty_malformed_and_duplicate_files(self):
        client = Mock()
        self.assertEqual(teambition_bug.resolve_activity_files(client, "t", [{"id": "a", "content": "bad"}])["files"], [])
        client.request.assert_not_called()
        activities = self.activities() * 2
        client.request.return_value = []
        result = teambition_bug.resolve_activity_files(client, "t", activities)
        self.assertEqual(len(result["errors"]), 1)
        client.request.assert_called_once()

    def test_batches_at_fifty_and_reports_errors(self):
        client = Mock()
        client.request.side_effect = teambition_bug.ApiError("HTTP 403")
        result = teambition_bug.resolve_activity_files(client, "t", {"result": self.activities(51)})
        self.assertEqual(client.request.call_count, 2)
        self.assertEqual(len(result["errors"]), 51)
        self.assertEqual(len(client.request.call_args_list[0].kwargs["json_body"]["resourceIds"]), 50)

    def test_non_image_attachment_is_not_an_image(self):
        client = Mock()
        rid = "task:t/activity:reply1/file:" + "0" * 24
        client.request.return_value = [{"resourceId": rid, "fileName": "数据.pdf", "mimeType": "application/pdf", "downloadUrl": "https://files.example/blob"}]
        result = teambition_bug.resolve_activity_files(client, "t", self.activities())
        self.assertEqual(result["resources"]["images"], [])
        self.assertEqual(result["resources"]["attachments"], ["https://files.example/blob"])

    def test_context_merges_reply_images_and_keeps_source(self):
        client = Mock()
        client.request.return_value = []
        attachment = {"files": [{"activityId": "a"}], "errors": [], "resources": {"images": ["https://example.test/s.png"], "attachments": [], "links": []}}
        with patch.object(teambition_bug, "get_task", return_value={"id": "t"}), patch.object(teambition_bug, "list_activities", return_value=[]), patch.object(teambition_bug, "render_task_rich_text", return_value={}), patch.object(teambition_bug, "resolve_activity_files", return_value=attachment):
            result = teambition_bug.build_task_context(client, "t")
        self.assertTrue(result["imageAnalysisRequired"])
        self.assertEqual(result["mediaResources"]["images"], ["https://example.test/s.png"])
        self.assertEqual(result["activityFiles"]["files"][0]["activityId"], "a")

    def test_download_includes_reply_image_without_authorization_headers(self):
        client = Mock()
        rid = "task:t/activity:reply1/file:" + "0" * 24
        client.request.side_effect = [[], [{"resourceId": rid, "mimeType": "image/png", "downloadUrl": "https://files.example/blob"}]]
        response = Mock(status_code=200, headers={"Content-Type": "image/png"})
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.iter_content.return_value = [b"png"]
        with tempfile.TemporaryDirectory() as folder, patch.object(teambition_bug, "TeambitionClient", return_value=client), patch.object(teambition_bug, "get_task", return_value={"id": "t"}), patch.object(teambition_bug, "list_activities", return_value=self.activities()), patch.object(teambition_bug.requests, "get", return_value=response) as download, patch.object(teambition_bug, "print_json") as output:
            args = teambition_bug.build_parser().parse_args(["download-images", "--task-id", "t", "--output-dir", folder])
            teambition_bug.cmd_download_images(args)
            download.assert_called_once_with("https://files.example/blob", timeout=(5, 30), stream=True)
            result = output.call_args.args[0]
            self.assertEqual(result["downloaded"][0]["bytes"], 3)
            self.assertTrue(Path(result["downloaded"][0]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
