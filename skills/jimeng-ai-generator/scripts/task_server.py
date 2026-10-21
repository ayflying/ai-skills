"""为即梦扩展提供仅限本机的任务分发和受限图片保存服务。"""

import http.client
import socketserver
from urllib.parse import parse_qs, urlparse

from local_support import InputError, LocalHandler, download_image, validate_task_id

PORT = 18542
VERSION = "1.17"
TASKS = [
    {"id": "hatsune_miku", "type": "image", "model": "4.0", "prompt": "初音未来 Q版卡通形象，葱绿色双马尾，蓝色大眼睛，粉色耳机，黑色露脐上衣，蓝色超短裙，白色过膝袜，黑色靴子，甜美微笑，站立姿势，卡通手办风格，精细刻画，清晰轮廓，动漫风格"},
]
IN_FLIGHT = {}


class AtomicTaskHandler(LocalHandler):
    def do_GET(self) -> None:
        if not self.require_trusted():
            return
        parsed = urlparse(self.path)
        if parsed.path != "/get_task":
            self.send_json(404, {"success": False, "error": "接口不存在"})
            return
        if parse_qs(parsed.query).get("v", [None])[0] != VERSION:
            self.send_json(409, {"success": False, "error": "v_err"})
            return
        if TASKS:
            task = TASKS.pop(0)
            IN_FLIGHT[task["id"]] = {"task": task, "saved": False, "status": "running"}
            self.send_json(200, task)
        else:
            self.send_json(200, {})

    def do_POST(self) -> None:
        if not self.require_trusted():
            return
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/save_image":
                data = self.read_json()
                task_id = validate_task_id(data.get("taskId"))
                state = IN_FLIGHT.get(task_id)
                if not state or state["status"] != "running":
                    raise InputError("任务未认领或已经结束")
                path = download_image(data.get("url"), task_id)
                state["saved"] = True
                self.send_json(200, {"success": True, "path": str(path)})
            elif parsed.path == "/finish_task":
                query = parse_qs(parsed.query)
                task_id = validate_task_id(query.get("id", [None])[0])
                status = query.get("status", [None])[0]
                state = IN_FLIGHT.get(task_id)
                if not state or state["status"] != "running":
                    raise InputError("任务未认领或已经结束")
                if status not in {"done", "failed"}:
                    raise InputError("任务状态无效")
                if status == "done" and not state["saved"]:
                    raise InputError("图片未保存，不能标记完成")
                state["status"] = status
                self.send_json(200, {"success": True, "status": status})
                print(f"任务 {task_id}：{'完成' if status == 'done' else '失败，未自动重试'}")
                del IN_FLIGHT[task_id]
            else:
                self.send_json(404, {"success": False, "error": "接口不存在"})
        except (InputError, ValueError) as exc:
            self.close_connection = True
            self.send_json(400, {"success": False, "error": str(exc)})
        except (OSError, http.client.HTTPException):
            self.close_connection = True
            self.send_json(502, {"success": False, "error": "图片下载失败或超时"})


def run_server() -> None:
    print(f"即梦任务服务 v{VERSION}：仅监听 http://127.0.0.1:{PORT}")
    with socketserver.TCPServer(("127.0.0.1", PORT), AtomicTaskHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
