import json
import os
import subprocess
import urllib.request

def get_env(name):
    if os.environ.get(name):
        return os.environ[name]
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[Environment]::GetEnvironmentVariable('{name}','User')"],
        capture_output=True, text=True, timeout=10, check=True)
    return out.stdout.strip()


def main() -> None:
    """显式查询模型列表，不在导入时读取本机配置。"""
    key = get_env("GPT_IMAGE_API_KEY")
    base = get_env("GPT_IMAGE_BASE_URL").rstrip("/")
    req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.load(response)
        ids = sorted(m.get("id", "") for m in data.get("data", []))
        img = [i for i in ids if any(k in i.lower() for k in ["image", "imagen", "flux", "seedream", "dall", "draw", "sd", "diffus"])]
        print("== 全部模型 ==")
        for i in ids:
            print(i)
        print("== 可能的图像模型 ==")
        for i in img:
            print(i)
        print("== 全部模型数 ==", len(ids))
    except Exception as e:
        raise SystemExit("模型列表查询失败，请检查配置和服务连接。") from None


if __name__ == "__main__":
    main()
