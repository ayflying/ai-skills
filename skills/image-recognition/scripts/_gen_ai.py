import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

def get_env(name):
    if os.environ.get(name):
        return os.environ[name]
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"[Environment]::GetEnvironmentVariable('{name}','User')"],
        capture_output=True, text=True, timeout=10, check=True)
    return out.stdout.strip()

OUT = os.path.join(os.path.dirname(__file__), "_bench_ai.png")

PROMPT_CN = (
    "生成一张信息密集的中文企业数据仪表盘信息图(竖版海报)。要求包含且文字清晰可读:\n"
    "1) 顶部深蓝标题栏:环球物流 2026 年度运营简报 GLOBAL LOGISTICS;\n"
    "2) 四张不同颜色KPI卡片(蓝/绿/橙/红),分别写:订单 1842、营收 ¥5.7M、延误 37、退货 12%;\n"
    "3) 一个柱状图(标题 本周运单量),5根柱;\n"
    "4) 一个饼图(运输方式占比:海运50% 空运30% 陆运20%);\n"
    "5) 一个折线图显示满意度趋势;\n"
    "6) 一张多行多列数据表格(列:区域/订单/准时率/状态,4行:华东/华南/华北/西部);\n"
    "7) 底部红色警示文字:西部区域准时率跌破80%,需在6月30日前整改;\n"
    "8) 右下角灰色水印:INTERNAL USE ONLY。\n"
    "整体专业精致,配色丰富,中文与数字必须清晰准确。"
)

def try_gpt_image(retries=6):
    key = get_env("GPT_IMAGE_API_KEY")
    base = get_env("GPT_IMAGE_BASE_URL").rstrip("/")
    if not key or not base:
        raise ValueError("缺少 GPT_IMAGE_API_KEY 或 GPT_IMAGE_BASE_URL 配置")
    url = base + "/images/generations"
    for i in range(retries):
        body = json.dumps({
            "model": "gpt-image-2",
            "prompt": PROMPT_CN,
            "size": "1024x1536",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                data = json.load(response)
            b64 = data["data"][0].get("b64_json")
            if b64:
                with open(OUT, "wb") as f:
                    f.write(base64.b64decode(b64))
                print("OK gpt-image-2 ->", OUT)
                return True
            url2 = data["data"][0].get("url")
            if url2:
                with urllib.request.urlopen(url2, timeout=180) as response:
                    with open(OUT, "wb") as f:
                        f.write(response.read())
                print("OK gpt-image-2(url) ->", OUT)
                return True
        except urllib.error.HTTPError as e:
            print(f"图片生成第 {i + 1} 次请求失败，HTTP {e.code}")
            e.close()
            if e.code == 429:
                time.sleep(8 * (i + 1))
                continue
            return False
        except Exception as e:
            print("图片生成失败，请检查配置、网络或响应格式。")
            time.sleep(5)
    return False

if __name__ == "__main__":
    if "--confirm-paid" not in sys.argv:
        raise SystemExit("本工具会调用图片生成接口并可能计费，确认后请添加 --confirm-paid。")
    raise SystemExit(0 if try_gpt_image() else 1)
