"""
测试 Google 自动登录功能
"""
import asyncio
from playwright.async_api import async_playwright
from database import SessionLocal
from models import Account
from utils import decrypt_password

async def test_google_login():
    db = SessionLocal()
    try:
        # 获取测试账号 (KeltnerAvon@gmail.com)
        account = db.query(Account).filter(Account.id == 1).first()
        if not account:
            print("未找到测试账号")
            return

        username = account.username
        password = decrypt_password(account.password)
        two_factor_secret = account.two_factor_secret

        print(f"开始测试登录: {username}")
        print(f"2FA 密钥: {'已配置' if two_factor_secret else '未配置'}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--start-maximized',
                ]
            )
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN',
                timezone_id='Asia/Shanghai',
            )
            page = await context.new_page()

            # 移除 webdriver 属性
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """)

            try:
                # 访问 Google 登录页面
                print("访问 Google 登录页面...")
                await page.goto("https://accounts.google.com/signin", wait_until="networkidle")
                await asyncio.sleep(2)

                # 填写邮箱
                print(f"填写邮箱: {username}")
                await page.fill('input[type="email"]', username)
                await page.click('button:has-text("Next"), button:has-text("下一步")')
                await asyncio.sleep(3)

                # 填写密码
                print("填写密码...")
                await page.fill('input[type="password"]', password)
                await page.click('button:has-text("Next"), button:has-text("下一步")')
                await asyncio.sleep(4)

                # 处理 2FA
                if two_factor_secret:
                    print("等待 2FA 输入框...")
                    try:
                        await page.wait_for_selector('input[type="tel"], input[name="challenge"], input[data-testid="challenge-input"]', timeout=10000)

                        import pyotp
                        totp = pyotp.TOTP(two_factor_secret)
                        code = totp.now()
                        print(f"生成 2FA 验证码: {code}")

                        totp_input = page.locator('input[type="tel"], input[name="challenge"], input[data-testid="challenge-input"]').first
                        await totp_input.fill(code)
                        await asyncio.sleep(1)

                        print("提交 2FA 验证码...")
                        await page.click('button:has-text("Next"), button:has-text("下一步")')
                        await asyncio.sleep(4)
                    except Exception as e:
                        print(f"2FA 处理异常: {e}")

                # 验证登录结果
                print("验证登录状态...")
                current_url = page.url
                print(f"当前 URL: {current_url}")

                # 检查是否成功登录
                if "accounts.google.com" in current_url:
                    print("✓ 登录成功!")

                    # 尝试获取登录的账号
                    try:
                        account_element = page.locator('div[data-email], [data-email]').first
                        logged_in_email = await account_element.get_attribute('data-email')
                        print(f"登录的账号: {logged_in_email}")

                        if logged_in_email == username:
                            print(f"✓✓ 账号验证成功! 正确登录到 {username}")
                        else:
                            print(f"✗ 账号不匹配! 预期: {username}, 实际: {logged_in_email}")
                    except:
                        print("无法获取登录账号信息")
                else:
                    print(f"✗ 登录失败,当前 URL: {current_url}")

                # 保持浏览器打开以便观察
                print("\n浏览器将保持打开 30 秒以便观察...")
                await asyncio.sleep(30)

            finally:
                await browser.close()

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_google_login())
