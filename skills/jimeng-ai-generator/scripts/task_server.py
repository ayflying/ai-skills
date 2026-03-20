import http.server
import socketserver
import json
import time
import os
import urllib.request
from urllib.parse import urlparse, parse_qs

PORT = 18542
VERSION = "1.16"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 任务队列
TASKS = [
    {"id": "hatsune_miku", "type": "image", "model": "4.0", "prompt": "初音未来 Q版卡通形象，葱绿色双马尾，蓝色大眼睛，粉色耳机，黑色露脐上衣，蓝色超短裙，白色过膝袜，黑色靴子，甜美微笑，站立姿势，卡通手办风格，精细刻画，清晰轮廓，动漫风格"},
]

class AtomicTaskHandler(http.server.BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200); self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        client_v = query.get('v', [None])[0]

        if parsed.path == '/get_task':
            self.send_response(200); self.end_headers()
            if client_v != VERSION:
                self.wfile.write(json.dumps({"error": "v_err"}).encode())
                return

            global TASKS
            # 原子发放：只要有人领，立刻弹出队列，绝不给第二次机会
            if TASKS:
                task = TASKS.pop(0)
                self.wfile.write(json.dumps(task).encode())
                print(f"\n>>> [唯一派发] ID: {task['id']} | 内容: {task['prompt']}")
            else:
                self.wfile.write(json.dumps({}).encode())

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        if self.path.startswith('/finish_task'):
            query = parse_qs(urlparse(self.path).query)
            tid = query.get('id', [None])[0]
            self.send_response(200); self.end_headers()
            print(f"\n<<< [任务成功] ID: {tid} 已完美闭环。")
        
        elif self.path.startswith('/save_image'):
            try:
                data = json.loads(body)
                task_id = data.get('taskId', 'unknown')
                img_url = data.get('url', '')
                
                if img_url:
                    # 下载图片
                    filename = f"{task_id}_{int(time.time())}.png"
                    filepath = os.path.join(OUTPUT_DIR, filename)
                    urllib.request.urlretrieve(img_url, filepath)
                    print(f"\n>>> [图片已保存] {filepath}")
                    self.wfile.write(json.dumps({"success": True, "path": filepath}).encode())
                else:
                    self.wfile.write(json.dumps({"success": False, "error": "no url"}).encode())
            except Exception as e:
                print(f">>> [保存图片失败] {e}")
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())
            self.send_response(200); self.end_headers()

def run_server():
    print(f"\n[即梦AI指挥部 v{VERSION}] 跨标签锁定模式启动")
    print(f"请手动刷新页面，监控萨摩耶任务...")
    with socketserver.TCPServer(("", PORT), AtomicTaskHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()
