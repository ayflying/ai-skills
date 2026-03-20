import asyncio
from playwright.async_api import async_playwright
import os
import re
import random
from datetime import datetime

OUTPUT_DIR = "D:/git/ai-skills/skills/jimeng-ai-generator/outputs"
BROWSER_PROFILE = "D:/git/ai-skills/skills/jimeng-ai-generator/browser-profile"
STORAGE_STATE = os.path.join(BROWSER_PROFILE, "storageState.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BROWSER_PROFILE, exist_ok=True)

# 随机提示词池
RANDOM_PROMPTS = [
    "一只可爱的橘猫在阳光下打盹",
    "未来城市的霓虹夜景赛博朋克风格",
    "一幅抽象派油画色彩斑斓的风景",
    "一只戴着墨镜的酷狗在海边冲浪",
    "中国古典园林亭台楼阁春暖花开",
    "梦幻星空下的独角兽城堡",
    "机械风格的未来机器人武士",
    "日式樱花树下的小木屋",
    "一只穿西装的卡通仓鼠商务精英",
    "海底世界的美人鱼公主",
    "秋日金黄的银杏叶森林小路",
    "未来科幻太空站探索宇宙",
    "可爱的熊猫宝宝抱着竹子卖萌",
    "欧洲中世纪城堡与巨龙战斗",
    "热带雨林瀑布彩虹鸟语花香",
]

# 模型映射
MODEL_MAP = {
    "5.0": "high_aes_general_v50",
    "4.6": "high_aes_general_v42",
    "4.5": "high_aes_general_v40l",
    "4.1": "high_aes_general_v41",
    "4.0": "high_aes_general_v40",
    "3.1": "high_aes_general_v30l_art_fangzhou:general_v3.0_18b",
    "3.0": "high_aes_general_v30l:general_v3.0_18b",
}


async def select_model(page, model_name):
    """选择模型"""
    try:
        config = await page.evaluate("() => window.__image_generate_model_config__")
        if config and "data" in config and "model_list" in config["data"]:
            models = config["data"]["model_list"]
            for m in models:
                if m.get("model_name") == model_name or model_name in m.get(
                    "model_name", ""
                ):
                    req_key = m.get("model_req_key", "")
                    print(f"  找到模型: {m.get('model_name')} -> {req_key}")

                    # 尝试通过JS设置模型
                    result = await page.evaluate(
                        """(reqKey) => {
                            if (window.__image_generate_model_config__) {
                                window.__image_generate_selected_model__ = reqKey;
                                return 'OK: ' + reqKey;
                            }
                            return 'Config not found';
                        }""",
                        req_key,
                    )
                    print(f"  {result}")
                    return True
    except Exception as e:
        print(f"  选择模型失败: {e}")
    return False


async def auto_generate_and_download(
    model_version="4.0", wait_seconds=60, max_images=10
):
    """自动生成图片并下载"""
    print("=" * 60)
    print(f"即梦AI自动生成工具 - 模型: {model_version}")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(OUTPUT_DIR, f"auto_{timestamp}")
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
            print("\n需要登录！请先运行 python browser_server.py 登录")
            await browser.close()
            return None

        # 点击图片创作
        print("[3/6] 选择图片创作模式...")
        buttons = await page.query_selector_all("button")
        for btn in buttons:
            text = await btn.inner_text()
            if text and "图片创作" in text:
                await btn.click()
                await page.wait_for_timeout(2000)
                break

        # 选择模型
        print(f"[4/6] 选择 {model_version} 模型...")
        await select_model(page, model_version)

        # 填入随机提示词
        prompt = random.choice(RANDOM_PROMPTS)
        print(f"[5/6] 填入提示词: {prompt}")

        # 查找输入框
        input_box = await page.query_selector('input[placeholder*="描述"], textarea')
        if input_box:
            await input_box.fill(prompt)
            await page.wait_for_timeout(500)
        else:
            print("  未找到输入框，尝试其他方式...")
            inputs = await page.query_selector_all("input")
            for inp in inputs:
                ph = await inp.get_attribute("placeholder")
                if ph:
                    print(f"  发现输入框: {ph}")
                    await inp.fill(prompt)
                    break

        # 点击生成按钮
        print("  触发生成...")
        gen_buttons = await page.query_selector_all("button")
        for btn in gen_buttons:
            text = await btn.inner_text()
            if text and ("立即生成" in text or "生成" in text):
                try:
                    disabled = await btn.get_attribute("disabled")
                    if disabled is None:
                        await btn.click()
                        print("  已点击生成按钮")
                        break
                except:
                    pass

        # 等待生成
        print(f"\n[6/6] 等待生成完成 ({wait_seconds}秒)...")
        for i in range(wait_seconds):
            await page.wait_for_timeout(1000)
            if (i + 1) % 10 == 0:
                print(f"  已等待 {i + 1}/{wait_seconds} 秒")

        # 截图记录
        await page.screenshot(
            path=os.path.join(session_dir, "result.png"), full_page=True
        )
        print("  结果截图已保存")

        # 下载图片
        image_urls = []

        def handle_response(response):
            url = response.url
            if "dreamina-sign" in url and (".webp" in url or ".png" in url):
                image_urls.append(url)

        page.on("response", handle_response)

        # 刷新以捕获图片
        await page.reload()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(3000)

        # 点击第一张图片触发动态加载
        images = await page.query_selector_all("img")
        for img in images:
            src = await img.get_attribute("src")
            if src and "dreamina-sign" in src and "resize_loss" in src:
                try:
                    await img.click()
                    await page.wait_for_timeout(2000)
                    break
                except:
                    pass

        # 去重并按尺寸排序
        unique_urls = list(set(image_urls))

        def get_size(url):
            m = re.search(r"resize[_\w]*:(\d+):(\d+)", url)
            return int(m.group(1)) * int(m.group(2)) if m else 0

        unique_urls.sort(key=get_size, reverse=True)

        print(f"\n找到 {len(unique_urls)} 个图片URL，开始下载...")

        downloaded = 0
        for i, url in enumerate(unique_urls[:max_images]):
            try:
                ext = ".webp"
                if ".png" in url:
                    ext = ".png"
                m = re.search(r"resize[_\w]*:(\d+):(\d+)", url)
                size_str = f"_{m.group(1)}x{m.group(2)}" if m else ""

                filename = f"generated_{i + 1:02d}{size_str}{ext}"
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

        # 保存登录状态
        await context.storage_state(path=STORAGE_STATE)

        print(f"\n完成！共下载 {downloaded} 张图片")
        print(f"保存位置: {session_dir}")
        await browser.close()
        return session_dir


if __name__ == "__main__":
    import sys

    model = sys.argv[1] if len(sys.argv) > 1 else "4.0"
    wait = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    print(f"使用模型: {model}, 等待时间: {wait}秒")
    result = asyncio.run(auto_generate_and_download(model, wait))
    if result:
        print(f"\n图片已保存到: {result}")
