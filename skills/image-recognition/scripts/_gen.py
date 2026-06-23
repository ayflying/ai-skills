import os
import subprocess
import sys

base = os.environ.get("IR_BASE") or ""
key = os.environ.get("IR_KEY") or ""

env = dict(os.environ)
env["GPT_IMAGE_API_KEY"] = key
env["GPT_IMAGE_BASE_URL"] = base
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

prompt = (
    "A dense, busy infographic dashboard poster, top-down flat design, lots of "
    "small distinct elements to test machine reading: a bold title bar reading "
    "'GLOBAL LOGISTICS 2026', four colored KPI cards (blue 'ORDERS 1842', green "
    "'REVENUE $5.7M', orange 'DELAYS 37', red 'RETURNS 12%'), a bar chart with five "
    "bars labeled Mon Tue Wed Thu Fri of heights 40 65 30 80 55, a small pie chart "
    "split into three slices 50% 30% 20%, a world map with 6 location pins, a "
    "checklist with three checked boxes and two empty boxes, a circular gauge "
    "pointing to 72, several flat icons: a truck, an airplane, a ship, a warehouse, "
    "a clock showing 3:45, and a small calendar showing the number 26. Use a clean "
    "white background, crisp readable labels, professional corporate style."
)

cmd = [
    sys.executable,
    "skills/gpt-image/scripts/gpt_image.py",
    "generate",
    prompt,
    "--model", os.environ.get("IR_IMG_MODEL", "gpt-image-2"),
    "--size", "1024x1024",
    "-o", "skills/image-recognition/scripts/_bench_complex.png",
]
print("running:", " ".join(cmd[:5]), "...")
import time
for attempt in range(1, 9):
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, encoding="utf-8")
    print(f"[attempt {attempt}] RC", r.returncode)
    if r.returncode == 0:
        print("OK", r.stdout)
        break
    err = (r.stderr or "") + (r.stdout or "")
    print("ERR", err.strip()[:200])
    if "429" in err or "rate limit" in err.lower():
        wait = min(20 + attempt * 15, 90)
        print(f"  rate limited, sleep {wait}s")
        time.sleep(wait)
        continue
    break
