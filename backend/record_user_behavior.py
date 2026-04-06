"""
记录用户在浏览器中的行为
"""
import pynput
from pynput import mouse, keyboard
import json
import time
from datetime import datetime

actions = []
start_time = time.time()

def on_move(x, y):
    """记录鼠标移动"""
    elapsed = time.time() - start_time
    actions.append({
        "type": "mouse_move",
        "x": x,
        "y": y,
        "elapsed_time": elapsed,
        "timestamp": datetime.now().isoformat()
    })

def on_click(x, y, button, pressed):
    """记录鼠标点击"""
    elapsed = time.time() - start_time
    if pressed:
        actions.append({
            "type": "mouse_click",
            "x": x,
            "y": y,
            "button": str(button),
            "elapsed_time": elapsed,
            "timestamp": datetime.now().isoformat()
        })
        print(f"鼠标点击: ({x}, {y})")

def on_scroll(x, y, dx, dy):
    """记录鼠标滚动"""
    elapsed = time.time() - start_time
    actions.append({
        "type": "mouse_scroll",
        "x": x,
        "y": y,
        "dx": dx,
        "dy": dy,
        "elapsed_time": elapsed,
        "timestamp": datetime.now().isoformat()
    })

def on_press(key):
    """记录键盘按下"""
    elapsed = time.time() - start_time
    try:
        key_char = key.char
    except AttributeError:
        key_char = str(key)

    actions.append({
        "type": "key_press",
        "key": key_char,
        "elapsed_time": elapsed,
        "timestamp": datetime.now().isoformat()
    })
    print(f"键盘按下: {key_char}")

    # 如果按 ESC,停止记录
    if key == keyboard.Key.esc:
        return False

def on_release(key):
    """记录键盘释放"""
    elapsed = time.time() - start_time
    try:
        key_char = key.char
    except AttributeError:
        key_char = str(key)

    actions.append({
        "type": "key_release",
        "key": key_char,
        "elapsed_time": elapsed,
        "timestamp": datetime.now().isoformat()
    })

def save_actions(filename="user_actions.json"):
    """保存操作到文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(actions, f, indent=2, ensure_ascii=False)
    print(f"\n已保存 {len(actions)} 个操作到 {filename}")

def main():
    print("开始记录用户行为...")
    print("请打开浏览器并登录 Google")
    print("完成后按 ESC 键停止记录")
    print("-" * 50)

    # 创建鼠标和键盘监听器
    mouse_listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    )

    keyboard_listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )

    # 启动监听
    mouse_listener.start()
    keyboard_listener.start()

    # 等待用户按 ESC
    try:
        keyboard_listener.join()
    except KeyboardInterrupt:
        pass

    # 停止监听
    mouse_listener.stop()
    keyboard_listener.stop()

    # 保存操作
    save_actions()

if __name__ == "__main__":
    main()
