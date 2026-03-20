import asyncio
from playwright.async_api import async_playwright
import os
import re
import time
import random
from datetime import datetime

OUTPUT_DIR = "D:/git/ai-skills/skills/jimeng-ai-generator/outputs"
BROWSER_PROFILE = "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile"
STORAGE_STATE = os.path.join(BROWSER_PROFILE, "jimeng_vip.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def generate_and_download_4(prompt=None):
    """
    1. 生成
    2. 下载 4 张 1080P
    3. 返回文件列表
    """
    print("=" * 60)
    print(f"即梦AI 4图下载器 (VIP 1080P)")
    print(f"提示词: {prompt}")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_DIR, f"eval_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    paths = []

    async with async_playwright() as p:
        print("\n[1/5] 启动浏览器...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state=STORAGE_STATE if os.path.exists(STORAGE_STATE) else None,
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        print("[2/5] 访问即梦AI并生成...")
        await page.goto("https://jimeng.jianying.com/ai-tool/generate/?type=image")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

        if prompt:
            input_box = await page.query_selector(
                'input[placeholder*="描述"], textarea'
            )
            if input_box:
                await input_box.fill(prompt)
                await page.wait_for_timeout(500)
                gen_btn = await page.query_selector('button:has-text("生成")')
                if gen_btn:
                    await gen_btn.click()
                    print("  已点击生成，等待 70 秒...")
                    await page.wait_for_timeout(70000)

        # 刷新结果
        await page.reload()
        await page.wait_for_timeout(5000)

        print("[3/5] 定位生成的 4 张图...")
        imgs = await page.query_selector_all("img")
        targets = []
        for img in imgs:
            src = await img.get_attribute("src")
            if src and "dreamina-sign" in src and ("480" in src or "360" in src):
                targets.append(img)
            if len(targets) == 4:
                break

        if not targets:
            print("  未找到生成的图片！")
            await browser.close()
            return []

        print(f"  找到 {len(targets)} 张图片，开始下载 1080P...")

        for i, img in enumerate(targets):
            try:
                print(f"  正在获取第 {i + 1} 张高清原图...")
                await img.click()
                await page.wait_for_timeout(3000)

                url = await page.evaluate("""() => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    const hr = imgs.find(i => i.src.includes('dreamina') && (i.src.includes('1080') || i.src.includes('720')));
                    return hr ? hr.src : null;
                }""")

                if url:
                    fpath = os.path.join(session_dir, f"img_{i + 1}.webp")
                    resp = await page.request.get(url)
                    if resp.status == 200:
                        body = await resp.body()
                        with open(fpath, "wb") as f:
                            f.write(body)
                        paths.append(fpath)
                        print(f"    OK: img_{i + 1}.webp ({len(body) / 1024:.1f} KB)")

                await page.keyboard.press("Escape")
                await page.wait_for_timeout(1000)
            except Exception as e:
                print(f"    ERROR: 第 {i + 1} 张处理失败: {e}")

        await context.storage_state(path=STORAGE_STATE)
        await browser.close()

    return paths, session_dir


if __name__ == "__main__":
    import sys

    prompt = sys.argv[1] if len(sys.argv) > 1 else "一只赛博朋克风格的未来城市"
    paths, sdir = asyncio.run(generate_and_download_4(prompt))
    print(f"\n下载完成，文件保存在: {sdir}")
    print(f"共下载: {len(paths)} 张高清图片")
