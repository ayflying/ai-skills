import asyncio
from playwright.async_api import async_playwright
import os
import re
import shutil
from datetime import datetime
from PIL import Image

OUTPUT_DIR = "D:/git/ai-skills/skills/jimeng-ai-generator/outputs"
BROWSER_PROFILE = "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BROWSER_PROFILE, exist_ok=True)


async def download_jimeng_images(prompt=None, max_images=20):
    print("=" * 50)
    print("即梦AI图片下载工具 v4.0 (VIP)")
    print("=" * 50)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_DIR, f"download_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    async with async_playwright() as p:
        print("\n[1/5] 启动浏览器...")
        browser = await p.chromium.launch(headless=False)

        storage_state = os.path.join(BROWSER_PROFILE, "storageState.json")
        context = await browser.new_context(
            storage_state=storage_state if os.path.exists(storage_state) else None,
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        image_urls = []

        def handle_response(response):
            url = response.url
            if "dreamina-sign" in url and (".webp" in url or ".png" in url):
                image_urls.append(url)

        page.on("response", handle_response)

        print("[2/5] 访问即梦AI...")
        await page.goto("https://jimeng.jianying.com/ai-tool/generate/?type=image")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # 检查登录
        if await page.query_selector('button:has-text("登录")'):
            print("\n需要登录！请运行 python browser_server.py 先登录")
            return session_dir

        # 填入提示词并生成
        if prompt:
            print(f"\n[3/5] 填入提示词: {prompt[:30]}...")
            input_box = await page.query_selector(
                'input[placeholder*="描述"], input[type="text"]'
            )
            if input_box:
                await input_box.fill(prompt)
                await page.wait_for_timeout(500)
                gen_btn = await page.query_selector('button:has-text("生成")')
                if gen_btn:
                    await gen_btn.click()
                    print("已触发生成，等待...")
                    await page.wait_for_timeout(10000)

        print("[3/5] 查找生成结果...")
        images = await page.query_selector_all("img")
        target_images = [
            img
            for img in images
            if "dreamina-sign" in (await img.get_attribute("src") or "")
            and "resize_loss" in (await img.get_attribute("src") or "")
        ]
        print(f"找到 {len(target_images)} 张图片")

        if target_images:
            print("[4/5] 点击触发动态加载...")
            try:
                await target_images[0].click(timeout=3000)
                await page.wait_for_timeout(2000)
            except:
                pass

            # 点击原图按钮
            buttons = await page.query_selector_all("button")
            for btn in buttons:
                text = await btn.inner_text()
                if text and "原图" in text:
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    break

        print(f"[5/5] 下载图片...")

        unique_urls = list(set(image_urls))

        # 按尺寸排序（优先大图去重）
        def get_size_key(url):
            m = re.search(r"resize[_\w]*:(\d+):(\d+)", url)
            return int(m.group(1)) * int(m.group(2)) if m else 0

        unique_urls.sort(key=get_size_key, reverse=True)

        downloaded = 0
        for i, url in enumerate(unique_urls[:max_images]):
            try:
                ext = ".webp"
                if ".png" in url:
                    ext = ".png"
                m = re.search(r"resize[_\w]*:(\d+):(\d+)", url)
                size_str = f"_{m.group(1)}x{m.group(2)}" if m else ""

                filename = f"jimeng_{i + 1:02d}{size_str}{ext}"
                filepath = os.path.join(session_dir, filename)

                resp = await page.request.get(url)
                if resp.status == 200:
                    body = await resp.body()
                    if len(body) > 1024:
                        with open(filepath, "wb") as f:
                            f.write(body)
                        size_kb = len(body) / 1024
                        print(f"  OK {filename} ({size_kb:.1f} KB)")
                        downloaded += 1
            except Exception as e:
                print(f"  FAIL: {e}")

        await context.storage_state(path=storage_state)

        print(f"\n完成！共下载 {downloaded} 张图片")
        print(f"保存位置: {session_dir}")
        await browser.close()
        return session_dir


if __name__ == "__main__":
    import sys

    prompt = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(download_jimeng_images(prompt))
