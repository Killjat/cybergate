"""
最简单的浏览器窗口测试
"""
import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    async with async_playwright() as p:
        print("启动浏览器...")
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        print("创建页面...")
        page = await browser.new_page()
        print("访问 Google...")
        await page.goto("https://www.google.com")
        print("浏览器窗口应该已经显示,按 Ctrl+C 关闭...")

        # 保持浏览器打开
        try:
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            pass

        await browser.close()
        print("浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(test_browser())
