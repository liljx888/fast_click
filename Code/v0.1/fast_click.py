import os
import time
import threading
import tkinter as tk
from tkinter import messagebox
from pynput import keyboard, mouse
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode

# 控制变量
mouse_controller = MouseController()
left_clicking = False
right_clicking = False
clicking_thread = None
current_keys = set()
clicker_enabled = True

# 设置默认值
left_key_combo = {'shift', 'r'}
right_key_combo = {'shift', 'c'}
left_interval = 20
right_interval = 20
settings_path = "settings.txt"

# GUI变量
gui_left_state = None
gui_right_state = None
gui_enabled_var = None
left_key_entry = None
right_key_entry = None
left_interval_entry = None
right_interval_entry = None

# ========== 设置读取与保存 ==========
def parse_key_combo(value):
    return set(part.strip().lower() for part in value.split('+'))

def load_settings():
    global left_key_combo, right_key_combo, left_interval, right_interval
    if not os.path.exists(settings_path):
        return
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip().lower()
                if line.startswith("left_key="):
                    left_key_combo = parse_key_combo(line.split("=")[1])
                elif line.startswith("right_key="):
                    right_key_combo = parse_key_combo(line.split("=")[1])
                elif line.startswith("left_interval="):
                    left_interval = int(line.split("=")[1])
                elif line.startswith("right_interval="):
                    right_interval = int(line.split("=")[1])
    except:
        messagebox.showerror("读取失败", "读取 settings.txt 出错，使用默认配置。")

def save_settings():
    global left_key_combo, right_key_combo, left_interval, right_interval
    try:
        left_key_combo.clear()
        right_key_combo.clear()

        left_key_combo.update(parse_key_combo(left_key_entry.get()))
        right_key_combo.update(parse_key_combo(right_key_entry.get()))
        left_interval = int(left_interval_entry.get())
        right_interval = int(right_interval_entry.get())

        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(f"left_key={'+'.join(left_key_combo).upper()}\n")
            f.write(f"right_key={'+'.join(right_key_combo).upper()}\n")
            f.write(f"left_interval={left_interval}\n")
            f.write(f"right_interval={right_interval}\n")
        messagebox.showinfo("保存成功", "设置已保存到 settings.txt")
    except:
        messagebox.showerror("保存失败", "无法保存设置，请检查输入格式。")

# ========== 连点器功能 ==========
def click_loop():
    while True:
        if not clicker_enabled:
            time.sleep(0.1)
            continue
        if left_clicking:
            mouse_controller.click(Button.left)
            time.sleep(left_interval / 1000.0)
        elif right_clicking:
            mouse_controller.click(Button.right)
            time.sleep(right_interval / 1000.0)
        else:
            time.sleep(0.05)

def key_to_str(key):
    if isinstance(key, KeyCode):
        return key.char.lower() if key.char else ''
    elif isinstance(key, Key):
        return str(key).replace('Key.', '').lower()
    return ''

def on_key_press(key):
    global left_clicking, right_clicking, clicking_thread
    if not clicker_enabled:
        return

    k_str = key_to_str(key)
    if k_str:
        current_keys.add(k_str)

        if current_keys == left_key_combo:
            toggle_left()
        elif current_keys == right_key_combo:
            toggle_right()

        if clicking_thread is None or not clicking_thread.is_alive():
            start_clicking()

def on_key_release(key):
    k_str = key_to_str(key)
    if k_str in current_keys:
        current_keys.remove(k_str)

def start_clicking():
    global clicking_thread
    clicking_thread = threading.Thread(target=click_loop, daemon=True)
    clicking_thread.start()

def toggle_left():
    global left_clicking, right_clicking
    left_clicking = not left_clicking
    right_clicking = False
    update_gui()

def toggle_right():
    global left_clicking, right_clicking
    right_clicking = not right_clicking
    left_clicking = False
    update_gui()

def update_gui():
    gui_left_state.set("开启 ✅" if left_clicking else "关闭 ❌")
    gui_right_state.set("开启 ✅" if right_clicking else "关闭 ❌")

# ========== GUI ==========
def create_gui():
    global gui_left_state, gui_right_state, gui_enabled_var
    global left_key_entry, right_key_entry, left_interval_entry, right_interval_entry
    load_settings()

    root = tk.Tk()
    root.title("🖱 快捷连点器")
    root.geometry("500x300")
    root.resizable(False, False)

    gui_enabled_var = tk.BooleanVar(value=True)
    gui_left_state = tk.StringVar(value="关闭 ❌")
    gui_right_state = tk.StringVar(value="关闭 ❌")

    # ===== 顶部总开关 =====
    tk.Checkbutton(root, text="启用连点器", variable=gui_enabled_var,
                   command=lambda: toggle_clicker(gui_enabled_var.get()),
                   font=("Arial", 10)).grid(row=0, column=0, columnspan=2, pady=10, sticky="n")

    # ===== 左键区域 =====
    tk.Label(root, text="左键快捷键: (编辑后需要保存设置)").grid(row=1, column=0, sticky="w", padx=10)
    left_key_entry = tk.Entry(root)
    left_key_entry.insert(0, '+'.join(left_key_combo).upper())
    left_key_entry.grid(row=2, column=0, padx=10, sticky="we")

    tk.Label(root, text="左键间隔(ms): (编辑后需要保存设置)").grid(row=3, column=0, sticky="w", padx=10)
    left_interval_entry = tk.Entry(root)
    left_interval_entry.insert(0, str(left_interval))
    left_interval_entry.grid(row=4, column=0, padx=10, sticky="we")

    tk.Label(root, text="当前状态：").grid(row=5, column=0, sticky="w", padx=10)
    tk.Label(root, textvariable=gui_left_state, fg='green').grid(row=6, column=0, padx=10)

    # ===== 右键区域 =====
    tk.Label(root, text="右键快捷键: (编辑后需要保存设置)").grid(row=1, column=1, sticky="w", padx=10)
    right_key_entry = tk.Entry(root)
    right_key_entry.insert(0, '+'.join(right_key_combo).upper())
    right_key_entry.grid(row=2, column=1, padx=10, sticky="we")

    tk.Label(root, text="右键间隔(ms): (编辑后需要保存设置)").grid(row=3, column=1, sticky="w", padx=10)
    right_interval_entry = tk.Entry(root)
    right_interval_entry.insert(0, str(right_interval))
    right_interval_entry.grid(row=4, column=1, padx=10, sticky="we")

    tk.Label(root, text="当前状态：").grid(row=5, column=1, sticky="w", padx=10)
    tk.Label(root, textvariable=gui_right_state, fg='blue').grid(row=6, column=1, padx=10)

    # ===== 底部按钮区域 =====
    tk.Button(root, text="💾 保存设置", command=save_settings).grid(row=7, column=0, pady=20)
    tk.Button(root, text="❌ 退出程序", command=root.destroy).grid(row=7, column=1, pady=20)

    # 设置列宽比例
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)

    threading.Thread(target=start_keyboard_listener, daemon=True).start()
    root.mainloop()

def toggle_clicker(enabled):
    global clicker_enabled, left_clicking, right_clicking
    clicker_enabled = enabled
    if not enabled:
        left_clicking = False
        right_clicking = False
        update_gui()

def start_keyboard_listener():
    with KeyboardListener(on_press=on_key_press, on_release=on_key_release) as listener:
        listener.join()

# 启动入口
if __name__ == "__main__":
    create_gui()
