import asyncio
from playwright.async_api import async_playwright
import os
import sys

BROWSER_PROFILE = "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile"
os.makedirs(BROWSER_PROFILE, exist_ok=True)


async def keep_browser_alive():
    """启动浏览器并保持运行，直到用户按Ctrl+C"""
    print("=" * 50)
    print("即梦AI 浏览器后台服务")
    print("=" * 50)
    print("浏览器已启动，按 Ctrl+C 停止")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])

        storage_state_path = os.path.join(BROWSER_PROFILE, "storageState.json")
        context = await browser.new_context(
            storage_state=storage_state_path
            if os.path.exists(storage_state_path)
            else None,
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        await page.goto("https://jimeng.jianying.com/ai-tool/generate/?type=image")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # 检查登录状态
        login_indicator = await page.query_selector('button:has-text("登录")')
        if login_indicator:
            print("WARNING: 需要登录，请在浏览器中扫码/登录...")
        else:
            print("OK: 已登录")

        print("浏览器运行中...")
        print()

        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n保存登录状态...")

        # 保存状态并退出
        await context.storage_state(path=storage_state_path)
        print("登录状态已保存")
        await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(keep_browser_alive())
    except KeyboardInterrupt:
        print("\n已退出")
