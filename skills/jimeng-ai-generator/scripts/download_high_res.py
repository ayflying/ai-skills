import asyncio
from playwright.async_api import async_playwright
import os
import re
import random
import time
from datetime import datetime

OUTPUT_DIR = "D:/git/ai-skills/skills/jimeng-ai-generator/outputs"
BROWSER_PROFILE = "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile"
STORAGE_STATE = os.path.join(BROWSER_PROFILE, "jimeng_vip.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def download_high_res_jimeng(prompt=None, model="4.1"):
    """
    VIP 高清下载方案 (1080P)
    """
    print("=" * 60)
    print(f"即梦AI VIP 高清生成下载器 v5.0")
    print(f"提示词: {prompt}")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_DIR, f"vip_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    async with async_playwright() as p:
        print("\n[1/6] 启动浏览器...")
        browser = await p.chromium.launch(headless=False)

        context = await browser.new_context(
            storage_state=STORAGE_STATE if os.path.exists(STORAGE_STATE) else None,
            viewport={"width": 1920, "height": 1080},
        )
        page = await context.new_page()

        print("[2/6] 访问即梦AI...")
        await page.goto("https://jimeng.jianying.com/ai-tool/generate/?type=image")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # 检查登录
        if await page.query_selector('button:has-text("登录")'):
            print("\n需要登录！请先运行 python browser_server.py")
            await browser.close()
            return

        # 填入提示词
        if prompt:
            print(f"[3/6] 填入提示词...")
            input_box = await page.query_selector(
                'input[placeholder*="描述"], textarea'
            )
            if input_box:
                await input_box.fill(prompt)
                await page.wait_for_timeout(500)
                # 生成
                gen_btn = await page.query_selector('button:has-text("生成")')
                if gen_btn:
                    await gen_btn.click()
                    print("  已触发生成，等待 60 秒...")
                    await page.wait_for_timeout(60000)

        # 查找最新生成的图片
        print("[4/6] 查找生成结果...")
        await page.reload()  # 刷新以同步结果
        await page.wait_for_timeout(3000)

        images = await page.query_selector_all("img")
        target_img = None
        for img in images:
            src = await img.get_attribute("src")
            if src and "dreamina-sign" in src and "resize" in src:
                target_img = img
                break

        if not target_img:
            print("  未找到生成的图片")
            await browser.close()
            return

        # 点击打开预览面板
        print("[5/6] 打开预览面板并获取高清链接...")
        await target_img.click()
        await page.wait_for_timeout(3000)

        # 从预览页提取高清原图 URL
        # 即梦的高清图通常在预览面板的 img 标签中，带有很大的尺寸参数 (如 1080x1080)
        high_res_url = await page.evaluate("""() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            // 过滤出预览区域的图片，通常带有较高的尺寸参数
            const highRes = imgs.find(i => i.src.includes('dreamina') && (i.src.includes('1080') || i.src.includes('720')));
            return highRes ? highRes.src : null;
        }""")

        if not high_res_url:
            print("  未找到高清原图链接，尝试备选方案...")
            high_res_url = await page.evaluate("""() => {
                // 查找所有 dreamina 链接并排序，取最长或包含 resize 的
                const links = Array.from(document.querySelectorAll('img')).map(i => i.src).filter(s => s.includes('dreamina'));
                links.sort((a, b) => b.length - a.length);
                return links[0];
            }""")

        # 下载高清原图
        if high_res_url:
            print(f"[6/6] 下载高清原图...")
            filename = f"high_res_{timestamp}.webp"
            filepath = os.path.join(session_dir, filename)

            # 使用 page.request.get 绕过 referer/cookie 问题
            response = await page.request.get(high_res_url)
            if response.status == 200:
                body = await response.body()
                with open(filepath, "wb") as f:
                    f.write(body)
                print(f"  ✓ 高清原图下载成功: {filename} ({len(body) / 1024:.1f} KB)")

                # 同步到 session_dir 下面的 results
                latest_path = os.path.join(OUTPUT_DIR, "latest_high_res.webp")
                with open(latest_path, "wb") as f:
                    f.write(body)
            else:
                print(f"  ✗ 下载失败: HTTP {response.status}")
        else:
            print("  ✗ 未捕获到高清链接")

        # 保存登录状态
        await context.storage_state(path=STORAGE_STATE)
        print("\n完成！")
        await browser.close()


if __name__ == "__main__":
    import sys

    prompt = sys.argv[1] if len(sys.argv) > 1 else "一只可爱的小橘猫在书架上走动"
    asyncio.run(download_high_res_jimeng(prompt))
