#!/usr/bin/env python3
"""
即梦AI自动生成工具 - agent-browser版本
使用 agent-browser CLI 进行稳定的浏览器自动化
"""

import subprocess
import os
import sys
import time
import random
import json

# 配置
BROWSER_PROFILE = "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile"
OUTPUT_DIR = "D:/git/ai-skills/skills/jimeng-ai-generator/outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 随机提示词池
RANDOM_PROMPTS = [
    "一只可爱的橘猫在阳光下打盹",
    "未来城市的霓虹夜景赛博朋克风格",
    "一幅抽象派油画色彩斑斓的风景",
    "一只是着墨镜的酷狗在海边冲浪",
    "中国古典园林亭台楼阁春暖花开",
    "梦幻星空下的独角兽城堡",
    "机械风格的未来机器人武士",
    "日式樱花树下的小木屋",
    "一只穿西装的卡通仓鼠商务精英",
    "海底世界的美人鱼公主",
    "秋日金黄的银杏叶森林小路",
    "可爱的大熊猫宝宝抱着竹子卖萌",
    "欧洲中世纪城堡与巨龙战斗",
    "热带雨林瀑布彩虹鸟语花香",
    "未来科幻太空站探索宇宙",
]


def run(cmd_list, timeout=30):
    """执行agent-browser命令"""
    cmd_str = "agent-browser " + " ".join(cmd_list)
    try:
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(BROWSER_PROFILE),
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return ""
    except Exception as e:
        print(f"命令执行失败: {e}")
        return ""


def wait(seconds=3):
    """等待"""
    time.sleep(seconds)


def auto_generate(prompt=None, model="4.1", wait_seconds=60):
    """自动生成图片"""
    print("=" * 60)
    print("即梦AI自动生成工具 (agent-browser)")
    print("=" * 60)

    # 使用已保存的登录状态
    state_file = os.path.join(BROWSER_PROFILE, "jimeng_vip.json")

    # 1. 打开浏览器并加载状态
    print("\n[1/7] 打开浏览器...")
    if os.path.exists(state_file):
        run(["--session-name", "jimeng-auto", "state", "load", state_file])
    run(
        [
            "--session-name",
            "jimeng-auto",
            "--headed",
            "open",
            "https://jimeng.jianying.com/ai-tool/home",
        ]
    )
    wait(3)

    # 2. 进入图片生成页面
    print("[2/7] 进入图片生成页面...")
    # 使用JS点击"图片生成"
    run(["eval", "--stdin"], timeout=10)

    js_code = """
const links = Array.from(document.querySelectorAll('a, button, [role="menuitem"]'));
const link = links.find(el => el.innerText.includes('图片生成'));
if (link) { link.click(); 'Clicked: ' + link.innerText; }
"""
    run(
        ["eval", "--stdin", "--", js_code.replace("\n", " ").replace("  ", "")],
        timeout=10,
    )
    wait(5)

    # 3. 获取页面快照确认加载完成
    print("[3/7] 确认页面加载...")
    snapshot = run(["--session-name", "jimeng-auto", "snapshot", "-i"])
    if "上传参考图" not in snapshot and "描述你想" not in snapshot:
        print("  等待输入框出现...")
        wait(5)
        snapshot = run(["--session-name", "jimeng-auto", "snapshot", "-i"])

    # 4. 填入提示词
    if not prompt:
        prompt = random.choice(RANDOM_PROMPTS)
    print(f"[4/7] 填入提示词: {prompt}")

    # 查找输入框
    run(["--session-name", "jimeng-auto", "fill", "@e18", prompt])
    wait(2)

    # 5. 点击生成
    print("[5/7] 触发生成...")
    run(["--session-name", "jimeng-auto", "click", "@e16"])

    # 6. 等待生成完成
    print(f"[6/7] 等待生成完成 ({wait_seconds}秒)...")
    for i in range(wait_seconds // 10):
        wait(10)
        snapshot = run(["--session-name", "jimeng-auto", "snapshot", "-i"])
        if "再次生成" in snapshot or "重新编辑" in snapshot:
            print("  检测到生成完成!")
            break
        print(f"  已等待 {(i + 1) * 10} 秒...")

    # 7. 获取图片URL并下载
    print("[7/7] 下载图片...")

    # 使用JS获取所有dreamina图片URL
    get_urls_js = """
const images = Array.from(document.querySelectorAll('img'));
const dreaminaImages = images.filter(img => img.src && img.src.includes('dreamina'));
JSON.stringify(dreaminaImages.map(img => img.src).slice(0, 10));
"""

    # 保存URLs
    urls_file = os.path.join(OUTPUT_DIR, "last_urls.txt")
    run(
        [
            "--session-name",
            "jimeng-auto",
            "eval",
            "--stdin",
            get_urls_js.replace("\n", " "),
        ]
    )
    wait(2)

    # 截图保存
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot = os.path.join(OUTPUT_DIR, f"result_{timestamp}.png")
    run(
        [
            "--session-name",
            "jimeng-auto",
            "screenshot",
            "--full",
            "--screenshot-dir",
            OUTPUT_DIR,
        ]
    )

    # 保存状态
    run(["--session-name", "jimeng-auto", "state", "save", state_file])

    print(f"\n完成! 截图已保存到: {OUTPUT_DIR}")
    print("请查看 last_urls.txt 获取图片URL列表")
    return True


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    model = sys.argv[2] if len(sys.argv) > 2 else "4.1"
    wait_sec = int(sys.argv[3]) if len(sys.argv) > 3 else 60

    auto_generate(prompt, model, wait_sec)
