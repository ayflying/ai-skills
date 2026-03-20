import http.server
import socketserver
import json
import time
import os
import urllib.request
import subprocess
import threading

# 配置
PORT = 18542
AGENT_BROWSER_PATH = 'npx agent-browser --headed --profile "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile" --download-path "D:/git/ai-skills/skills/jimeng-ai-generator/outputs"'
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 任务队列
TASKS = []
TASKS_LOCK = threading.Lock()


def run_agent_cmd(cmd_list):
    node_path = "C:\\Program Files\\nodejs"
    cmd_str = f'"{AGENT_BROWSER_PATH}" ' + " ".join(cmd_list)
    full_cmd = f'set "PATH=%PATH%;{node_path}" && {cmd_str}'
    result = subprocess.run(
        full_cmd, shell=True, capture_output=True, text=True, errors="ignore"
    )
    return result.stdout


def process_tasks():
    print(">>> [任务处理器已启动]")
    while True:
        task = None
        with TASKS_LOCK:
            if TASKS:
                task = TASKS.pop(0)

        if task:
            try:
                print(f"\n>>> [执行任务] ID: {task['id']} | 提示词: {task['prompt']}")

                # 1. 确保在生成页面
                run_agent_cmd(
                    ["open", "https://jimeng.jianying.com/ai-tool/image/generate"]
                )
                time.sleep(2)

                # 2. 注入提示词 (使用 JS 注入最稳)
                set_val_js = f'const el = document.querySelector(\'[contenteditable="true"]\'); if(el) {{ el.innerText = "{task["prompt"]}"; el.dispatchEvent(new Event("input", {{ bubbles: true }})); }}'
                run_agent_cmd(["eval", f'"{set_val_js}"'])
                time.sleep(1)

                # 3. 提交生成
                run_agent_cmd(["press", "Enter"])
                click_btn_js = 'Array.from(document.querySelectorAll("button")).find(b => b.innerText.includes("生成") || b.querySelector("svg"))?.click()'
                run_agent_cmd(["eval", f'"{click_btn_js}"'])

                # 4. 监控进度 (最多等 120s)
                success = False
                for i in range(60):
                    time.sleep(2)
                    check = run_agent_cmd(["snapshot", "-i"])
                    if "再次生成" in check or "重新编辑" in check:
                        print(f">>> [任务完成] ID: {task['id']}")
                        success = True
                        break

                # 5. 下载结果
                if success:
                    get_img_js = 'Array.from(document.querySelectorAll("img")).filter(img => img.src.includes("jianying") || img.src.includes("seaway")).pop()?.src'
                    img_url = run_agent_cmd(["eval", f'"{get_img_js}"']).strip()
                    if img_url and img_url.startswith("http"):
                        filename = f"{task['id']}.png"
                        filepath = os.path.join(OUTPUT_DIR, filename)
                        urllib.request.urlretrieve(img_url, filepath)
                        print(f">>> [下载成功] {filepath}")
            except Exception as e:
                print(f"!!! [执行出错] {e}")

        time.sleep(3)  # 轮询间隔


class TaskServerHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/add_task":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                task_id = data.get("id", f"task_{int(time.time())}")
                prompt = data.get("prompt", "")

                if prompt:
                    with TASKS_LOCK:
                        TASKS.append({"id": task_id, "prompt": prompt})
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(
                        json.dumps({"status": "ok", "id": task_id}).encode()
                    )
                    print(f"\n<<< [收到新任务] {task_id}")
                else:
                    self.send_response(400)
                    self.end_headers()
            except:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    # 启动后台任务处理器
    threading.Thread(target=process_tasks, daemon=True).start()

    print(f"\n[即梦AI服务器启动] 监听端口: {PORT}")
    with socketserver.TCPServer(("", PORT), TaskServerHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
