"""
自动化登录相关 API
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Account
from utils import decrypt_password
from utils_audit import log_access_action
from playwright.async_api import async_playwright
import asyncio
import random

router = APIRouter()

# user_id -> set of instance_ids，记录每个用户打开的浏览器实例
user_instances: dict[str, set] = {}

def register_instance(user_id: str, inst_id: str):
    user_instances.setdefault(user_id, set()).add(inst_id)

def unregister_instance(user_id: str, inst_id: str):
    if user_id in user_instances:
        user_instances[user_id].discard(inst_id)

def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

@router.get("/totp/{secret}")
async def get_totp_code(secret: str, request: Request, db: Session = Depends(get_db)):
    """生成 TOTP 验证码（后端生成）"""
    try:
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()
        return {"code": code, "expires_in": 30}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成验证码失败: {str(e)}")

@router.post("/validate-totp")
async def validate_totp(body: dict):
    """验证 2FA 密钥是否有效，并返回当前验证码预览"""
    import pyotp, re
    secret = body.get("secret", "").strip().replace(" ", "").replace("-", "")
    if not secret:
        raise HTTPException(status_code=400, detail="密钥不能为空")
    # 支持 otpauth:// 链接
    if "secret=" in secret.lower():
        m = re.search(r"secret=([A-Z2-7a-z0-9=]+)", secret, re.IGNORECASE)
        secret = m.group(1) if m else secret
    try:
        code = pyotp.TOTP(secret).now()
        return {"valid": True, "code": code, "secret": secret}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无效的 2FA 密钥: {e}")

# 存储自动化登录任务状态
login_tasks = {}

async def auto_login_google(username: str, password: str, two_factor_secret: str = None, user_id: str = "anonymous"):
    """
    自动登录 Google - 通过 PinchTab HTTP API 控制 Chrome
    流程: 空白页 -> 地址栏输入 google.com -> 点击登录 -> 输入账号密码 -> 处理 2FA
    """
    import requests as req
    import time

    BASE = "http://localhost:9867"

    def pt_get(path, **kwargs):
        return req.get(f"{BASE}{path}", **kwargs).json()

    def pt_post(path, body=None):
        return req.post(f"{BASE}{path}", json=body or {}).json()

    def human_delay(a=1.5, b=3.5):
        time.sleep(random.uniform(a, b))

    def snap(tab_id, filt="interactive"):
        """获取页面可交互元素快照"""
        return req.get(f"{BASE}/tabs/{tab_id}/snapshot", params={"filter": filt}).json()

    def find_ref(tab_id, hint, retries=3):
        """从 snapshot 里按名字找元素，返回 ref，支持重试"""
        hint_lower = hint.lower()
        for _ in range(retries):
            try:
                data = snap(tab_id, filt="interactive")
                for node in data.get("nodes", []):
                    name = node.get("name", "").lower()
                    if hint_lower in name or name in hint_lower:
                        return node["ref"]
            except Exception:
                pass
            time.sleep(1.5)
        return None

    def find_textbox(tab_id, retries=3):
        """找页面上第一个 textbox"""
        for _ in range(retries):
            try:
                data = snap(tab_id, filt="interactive")
                for node in data.get("nodes", []):
                    if node.get("role") == "textbox":
                        return node["ref"]
            except Exception:
                pass
            time.sleep(1.5)
        return None

    def action(tab_id, kind, ref=None, text=None, selector=None, key=None):
        body = {"kind": kind}
        if ref:      body["ref"] = ref
        if text:     body["text"] = text
        if selector: body["selector"] = selector
        if key:      body["key"] = key
        return pt_post(f"/tabs/{tab_id}/action", body)

    def type_human(tab_id, ref, text):
        """逐字符输入，模拟人类打字速度"""
        action(tab_id, "focus", ref=ref)
        time.sleep(0.3)
        for char in text:
            action(tab_id, "type", ref=ref, text=char)
            time.sleep(random.uniform(0.08, 0.18))
            if random.random() < 0.1:
                time.sleep(random.uniform(0.3, 0.7))

    # ── profile: google_<邮箱前缀> ──────────────────────────────────
    account_prefix = username.split("@")[0].lower()
    profile_name = f"google_{account_prefix}"

    import requests as req
    import time
    BASE = "http://localhost:9867"

    def pt_get(path):
        return req.get(f"{BASE}{path}").json()

    def pt_post(path, body=None):
        return req.post(f"{BASE}{path}", json=body or {}).json()

    try:
        print("连接 PinchTab...")
        pt_get("/health")

        # 查找或创建 profile
        profiles = pt_get("/profiles")
        profile_id = next((p["id"] for p in profiles if p.get("name") == profile_name), None)
        if not profile_id:
            print(f"创建 profile: {profile_name}")
            r = pt_post("/profiles", {"name": profile_name, "description": f"Google: {username}"})
            profile_id = r["id"]
        else:
            print(f"复用 profile: {profile_name} ({profile_id})")

        # 每次新开 instance，用完关掉，session 存 profile
        # 先检查是否有残留 instance，有则先停掉
        print("检查残留 instance...")
        try:
            instances = req.get(f"{BASE}/instances", timeout=10).json()
            for inst in (instances if isinstance(instances, list) else []):
                if inst.get("profileId") == profile_id and inst.get("status") == "running":
                    print(f"停掉残留 instance: {inst['id']}")
                    try:
                        req.post(f"{BASE}/instances/{inst['id']}/stop", timeout=10)
                    except Exception:
                        pass
                    time.sleep(1)
        except Exception:
            pass

        # 清理 Chrome LOCK 文件，防止 profile 被锁定
        profiles_info = pt_get("/profiles")
        prof_path = next((p["path"] for p in profiles_info if p["id"] == profile_id), None)
        if prof_path:
            import os
            lock_file = os.path.join(prof_path, "Default", "LOCK")
            if os.path.exists(lock_file):
                os.remove(lock_file)
                print(f"清理锁文件: {lock_file}")

        print("启动浏览器...")
        inst_info = pt_post("/instances/start", {"profileId": profile_id, "mode": "headed"})
        inst_id = inst_info.get("id") or inst_info.get("instanceId")
        if not inst_id:
            return {"success": False, "message": f"启动失败: {inst_info}"}
        print(f"Instance: {inst_id}")

        # 等待 instance 变成 running
        for _ in range(15):
            time.sleep(2)
            status = req.get(f"{BASE}/instances/{inst_id}").json()
            if status.get("status") == "running":
                print("Chrome 已就绪")
                break

        try:
            # 等待 Chrome 就绪，打开 tab
            tab_id = None
            for i in range(8):
                try:
                    r = pt_post(f"/instances/{inst_id}/tabs/open", {"url": "about:blank"})
                    tab_id = r.get("tabId") or r.get("id")
                    if tab_id:
                        break
                except Exception:
                    pass
                print(f"等待就绪... ({i+1}/8)")
                time.sleep(3)

            if not tab_id:
                return {"success": False, "message": "Chrome 未就绪"}
            print(f"Tab: {tab_id}")
            human_delay(2, 3)

            # ── 第一步：导航到 google.com ────────────────────────────
            print("导航到 google.com...")
            pt_post(f"/tabs/{tab_id}/navigate", {"url": "https://www.google.com"})
            human_delay(3, 5)

            # ── 第二步：随机浏览主页 ─────────────────────────────────
            print("模拟浏览...")
            for _ in range(random.randint(2, 3)):
                action(tab_id, "scroll", text="down")
                human_delay(2, 4)
            action(tab_id, "scroll", text="top")
            human_delay(1, 2)

            # ── 第三步：点击登录按钮 ─────────────────────────────────
            print("查找登录按钮...")
            login_ref = find_ref(tab_id, "Sign in") or find_ref(tab_id, "登录")
            if login_ref:
                print(f"找到: {login_ref}")
                action(tab_id, "hover", ref=login_ref)
                human_delay(0.8, 1.5)
                action(tab_id, "click", ref=login_ref)
                human_delay(4, 6)
            else:
                print("未找到登录按钮，直接导航...")
                pt_post(f"/tabs/{tab_id}/navigate", {
                    "url": "https://accounts.google.com/v3/signin/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin"
                })
                human_delay(4, 6)

            # ── 第四步：输入邮箱 ─────────────────────────────────────
            print("等待邮箱输入框...")
            human_delay(2, 3)
            email_ref = find_textbox(tab_id)
            if not email_ref:
                return {"success": False, "message": "找不到邮箱输入框"}

            print(f"输入邮箱: {username}")
            action(tab_id, "click", ref=email_ref)
            human_delay(0.8, 1.5)
            action(tab_id, "fill", ref=email_ref, text=username)
            human_delay(2, 3)

            next_ref = find_ref(tab_id, "Next") or find_ref(tab_id, "下一步")
            if next_ref:
                action(tab_id, "hover", ref=next_ref)
                human_delay(0.5, 1.0)
                action(tab_id, "click", ref=next_ref)
            else:
                action(tab_id, "press", ref=email_ref, key="Enter")
            print("等待密码页面...")
            human_delay(5, 7)

            # ── 第五步：输入密码 ─────────────────────────────────────
            print("等待密码输入框...")
            human_delay(1, 2)
            pwd_ref = find_textbox(tab_id)
            if not pwd_ref:
                return {"success": False, "message": "找不到密码输入框"}

            print("输入密码...")
            action(tab_id, "click", ref=pwd_ref)
            human_delay(0.8, 1.5)
            action(tab_id, "fill", ref=pwd_ref, text=password)
            human_delay(2, 3)

            next_ref = find_ref(tab_id, "Next") or find_ref(tab_id, "下一步")
            if next_ref:
                action(tab_id, "hover", ref=next_ref)
                human_delay(0.5, 1.0)
                action(tab_id, "click", ref=next_ref)
            else:
                action(tab_id, "press", ref=pwd_ref, key="Enter")
            print("等待登录完成...")
            human_delay(6, 9)

            # ── 第六步：处理 2FA ─────────────────────────────────────
            if two_factor_secret:
                print("检查 2FA...")
                human_delay(2, 3)
                state = snap(tab_id)
                current_url = state.get("url", "")

                # 如果是 challenge/selection 页面，先选 Authenticator app
                if "challenge/selection" in current_url or "challenge/totp" in current_url:
                    print("检测到 2FA 选择页面，查找 Authenticator 选项...")
                    for hint in ["Authenticator app", "authenticator", "Google Authenticator", "Use an authenticator"]:
                        auth_ref = find_ref(tab_id, hint)
                        if auth_ref:
                            print(f"选择: {hint}")
                            action(tab_id, "click", ref=auth_ref)
                            human_delay(3, 5)
                            break

                # 等待验证码输入框
                human_delay(2, 3)
                totp_ref = find_textbox(tab_id)
                if totp_ref:
                    import pyotp, re as _re
                    # 清理密钥格式：去空格/横线，支持 otpauth:// 链接
                    secret = two_factor_secret.strip().replace(' ', '').replace('-', '')
                    if 'secret=' in secret.lower():
                        m = _re.search(r'secret=([A-Z2-7=]+)', secret, _re.IGNORECASE)
                        secret = m.group(1) if m else secret
                    code = pyotp.TOTP(secret).now()
                    print(f"输入 2FA: {code}")
                    action(tab_id, "click", ref=totp_ref)
                    human_delay(0.5, 1.0)
                    action(tab_id, "fill", ref=totp_ref, text=code)
                    human_delay(1, 2)
                    next_ref = find_ref(tab_id, "Next") or find_ref(tab_id, "下一步") or find_ref(tab_id, "Verify")
                    if next_ref:
                        action(tab_id, "hover", ref=next_ref)
                        human_delay(0.5, 1.0)
                        action(tab_id, "click", ref=next_ref)
                    else:
                        action(tab_id, "press", ref=totp_ref, key="Enter")
                    human_delay(4, 6)
                else:
                    print("未找到验证码输入框，查看当前页面...")
                    state = snap(tab_id)
                    print(f"页面: {state.get('url', '')}")

            # ── 第七步：验证结果 ─────────────────────────────────────
            state = snap(tab_id)
            current_url = state.get("url", "")
            print(f"当前 URL: {current_url}")

            if "google.com" in current_url and "accounts.google.com/signin" not in current_url:
                print("登录成功，浏览器保持开启")
                # 注册到用户的 instance 列表
                register_instance(user_id, inst_id)
                return {"success": True, "message": f"成功登录到 {username}", "instance_id": inst_id, "tab_id": tab_id}
            else:
                return {"success": False, "message": f"登录状态不明: {current_url}"}

        except Exception as inner_e:
            import traceback
            traceback.print_exc()
            # 失败时才关闭
            try:
                pt_post(f"/instances/{inst_id}/stop")
            except Exception:
                pass
            return {"success": False, "message": f"登录失败: {str(inner_e)}"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"登录失败: {str(e)}"}


    """直接登录 Reddit 账号"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            # 访问 Reddit 首页
            await page.goto("https://www.reddit.com/", wait_until="networkidle")
            await asyncio.sleep(1)
            
            # 点击登录按钮
            try:
                login_btn = page.locator('button:has-text("Log In"), a[href*="login"]').first
                await login_btn.click()
                await asyncio.sleep(2)
            except:
                # 尝试直接访问登录页面
                await page.goto("https://www.reddit.com/login/", wait_until="networkidle")
                await asyncio.sleep(2)
            
            # 填写用户名和密码
            await page.fill('input[name="username"], input[autocomplete="username"]', username)
            await page.fill('input[name="password"], input[autocomplete="current-password"]', password)
            
            # 点击登录
            await page.click('button[type="submit"], button:has-text("Log In")')
            await asyncio.sleep(3)
            
            # 处理 Reddit 2FA
            if two_factor_secret:
                try:
                    # 等待 2FA 输入框出现
                    await page.wait_for_selector('input[autocomplete="one-time-code"], input[type="text"][placeholder*="code"]', timeout=10000)
                    
                    import pyotp
                    totp = pyotp.TOTP(two_factor_secret)
                    code = totp.now()
                    
                    # 填写验证码
                    await page.fill('input[autocomplete="one-time-code"], input[type="text"][placeholder*="code"]', code)
                    await asyncio.sleep(1)
                    
                    # 点击确认
                    await page.click('button[type="submit"], button:has-text("Log In")')
                    await asyncio.sleep(3)
                except Exception as e:
                    print(f"Reddit 2FA 处理异常: {e}")
            
            # 等待跳转回 Reddit 首页
            try:
                await page.wait_for_url("**/www.reddit.com/**", timeout=15000)
                await asyncio.sleep(2)
                
                # 验证是否登录成功
                try:
                    username_part = username.split('@')[0]
                    user_menu = page.locator(f'text="u/{username_part}"').first
                    if await user_menu.count() > 0:
                        return {"success": True, "message": f"成功登录到 Reddit 账号 {username}"}
                except:
                    pass
                
                return {"success": True, "message": f"成功登录到 Reddit"}
            except:
                return {"success": False, "message": "Reddit 登录后跳转失败"}
            
        except Exception as e:
            result = {"success": False, "message": f"登录失败: {str(e)}"}
        finally:
            await browser.close()

async def auto_login_github(username: str, password: str, two_factor_secret: str = None):
    """自动登录 GitHub"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 访问 GitHub
            await page.goto("https://github.com/")
            await page.wait_for_load_state("networkidle")
            
            # 点击登录
            sign_in_btn = page.locator('a[href="/login"]')
            await sign_in_btn.click()
            await asyncio.sleep(2)
            
            # 填写用户名密码
            await page.fill('input[name="login"]', username)
            await page.fill('input[name="password"]', password)
            
            # 点击登录
            await page.click('input[type="submit"][value="Sign in"]')
            await asyncio.sleep(3)
            
            # 处理 2FA
            if two_factor_secret:
                await page.wait_for_selector('input[name="otp"]', timeout=10000)
                import pyotp
                totp = pyotp.TOTP(two_factor_secret)
                code = totp.now()
                
                await page.fill('input[name="otp"]', code)
                await page.click('button[type="submit"]')
                await asyncio.sleep(3)
            
            # 检查登录成功
            await page.wait_for_url("**/github.com/**", timeout=10000)
            result = {"success": True, "message": "登录成功"}
            
        except Exception as e:
            result = {"success": False, "message": f"登录失败: {str(e)}"}
        finally:
            await browser.close()

@router.post("/open-browser/{account_id}")
async def open_browser(account_id: int, request: Request, db: Session = Depends(get_db)):
    """用已有 session 打开浏览器，支持指定目标 URL"""
    import requests as req

    # 获取 user_id 和目标 URL
    try:
        from auth import decode_token
        auth_header = request.headers.get("authorization", "")
        user_id = decode_token(auth_header[7:]).get("sub", "anonymous") if auth_header.startswith("Bearer ") else "anonymous"
    except Exception:
        user_id = "anonymous"

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    target_url = body.get("url", "https://www.google.com")

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    BASE = "http://localhost:9867"
    account_prefix = account.username.split("@")[0].lower()
    profile_name = f"google_{account_prefix}"

    # 找 profile
    profiles = req.get(f"{BASE}/profiles").json()
    profile_id = next((p["id"] for p in profiles if p.get("name") == profile_name), None)
    if not profile_id:
        raise HTTPException(status_code=404, detail=f"未找到 profile {profile_name}，请先登录")

    # 检查是否已有 running instance，有则复用
    import time
    instances = req.get(f"{BASE}/instances").json()
    inst_id = next((i["id"] for i in instances
                    if i.get("profileId") == profile_id and i.get("status") == "running"), None)

    if not inst_id:
        # 清理 LOCK 文件
        import os
        profiles_info = req.get(f"{BASE}/profiles").json()
        prof_path = next((p["path"] for p in profiles_info if p["id"] == profile_id), None)
        if prof_path:
            lock_file = os.path.join(prof_path, "Default", "LOCK")
            if os.path.exists(lock_file):
                os.remove(lock_file)

        inst_info = req.post(f"{BASE}/instances/start", json={"profileId": profile_id, "mode": "headed"}).json()
        inst_id = inst_info.get("id") or inst_info.get("instanceId")
        if not inst_id:
            raise HTTPException(status_code=500, detail=f"启动失败: {inst_info}")
        # 等待 instance 变成 running 状态
        for _ in range(15):
            time.sleep(2)
            status = req.get(f"{BASE}/instances/{inst_id}").json()
            if status.get("status") == "running":
                break

    # 打开目标 URL
    tab_id = None
    for _ in range(8):
        try:
            r = req.post(f"{BASE}/instances/{inst_id}/tabs/open",
                         json={"url": target_url}).json()
            tab_id = r.get("tabId") or r.get("id")
            if tab_id:
                break
        except Exception:
            pass
        time.sleep(3)

    if not tab_id:
        raise HTTPException(status_code=500, detail="Chrome 未就绪")

    # 注册到用户的 instance 列表
    register_instance(user_id, inst_id)

    return {
        "success": True,
        "instance_id": inst_id,
        "tab_id": tab_id,
        "message": f"已用 {account.username} 的 session 打开浏览器"
    }


@router.post("/close-browser/{instance_id}")
async def close_browser(instance_id: str):
    """关闭指定 instance"""
    import requests as req
    BASE = "http://localhost:9867"
    req.post(f"{BASE}/instances/{instance_id}/stop")
    return {"success": True, "message": f"instance {instance_id} 已关闭"}


@router.get("/accounts/{account_id}/linked-platforms")
async def get_linked_platforms(account_id: int, db: Session = Depends(get_db)):
    """获取某个 Google 账号关联的平台列表"""
    from models import LinkedPlatform
    items = db.query(LinkedPlatform).filter(LinkedPlatform.account_id == account_id).all()
    return [{"id": i.id, "platform": i.platform, "status": i.status, "logged_in_at": i.logged_in_at} for i in items]


@router.post("/accounts/{account_id}/linked-platforms")
async def add_linked_platform(account_id: int, body: dict, db: Session = Depends(get_db)):
    """给 Google 账号添加关联平台（如 reddit）"""
    from models import LinkedPlatform
    platform = body.get("platform", "").lower()
    if not platform:
        raise HTTPException(status_code=400, detail="platform 不能为空")
    exists = db.query(LinkedPlatform).filter(
        LinkedPlatform.account_id == account_id,
        LinkedPlatform.platform == platform
    ).first()
    if exists:
        return {"id": exists.id, "platform": exists.platform, "status": exists.status}
    lp = LinkedPlatform(account_id=account_id, platform=platform, status="pending")
    db.add(lp)
    db.commit()
    db.refresh(lp)
    return {"id": lp.id, "platform": lp.platform, "status": lp.status}


@router.delete("/accounts/{account_id}/linked-platforms/{platform}")
async def remove_linked_platform(account_id: int, platform: str, db: Session = Depends(get_db)):
    from models import LinkedPlatform
    db.query(LinkedPlatform).filter(
        LinkedPlatform.account_id == account_id,
        LinkedPlatform.platform == platform
    ).delete()
    db.commit()
    return {"message": "已删除"}


@router.get("/profiles")
async def list_profiles(db: Session = Depends(get_db)):
    """列出所有账号对应的 profile 状态，供情报采集系统查询"""
    import requests as req
    BASE = "http://localhost:9867"

    accounts = db.query(Account).all()
    pinchtab_profiles = req.get(f"{BASE}/profiles", timeout=5).json()
    profile_map = {p["name"]: p for p in pinchtab_profiles}

    result = []
    for acc in accounts:
        prefix = acc.username.split("@")[0].lower()
        profile_name = f"google_{prefix}"
        p = profile_map.get(profile_name, {})
        result.append({
            "account_id": acc.id,
            "username": acc.username,
            "platform": acc.platform,
            "profile_name": profile_name,
            "profile_id": p.get("id"),
            "has_session": p.get("hasAccount", False),
            "session_email": p.get("accountEmail", ""),
            "size_mb": round(p.get("sizeMB", 0), 1),
        })
    return result


@router.get("/profiles/{account_id}/export")
async def export_profile(account_id: int, db: Session = Depends(get_db)):
    """打包下载指定账号的 Chrome Profile，供情报采集系统部署到远程节点"""
    import requests as req, tarfile, io, os
    from fastapi.responses import StreamingResponse
    BASE = "http://localhost:9867"

    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    prefix = account.username.split("@")[0].lower()
    profile_name = f"google_{prefix}"

    # 找 profile 路径
    profiles = req.get(f"{BASE}/profiles", timeout=5).json()
    profile = next((p for p in profiles if p.get("name") == profile_name), None)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile {profile_name} 不存在，请先登录")
    if not profile.get("hasAccount"):
        raise HTTPException(status_code=400, detail="该账号尚未完成登录，session 未保存")

    profile_path = profile["path"]
    if not os.path.exists(profile_path):
        raise HTTPException(status_code=404, detail="Profile 目录不存在")

    # 打包成 tar.gz，流式返回
    def generate():
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            tar.add(profile_path, arcname=profile_name)
        buf.seek(0)
        yield buf.read()

    filename = f"{profile_name}.tar.gz"
    return StreamingResponse(
        generate(),
        media_type="application/gzip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/logout")
async def logout(body: dict = {}, request: Request = None):
    """用户退出时关闭所有该用户的 instances"""
    import requests as req
    BASE = "http://localhost:9867"

    # 从 token 拿 user_id
    user_id = "anonymous"
    if request:
        try:
            from auth import decode_token
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                user_id = decode_token(auth_header[7:]).get("sub", "anonymous")
        except Exception:
            pass

    # 合并：token 里的 user_id 对应的 instances + 前端传来的 instance_ids
    ids_to_close = set(body.get("instance_ids", []))
    ids_to_close.update(user_instances.pop(user_id, set()))

    closed = []
    for inst_id in ids_to_close:
        try:
            req.post(f"{BASE}/instances/{inst_id}/stop", timeout=3)
            closed.append(inst_id)
        except Exception:
            pass
    return {"closed": closed}


@router.post("/start-auto-login/{account_id}")
async def start_auto_login(account_id: int, request: Request, db: Session = Depends(get_db)):
    """开始自动化登录"""
    # 获取当前用户（可选，游客也允许）
    from auth import get_current_user_optional
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    current_user = None
    try:
        from auth import decode_token
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            payload = decode_token(auth_header[7:])
            current_user_id = payload.get("sub", "anonymous")
        else:
            current_user_id = "anonymous"
    except Exception:
        current_user_id = "anonymous"
    """开始自动化登录"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    password = decrypt_password(account.password)

    log_access_action(
        db=db,
        account_id=account.id,
        platform=account.platform,
        username=account.username,
        action="auto_login_start",
        success=True,
        user="web_user",
        ip_address=get_client_ip(request)
    )

    task_id = f"login_{account_id}_{int(asyncio.get_event_loop().time()*1000)}"

    if account.platform.lower() == "google":
        loop = asyncio.get_event_loop()
        import functools
        login_tasks[task_id] = loop.run_in_executor(
            None,
            functools.partial(
                _run_google_login,
                account.username, password, account.two_factor_secret, current_user_id
            )
        )
    elif account.platform.lower() == "reddit":
        # Reddit 用 Google 账号登录，找关联的 Google 账号
        from models import LinkedPlatform
        lp = db.query(LinkedPlatform).filter(
            LinkedPlatform.account_id == account_id,
            LinkedPlatform.platform == "reddit"
        ).first()
        if not lp:
            raise HTTPException(status_code=400, detail="请先在账号详情里关联 Reddit 平台")
        google_account = db.query(Account).filter(Account.id == lp.account_id).first()
        loop = asyncio.get_event_loop()
        import functools
        login_tasks[task_id] = loop.run_in_executor(
            None,
            functools.partial(_run_reddit_login, google_account.username, account_id, current_user_id)
        )
    else:
        raise HTTPException(status_code=400, detail=f"暂不支持平台: {account.platform}")

    return {"task_id": task_id, "status": "started", "message": "自动化登录已启动"}


def _run_google_login(username, password, two_factor_secret, user_id="anonymous"):
    """同步包装，供 executor 调用"""
    import asyncio as _asyncio
    return _asyncio.run(auto_login_google(username, password, two_factor_secret, user_id))


async def auto_login_reddit(google_username: str, account_id: int, user_id: str = "anonymous"):
    """
    用 Google 账号登录 Reddit（Continue with Google）
    复用 google_xxx profile，Reddit session 也存入同一个 profile
    """
    import requests as req, time, re
    from database import SessionLocal
    from models import LinkedPlatform

    BASE = "http://localhost:9867"
    account_prefix = google_username.split("@")[0].lower()
    profile_name = f"google_{account_prefix}"

    def pt_get(path): return req.get(f"{BASE}{path}", timeout=10).json()
    def pt_post(path, body=None): return req.post(f"{BASE}{path}", json=body or {}, timeout=10).json()
    def human_delay(a=1.5, b=3.5): time.sleep(random.uniform(a, b))

    def snap(tab_id, filt="interactive"):
        return req.get(f"{BASE}/tabs/{tab_id}/snapshot", params={"filter": filt}, timeout=10).json()

    def find_ref(tab_id, hint, retries=3):
        hint_lower = hint.lower()
        for _ in range(retries):
            try:
                data = snap(tab_id)
                for node in data.get("nodes", []):
                    if hint_lower in node.get("name", "").lower():
                        return node["ref"]
            except Exception:
                pass
            time.sleep(1.5)
        return None

    def action(tab_id, kind, ref=None, text=None, key=None):
        body = {"kind": kind}
        if ref:  body["ref"] = ref
        if text: body["text"] = text
        if key:  body["key"] = key
        return pt_post(f"/tabs/{tab_id}/action", body)

    try:
        # 找 Google profile
        profiles = pt_get("/profiles")
        profile_id = next((p["id"] for p in profiles if p.get("name") == profile_name), None)
        if not profile_id:
            return {"success": False, "message": f"未找到 profile {profile_name}，请先完成 Google 登录"}
        if not next((p for p in profiles if p.get("name") == profile_name and p.get("hasAccount")), None):
            return {"success": False, "message": "Google 账号尚未登录，请先完成 Google 登录"}

        # 清理残留 instance
        instances = pt_get("/instances")
        for inst in (instances if isinstance(instances, list) else []):
            if inst.get("profileId") == profile_id and inst.get("status") == "running":
                try: pt_post(f"/instances/{inst['id']}/stop")
                except Exception: pass
                time.sleep(1)

        # 清理 LOCK 文件
        import os
        prof_path = next((p["path"] for p in profiles if p["id"] == profile_id), None)
        if prof_path:
            lock = os.path.join(prof_path, "Default", "LOCK")
            if os.path.exists(lock): os.remove(lock)

        # 启动 instance（用 Google profile）
        print(f"用 {profile_name} 启动浏览器...")
        inst_info = pt_post("/instances/start", {"profileId": profile_id, "mode": "headed"})
        inst_id = inst_info.get("id") or inst_info.get("instanceId")
        if not inst_id:
            return {"success": False, "message": f"启动失败: {inst_info}"}

        # 等待就绪
        for _ in range(15):
            time.sleep(2)
            if pt_get(f"/instances/{inst_id}").get("status") == "running":
                break

        try:
            # 打开 Reddit
            print("导航到 reddit.com...")
            r = pt_post(f"/instances/{inst_id}/tabs/open", {"url": "https://www.reddit.com"})
            tab_id = r.get("tabId") or r.get("id")
            if not tab_id:
                return {"success": False, "message": "无法打开 tab"}
            human_delay(3, 5)

            # 随机浏览一下
            action(tab_id, "scroll", text="down")
            human_delay(2, 3)
            action(tab_id, "scroll", text="top")
            human_delay(1, 2)

            # 找登录按钮
            print("查找登录按钮...")
            login_ref = find_ref(tab_id, "Log In") or find_ref(tab_id, "Sign Up") or find_ref(tab_id, "login")
            if login_ref:
                action(tab_id, "hover", ref=login_ref)
                human_delay(0.8, 1.5)
                action(tab_id, "click", ref=login_ref)
                human_delay(3, 5)
            else:
                pt_post(f"/tabs/{tab_id}/navigate", {"url": "https://www.reddit.com/login"})
                human_delay(3, 5)

            # 找 "Continue with Google" 按钮
            print("查找 Continue with Google...")
            google_ref = find_ref(tab_id, "Continue with Google") or find_ref(tab_id, "Google")
            if not google_ref:
                return {"success": False, "message": "未找到 Continue with Google 按钮"}

            action(tab_id, "hover", ref=google_ref)
            human_delay(0.8, 1.5)
            action(tab_id, "click", ref=google_ref)
            print("等待 Google 授权...")
            human_delay(5, 8)

            # Google 授权页 — 已登录状态，找账号或直接确认
            state = snap(tab_id)
            current_url = state.get("url", "")
            print(f"当前 URL: {current_url}")

            if "accounts.google.com" in current_url:
                # 可能需要选择账号
                account_ref = find_ref(tab_id, google_username) or find_ref(tab_id, google_username.split("@")[0])
                if account_ref:
                    print(f"选择账号: {google_username}")
                    action(tab_id, "click", ref=account_ref)
                    human_delay(3, 5)
                else:
                    # 直接点 Continue
                    continue_ref = find_ref(tab_id, "Continue") or find_ref(tab_id, "Allow")
                    if continue_ref:
                        action(tab_id, "click", ref=continue_ref)
                        human_delay(3, 5)

            # 等待跳回 Reddit
            human_delay(4, 6)
            state = snap(tab_id)
            current_url = state.get("url", "")
            print(f"最终 URL: {current_url}")

            if "reddit.com" in current_url and "login" not in current_url:
                # 更新数据库 linked_platforms 状态
                db = SessionLocal()
                try:
                    lp = db.query(LinkedPlatform).filter(
                        LinkedPlatform.account_id == account_id,
                        LinkedPlatform.platform == "reddit"
                    ).first()
                    if lp:
                        from datetime import datetime
                        lp.status = "logged_in"
                        lp.logged_in_at = datetime.utcnow()
                        db.commit()
                finally:
                    db.close()

                register_instance(user_id, inst_id)
                return {"success": True, "message": f"Reddit 登录成功（使用 {google_username}）", "instance_id": inst_id}
            else:
                return {"success": False, "message": f"Reddit 登录失败，当前页面: {current_url}"}

        except Exception as e:
            try: pt_post(f"/instances/{inst_id}/stop")
            except Exception: pass
            raise e

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"Reddit 登录失败: {str(e)}"}


def _run_reddit_login(google_username, account_id, user_id="anonymous"):
    import asyncio as _asyncio
    return _asyncio.run(auto_login_reddit(google_username, account_id, user_id))

@router.get("/login-status/{task_id}")
async def get_login_status(task_id: str):
    """获取登录状态"""
    if task_id not in login_tasks:
        return {"status": "not_found", "message": "任务不存在"}
    
    task = login_tasks[task_id]
    if task.done():
        try:
            result = task.result()
            return {"status": "completed", "result": result}
        except Exception as e:
            return {"status": "failed", "message": str(e)}
    else:
        return {"status": "in_progress", "message": "登录进行中..."}

