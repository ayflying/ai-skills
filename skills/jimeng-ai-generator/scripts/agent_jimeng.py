import subprocess
import json
import time
import os
import urllib.request
import sys

# 配置
AGENT_BROWSER_PATH = "npx agent-browser"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 任务列表
TASKS = [
    {"id": "miku_test_v3", "prompt": "初音未来 Q版形象，手持大葱，甜美微笑，精细刻画，3D渲染风格, 极高画质"},
]

def run_cmd(cmd_list):
    node_path = "C:\\Program Files\\nodejs"
    cmd_str = f'"{AGENT_BROWSER_PATH}" ' + " ".join(cmd_list)
    full_cmd = f'set "PATH=%PATH%;{node_path}" && {cmd_str}'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, errors='ignore')
    return result.stdout

def automate_jimeng():
    print(">>> [启动即梦 AI 自动化 (agent-browser 版)]")
    
    # 1. 强制进入图片生成页面
    print(">>> 正在强制进入图片生成页面...")
    run_cmd(["open", "https://jimeng.jianying.com/ai-tool/image/generate"])
    time.sleep(5) # 等待页面完全加载
    
    # 尝试切换 4.0 模型
    run_cmd(["click", "--text", "4.0"])
    
    for task in TASKS:
        print(f"\n>>> [执行任务] ID: {task['id']}")
        
        # 2. 定位输入框：直接使用 JS 设置 value，这是最稳的，不受编号变化影响
        print(">>> 正在注入提示词...")
        set_val_js = f'const el = document.querySelector(\'[contenteditable="true"]\'); if(el) {{ el.innerText = "{task["prompt"]}"; el.dispatchEvent(new Event("input", {{ bubbles: true }})); }}'
        run_cmd(["eval", f'"{set_val_js}"'])
        time.sleep(1)
        
        # 3. 提交生成：查找带有 "生成" 字样的按钮或直接模拟 Enter
        print(">>> 提交生成...")
        # 方式A: 模拟 Enter
        run_cmd(["press", "Enter"])
        # 方式B: 寻找生成按钮点击 (即梦的生成按钮通常包含特定的 svg)
        click_btn_js = 'Array.from(document.querySelectorAll("button")).find(b => b.innerText.includes("生成") || b.querySelector("svg"))?.click()'
        run_cmd(["eval", f'"{click_btn_js}"'])
        
        # 4. 结果监控
        print(">>> 正在监控生成进度...")
        success = False
        for i in range(60):
            time.sleep(2)
            check = run_cmd(["snapshot", "-i"])
            if "再次生成" in check or "重新编辑" in check:
                print(">>> [任务完成] 生成结束！")
                success = True
                break
            # 每隔 10 秒截个图看看进度
            if i % 5 == 0:
                print(f">>> 进度检查 ({i*2}s)...")
        
        # 5. 下载
        if success:
            get_img_js = 'Array.from(document.querySelectorAll("img")).filter(img => img.src.includes("jianying") || img.src.includes("seaway")).pop()?.src'
            img_url = run_cmd(["eval", f'"{get_img_js}"']).strip()
            if img_url and img_url.startswith("http"):
                filename = f"{task['id']}.png"
                filepath = os.path.join(OUTPUT_DIR, filename)
                urllib.request.urlretrieve(img_url, filepath)
                print(f">>> [图片已下载] {filepath}")

    print("\n>>> 处理完毕。")

if __name__ == "__main__":
    automate_jimeng()
