import asyncio
from playwright.async_api import async_playwright
import os
import re
import sys
import shutil
from datetime import datetime

OUTPUT_DIR = "D:/git/ai-skills/skills/jimeng-ai-generator/outputs"
BROWSER_PROFILE = "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile"
STORAGE_STATE = os.path.join(BROWSER_PROFILE, "jimeng_vip.json")


async def run_flow(prompt):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_DIR, f"result_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state=STORAGE_STATE if os.path.exists(STORAGE_STATE) else None,
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        print(f">>> 正在生成: {prompt}")
        await page.goto("https://jimeng.jianying.com/ai-tool/generate/?type=image")
        await page.wait_for_load_state("networkidle")

        # 填入提示词
        input_box = await page.query_selector('input[placeholder*="描述"], textarea')
        if input_box:
            await input_box.fill(prompt)
            await page.keyboard.press("Enter")
            print(">>> 已触发生成，等待 70 秒...")
            await page.wait_for_timeout(70000)

        # 刷新页面并下载
        await page.reload()
        await page.wait_for_timeout(5000)

        imgs = await page.query_selector_all("img")
        targets = [
            img
            for img in imgs
            if "dreamina-sign" in (await img.get_attribute("src") or "")
        ][:4]

        print(f">>> 找到 {len(targets)} 张图片，开始下载 1080P 高清原图...")
        for i, img in enumerate(targets):
            await img.click()
            await page.wait_for_timeout(3000)
            url = await page.evaluate("""() => {
                const i = Array.from(document.querySelectorAll('img')).find(x => x.src.includes('dreamina') && x.src.includes('1080'));
                return i ? i.src : null;
            }""")
            if url:
                resp = await page.request.get(url)
                with open(os.path.join(session_dir, f"img_{i + 1}.webp"), "wb") as f:
                    f.write(await resp.body())
                print(f"  ✓ 已下载 img_{i + 1}.webp")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(1000)

        await context.storage_state(path=STORAGE_STATE)
        await browser.close()

    print(f"\n>>> 任务完成！4张原图保存在: {session_dir}")


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "一只可爱的橘猫"
    asyncio.run(run_flow(prompt))
