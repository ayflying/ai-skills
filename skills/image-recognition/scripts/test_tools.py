"""评测工具的离线入口与导入安全回归。"""

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parent


class ToolImportTests(unittest.TestCase):
    def test_import_does_not_request_generate_or_write(self) -> None:
        for filename in ("_gen.py", "_gen_ai.py", "_models.py", "_listmodels.py", "_draw_bench.py"):
            with self.subTest(filename=filename):
                spec = importlib.util.spec_from_file_location("bench_tool", SCRIPTS / filename)
                module = importlib.util.module_from_spec(spec)
                with patch("subprocess.run", side_effect=AssertionError("导入不应创建进程")), patch(
                    "urllib.request.urlopen", side_effect=AssertionError("导入不应请求网络")
                ), patch("PIL.Image.new", side_effect=AssertionError("导入不应生成图片")):
                    spec.loader.exec_module(module)

    def test_paid_tools_require_explicit_confirmation(self) -> None:
        for filename in ("_gen.py", "_gen_ai.py"):
            with self.subTest(filename=filename):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / filename)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=10,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("--confirm-paid", result.stderr)


if __name__ == "__main__":
    unittest.main()
