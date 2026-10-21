"""通过 agent-browser 执行本机排队任务；不经过 Shell 拼接用户输入。"""

import http.client
import json
import socketserver
import subprocess
import threading
import time

from local_support import (
    BROWSER_PROFILE, OUTPUT_DIR, InputError, LocalHandler,
    download_image, run_browser_command, validate_task,
)

PORT = 18542
TASKS = []
TASKS_LOCK = threading.Lock()


def run_agent_cmd(cmd_list: list[str]) -> str:
    return run_browser_command([
        "--headed", "--profile", str(BROWSER_PROFILE),
        "--download-path", str(OUTPUT_DIR), *cmd_list,
    ])


def prompt_script(prompt: str) -> str:
    """提示词作为 JSON 字符串值注入，不拼成可执行代码。"""
    return (
        'const el = document.querySelector(\'[contenteditable="true"]\');'
        'if (!el) throw new Error("找不到提示词输入框");'
        f'el.innerText = {json.dumps(prompt, ensure_ascii=True)};'
        'el.dispatchEvent(new Event("input", {bubbles:true}));'
    )


def process_task(task: dict) -> None:
    run_agent_cmd(["open", "https://jimeng.jianying.com/ai-tool/image/generate"])
    time.sleep(2)
    # 记录提交前的图片，不能把上一轮结果误报为本轮成功。
    image_script = 'JSON.stringify(Array.from(document.images).map(img => img.src))'
    previous = json.loads(run_agent_cmd(["eval", image_script]).strip())
    run_agent_cmd(["eval", prompt_script(task["prompt"])])
    time.sleep(1)
    run_agent_cmd(["press", "Enter"])
    click_script = 'Array.from(document.querySelectorAll("button")).find(b => b.innerText.includes("生成"))?.click()'
    run_agent_cmd(["eval", click_script])
    for _ in range(60):
        time.sleep(2)
        urls = json.loads(run_agent_cmd(["eval", image_script]).strip())
        candidates = [url for url in urls if url not in previous and url.startswith("https://")]
        if candidates:
            path = download_image(candidates[-1], task["id"])
            print(f"任务 {task['id']} 图片已保存：{path.name}")
            return
    raise TimeoutError("未检测到本轮新增图片，任务未完成")


def process_tasks() -> None:
    while True:
        with TASKS_LOCK:
            task = TASKS.pop(0) if TASKS else None
        if task:
            try:
                process_task(task)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, http.client.HTTPException):
                # 不输出可能含提示词、签名地址或完整命令的异常详情。
                print(f"任务 {task['id']} 失败；未标记成功，未自动重试")
        time.sleep(3)


class TaskServerHandler(LocalHandler):
    def do_POST(self) -> None:
        if not self.require_trusted():
            return
        if self.path != "/add_task":
            self.send_json(404, {"success": False, "error": "接口不存在"})
            return
        try:
            task = validate_task(self.read_json())
            with TASKS_LOCK:
                if len(TASKS) >= 100:
                    raise InputError("任务队列已满")
                if any(item["id"] == task["id"] for item in TASKS):
                    raise InputError("任务 ID 已在队列中")
                TASKS.append(task)
            self.send_json(200, {"success": True, "status": "ok", "id": task["id"]})
        except (InputError, ValueError) as exc:
            self.close_connection = True
            self.send_json(400, {"success": False, "error": str(exc)})


def run_server() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    BROWSER_PROFILE.mkdir(parents=True, exist_ok=True)
    with socketserver.TCPServer(("127.0.0.1", PORT), TaskServerHandler) as httpd:
        threading.Thread(target=process_tasks, daemon=True).start()
        print(f"即梦代理服务：仅监听 http://127.0.0.1:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
