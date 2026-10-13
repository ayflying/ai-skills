import unittest
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


if __name__ == "__main__":
    unittest.main()
