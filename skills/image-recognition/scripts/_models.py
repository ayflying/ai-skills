import json
import os
import urllib.request


def main() -> None:
    """显式查询模型列表，不在导入时请求服务。"""
    base = os.environ["IR_BASE"].rstrip("/")
    key = os.environ["IR_KEY"]
    req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer " + key})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.load(response)
    ids = sorted(m.get("id", "") for m in data.get("data", []))
    print("total", len(ids))
    for i in ids:
        print(i)


if __name__ == "__main__":
    main()
