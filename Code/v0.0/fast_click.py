import os
import time
import threading
from pynput import keyboard, mouse
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode

mouse_controller = MouseController()

# 状态变量
left_clicking = False
right_clicking = False
clicking_thread = None
current_keys = set()  # 当前按下的组合键

# 默认设置
left_key_combo = {'shift', 'r'}
right_key_combo = {'shift', 'c'}
left_interval = 20
right_interval = 20

# 读取 settings.txt 配置
def load_settings():
    global left_key_combo, right_key_combo, left_interval, right_interval
    def parse_key_combo(value):
        return set(part.strip().lower() for part in value.split('+'))

    try:
        with open("settings.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip().lower()
                if line.startswith("left_key="):
                    left_key_combo = parse_key_combo(line.split("=")[1])
                elif line.startswith("right_key="):
                    right_key_combo = parse_key_combo(line.split("=")[1])
                elif line.startswith("left_interval="):
                    left_interval = int(line.split("=")[1].strip())
                elif line.startswith("right_interval="):
                    right_interval = int(line.split("=")[1].strip())
        print(f"✅ 设置已加载：左键({'+'.join(left_key_combo).upper()}, {left_interval}ms)，右键({'+'.join(right_key_combo).upper()}, {right_interval}ms)")
        print("⚙️ 可在 settings.txt 中修改设置")
    except Exception as e:
        print("⚠️ 无法读取 settings.txt，使用默认配置")

# 连点线程
def click_loop():
    while True:
        if left_clicking:
            mouse_controller.click(Button.left)
            time.sleep(left_interval / 1000.0)
        elif right_clicking:
            mouse_controller.click(Button.right)
            time.sleep(right_interval / 1000.0)
        else:
            time.sleep(0.05)

# 将 pynput 的 key 转为统一字符串表示
def key_to_str(key):
    if isinstance(key, KeyCode):
        return key.char.lower() if key.char else ''
    elif isinstance(key, Key):
        return str(key).replace('Key.', '').lower()
    return ''

# 按键按下
def on_key_press(key):
    global left_clicking, right_clicking, clicking_thread
    k_str = key_to_str(key)
    if k_str:
        current_keys.add(k_str)

        # 检查组合键是否满足
        if current_keys == left_key_combo:
            left_clicking = not left_clicking
            right_clicking = False
            print("左键连点", "✅ 开启" if left_clicking else "❌ 关闭")
        elif current_keys == right_key_combo:
            right_clicking = not right_clicking
            left_clicking = False
            print("右键连点", "✅ 开启" if right_clicking else "❌ 关闭")

        if clicking_thread is None or not clicking_thread.is_alive():
            clicking_thread = threading.Thread(target=click_loop, daemon=True)
            clicking_thread.start()

# 按键释放
def on_key_release(key):
    k_str = key_to_str(key)
    if k_str in current_keys:
        current_keys.remove(k_str)

# 主函数
if __name__ == "__main__":
    load_settings()
    print("🎯 连点器已启动")
    print(f"👉 按 {'+'.join(left_key_combo).upper()} 开/关左键连点（{left_interval}ms），"
          f"{'+'.join(right_key_combo).upper()} 开/关右键连点（{right_interval}ms）")
    with KeyboardListener(on_press=on_key_press, on_release=on_key_release) as listener:
        listener.join()
