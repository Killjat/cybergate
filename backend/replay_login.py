"""
根据用户记录的行为自动登录 Google
"""
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def load_actions(filename="user_actions.json"):
    """加载记录的操作"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def replay_actions(actions, username, password):
    """重放操作"""
    # 使用 undetected-chromedriver
    import undetected_chromedriver as uc

    print("启动浏览器...")
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')

    driver = uc.Chrome(options=options)

    try:
        start_time = time.time()

        for action in actions:
            action_type = action['type']
            elapsed = action['elapsed_time']
            x = action.get('x')
            y = action.get('y')

            # 按照记录的时间延迟执行
            current_elapsed = time.time() - start_time
            wait_time = elapsed - current_elapsed
            if wait_time > 0:
                time.sleep(wait_time)

            print(f"[{elapsed:.2f}s] 执行: {action_type}")

            if action_type == 'mouse_move':
                # 鼠标移动
                actions_chain = ActionChains(driver)
                actions_chain.move_by_offset(x - driver.execute_script("return window.innerWidth/2"),
                                           y - driver.execute_script("return window.innerHeight/2"))
                actions_chain.perform()

            elif action_type == 'mouse_click':
                # 鼠标点击
                if action.get('button') == 'Button.left':
                    actions_chain = ActionChains(driver)
                    actions_chain.click()
                    actions_chain.perform()
                print(f"点击位置: ({x}, {y})")

            elif action_type == 'key_press':
                # 键盘输入
                key = action.get('key')

                # 处理特殊键
                if key.startswith('Key.'):
                    key_name = key.split('.')[-1]
                    if key_name == 'shift':
                        continue
                    elif key_name == 'backspace':
                        ActionChains(driver).send_keys(Keys.BACKSPACE).perform()
                    elif key_name == 'enter':
                        ActionChains(driver).send_keys(Keys.ENTER).perform()
                    elif key_name == 'tab':
                        ActionChains(driver).send_keys(Keys.TAB).perform()
                else:
                    # 普通字符
                    if len(key) == 1 and key.isprintable():
                        ActionChains(driver).send_keys(key).perform()
                        print(f"输入: {key}")

        print("\n操作完成,保持浏览器打开...")
        input("按回车键关闭浏览器...")

    finally:
        driver.quit()

def main():
    # 加载操作记录
    print("加载操作记录...")
    actions = load_actions()
    print(f"加载了 {len(actions)} 个操作")

    # 获取账号信息
    from database import SessionLocal
    from models import Account
    from utils import decrypt_password

    db = SessionLocal()
    account = db.query(Account).filter(Account.id == 1).first()
    if not account:
        print("未找到账号")
        return

    username = account.username
    password = decrypt_password(account.password)

    db.close()

    # 重放操作
    replay_actions(actions, username, password)

if __name__ == "__main__":
    main()
