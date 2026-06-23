import os, json, urllib.request, subprocess

def get_env(name):
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[Environment]::GetEnvironmentVariable('{name}','User')"],
        capture_output=True, text=True)
    return out.stdout.strip()

key = get_env("GPT_IMAGE_API_KEY")
base = get_env("GPT_IMAGE_BASE_URL").rstrip("/")
req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer " + key})
try:
    data = json.load(urllib.request.urlopen(req, timeout=30))
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
    print("ERR", e)
