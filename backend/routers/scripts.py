"""
脚本生成相关 API
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from models import Account
from utils import decrypt_password
from utils_audit import log_audit_action, log_access_action
from fastapi.responses import PlainTextResponse

router = APIRouter()

def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.get("/login-script/{account_id}", response_class=PlainTextResponse)
async def generate_login_script(account_id: int, request: Request, db: Session = Depends(get_db)):
    """生成 Playwright 登录脚本"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    password = decrypt_password(account.password)
    
    # 记录审计日志
    log_audit_action(
        db=db,
        action="download",
        resource_type="script",
        resource_id=account_id,
        user="web_user",
        details={"platform": account.platform, "username": account.username},
        ip_address=get_client_ip(request)
    )
    
    # 记录访问日志
    log_access_action(
        db=db,
        account_id=account.id,
        platform=account.platform,
        username=account.username,
        action="script_download",
        success=True,
        user="web_user",
        ip_address=get_client_ip(request)
    )
    
    # 根据平台生成不同的登录脚本
    if account.platform.lower() == "google":
        return generate_google_script(account.username, password, account.two_factor_secret)
    elif account.platform.lower() == "reddit":
        return generate_reddit_script(account.username, password, account.two_factor_secret)
    elif account.platform.lower() == "github":
        return generate_github_script(account.username, password, account.two_factor_secret)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {account.platform}")

def generate_google_script(username, password, two_factor_secret):
    """生成 Google 登录脚本"""
    script = f'''"""
Google 自动登录脚本
使用 Playwright 自动化登录 Google 账号
"""
from playwright.sync_api import sync_playwright
import requests
import time

def get_totp_code(secret):
    """调用 2FA API 获取验证码"""
    try:
        response = requests.get(f"https://2fa.run/api?secret={{secret}}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("code", "")
        return ""
    except Exception as e:
        print(f"获取 2FA 验证码失败: {{e}}")
        return ""

def login_google():
    """自动登录 Google"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 访问 Google 登录页面
        page.goto("https://accounts.google.com/signin")
        page.wait_for_load_state("networkidle")
        
        # 填写邮箱
        try:
            page.fill('input[type="email"]', "{username}")
            page.click('button:has-text("下一步")')
            time.sleep(2)
        except Exception as e:
            print(f"填写邮箱时出错: {{e}}")
        
        # 填写密码
        try:
            page.fill('input[type="password"]', "{password}")
            page.click('button:has-text("下一步")')
            time.sleep(3)
        except Exception as e:
            print(f"填写密码时出错: {{e}}")
        
        # 处理 Google 2FA 验证（如果存在）
        if "{two_factor_secret}":
            try:
                # 等待 2FA 输入框出现
                print("等待 2FA 输入框出现...")
                
                # 尝试多种可能的 2FA 输入框选择器
                totp_selectors = [
                    'input[name="challenge"]',
                    'input[type="tel"]',
                    'input[aria-label*="验证码"]',
                    'input[aria-label*="code"]',
                    'input[id*="otp"]',
                    'input[name="otp"]',
                    'input[type="text"][autocomplete="one-time-code"]'
                ]
                
                totp_input = None
                for selector in totp_selectors:
                    try:
                        totp_input = page.wait_for_selector(selector, timeout=3000)
                        if totp_input and totp_input.is_visible():
                            print(f"找到 2FA 输入框: {{selector}}")
                            break
                    except:
                        continue
                
                if totp_input and totp_input.is_visible():
                    # 只有当 2FA 输入框出现时，才获取验证码
                    print("检测到 2FA 输入框，正在获取验证码...")
                    totp_code = get_totp_code("{two_factor_secret}")
                    
                    if totp_code:
                        print(f"获取到验证码: {{totp_code}}")
                        totp_input.fill(totp_code)
                        time.sleep(1)
                        
                        # 点击下一步按钮
                        next_buttons = page.locator('button:has-text("下一步"), button:has-text("Next"), button:has-text("Continue")')
                        if next_buttons.count() > 0:
                            next_buttons.first.click()
                            print("已提交验证码")
                            time.sleep(3)
                    else:
                        print("无法获取 2FA 验证码，请手动输入")
            except Exception as e:
                print(f"处理 2FA 时出错: {{e}}")
        
        # 检查是否有验证码
        try:
            if page.is_visible("text=验证码"):
                print("检测到验证码，请手动完成验证")
                input("验证完成后按回车继续...")
        except:
            pass
        
        # 等待登录完成
        time.sleep(5)
        
        print("Google 登录完成！")
        
        # 保持浏览器打开
        input("按回车键关闭浏览器...")
        browser.close()

if __name__ == "__main__":
    login_google()
'''
    return script

def generate_reddit_script(username, password, two_factor_secret):
    """生成 Reddit 登录脚本（通过 Google 账号登录）"""
    script = f'''"""
Reddit 自动登录脚本
使用 Playwright 自动化通过 Google 账号登录 Reddit
"""
from playwright.sync_api import sync_playwright
import requests
import time

def get_totp_code(secret):
    """调用 2FA API 获取验证码"""
    try:
        response = requests.get(f"https://2fa.run/api?secret={{secret}}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("code", "")
        return ""
    except Exception as e:
        print(f"获取 2FA 验证码失败: {{e}}")
        return ""

def login_reddit():
    """通过 Google 账号自动登录 Reddit"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 访问 Reddit 登录页面
        page.goto("https://www.reddit.com/login/")
        page.wait_for_load_state("networkidle")
        
        # 点击使用 Google 账号登录按钮
        try:
            # 查找 Google 登录按钮
            google_login_button = page.locator('button[data-click-id="continue_with_google"]')
            if google_login_button.is_visible():
                google_login_button.click()
                time.sleep(2)
            else:
                # 备选方案：查找 Google 登录链接
                page.click('a[href*="google.com"]')
                time.sleep(2)
        except Exception as e:
            print(f"点击 Google 登录按钮时出错: {{e}}")
            print("尝试直接访问 Google OAuth...")
        
        # Google 账号登录流程
        try:
            # 等待 Google 登录页面加载
            page.wait_for_load_state("networkidle")
            
            # 填写 Google 账号
            page.fill('input[type="email"]', "{username}")
            time.sleep(1)
            page.click('button:has-text("下一步")')
            time.sleep(2)
            
            # 填写密码
            page.fill('input[type="password"]', "{password}")
            time.sleep(1)
            page.click('button:has-text("下一步")')
            time.sleep(3)
            
            # 处理 Google 2FA 验证
            if "{two_factor_secret}":
                try:
                    # 等待 2FA 输入框出现
                    print("等待 2FA 输入框出现...")
                    
                    totp_selectors = [
                        'input[name="challenge"]',
                        'input[type="tel"]',
                        'input[aria-label*="验证码"]',
                        'input[aria-label*="code"]',
                        'input[id*="otp"]',
                        'input[name="otp"]',
                        'input[type="text"][autocomplete="one-time-code"]'
                    ]
                    
                    totp_input = None
                    for selector in totp_selectors:
                        try:
                            totp_input = page.wait_for_selector(selector, timeout=3000)
                            if totp_input and totp_input.is_visible():
                                print(f"找到 2FA 输入框: {{selector}}")
                                break
                        except:
                            continue
                    
                    if totp_input and totp_input.is_visible():
                        # 只有当 2FA 输入框出现时，才获取验证码
                        print("检测到 2FA 输入框，正在获取验证码...")
                        totp_code = get_totp_code("{two_factor_secret}")
                        
                        if totp_code:
                            print(f"获取到验证码: {{totp_code}}")
                            totp_input.fill(totp_code)
                            time.sleep(1)
                            
                            # 点击下一步按钮
                            next_buttons = page.locator('button:has-text("下一步"), button:has-text("Next"), button:has-text("Continue")')
                            if next_buttons.count() > 0:
                                next_buttons.first.click()
                                print("已提交验证码")
                                time.sleep(3)
                        else:
                            print("无法获取 2FA 验证码，请手动输入")
                except Exception as e:
                    print(f"处理 Google 2FA 时出错: {{e}}")
            
            # 确认授权（如果需要）
            try:
                if page.is_visible("button:has-text('继续')") or page.is_visible("button:has-text('Allow')"):
                    page.click("button:has-text('继续'), button:has-text('Allow')")
                    time.sleep(2)
            except:
                pass
            
            # 等待跳转回 Reddit
            time.sleep(5)
            
        except Exception as e:
            print(f"Google 登录流程出错: {{e}}")
        
        # 检查是否有验证码
        try:
            if page.is_visible("text=验证码") or page.is_visible("text=captcha"):
                print("检测到验证码，请手动完成验证")
                input("验证完成后按回车继续...")
        except:
            pass
        
        # 验证是否成功登录 Reddit
        try:
            page.wait_for_url("**/www.reddit.com/**", timeout=10000)
            print("Reddit 登录成功！")
        except:
            print("等待 Reddit 登录超时，请检查登录状态")
        
        # 保持浏览器打开
        input("按回车键关闭浏览器...")
        browser.close()

if __name__ == "__main__":
    login_reddit()
'''
    return script

def generate_github_script(username, password, two_factor_secret):
    """生成 GitHub 登录脚本"""
    script = f'''"""
GitHub 自动登录脚本
使用 Playwright 自动化登录 GitHub 账号
"""
from playwright.sync_api import sync_playwright
import requests
import time

def get_totp_code(secret):
    """调用 2FA API 获取验证码"""
    try:
        response = requests.get(f"https://2fa.run/api?secret={{secret}}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("code", "")
        return ""
    except Exception as e:
        print(f"获取 2FA 验证码失败: {{e}}")
        return ""

def login_github():
    """自动登录 GitHub"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 访问 GitHub 登录页面
        page.goto("https://github.com/login")
        page.wait_for_load_state("networkidle")
        
        # 填写用户名
        try:
            page.fill('input[name="login"]', "{username}")
            time.sleep(1)
        except Exception as e:
            print(f"填写用户名时出错: {{e}}")
        
        # 填写密码
        try:
            page.fill('input[name="password"]', "{password}")
            time.sleep(1)
            
            # 点击登录按钮
            page.click('input[type="submit"][value="Sign in"]')
            time.sleep(3)
        except Exception as e:
            print(f"填写密码时出错: {{e}}")
        
        # 处理 2FA 验证（如果存在）
        if "{two_factor_secret}":
            try:
                # 等待 2FA 输入框出现
                print("等待 2FA 输入框出现...")
                
                totp_selectors = [
                    'input[name="otp"]',
                    'input[type="tel"]',
                    'input[aria-label*="验证码"]',
                    'input[aria-label*="code"]',
                    'input[id*="otp"]',
                    'input[name="authenticator_code"]',
                    'input[type="text"][autocomplete="one-time-code"]'
                ]
                
                totp_input = None
                for selector in totp_selectors:
                    try:
                        totp_input = page.wait_for_selector(selector, timeout=3000)
                        if totp_input and totp_input.is_visible():
                            print(f"找到 2FA 输入框: {{selector}}")
                            break
                    except:
                        continue
                
                if totp_input and totp_input.is_visible():
                    # 只有当 2FA 输入框出现时，才获取验证码
                    print("检测到 2FA 输入框，正在获取验证码...")
                    totp_code = get_totp_code("{two_factor_secret}")
                    
                    if totp_code:
                        print(f"获取到验证码: {{totp_code}}")
                        totp_input.fill(totp_code)
                        time.sleep(1)
                        
                        # 点击提交按钮
                        submit_button = page.locator('button[type="submit"], input[type="submit"]')
                        if submit_button.count() > 0:
                            submit_button.first.click()
                            print("已提交验证码")
                            time.sleep(3)
                    else:
                        print("无法获取 2FA 验证码，请手动输入")
            except Exception as e:
                print(f"处理 2FA 时出错: {{e}}")
        
        # 检查是否有验证码
        try:
            if page.is_visible("text=验证码") or page.is_visible("text=captcha"):
                print("检测到验证码，请手动完成验证")
                input("验证完成后按回车继续...")
        except:
            pass
        
        # 等待登录完成
        time.sleep(5)
        
        print("GitHub 登录完成！")
        
        # 保持浏览器打开
        input("按回车键关闭浏览器...")
        browser.close()

if __name__ == "__main__":
    login_github()
'''
    return script
