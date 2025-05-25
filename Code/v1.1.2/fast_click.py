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

# 默认设置
left_key_combo = {'shift', 'r'}
right_key_combo = {'shift', 'c'}
left_interval = 20
right_interval = 20
theme_mode = "light"
settings_path = "settings.txt"

# GUI变量
gui_left_state = None
gui_right_state = None
gui_enabled_var = None
left_key_entry = None
right_key_entry = None
left_interval_entry = None
right_interval_entry = None
root = None
theme_button = None

# GitHub风格主题
light_theme = {
    "bg": "#ffffff",
    "fg": "#24292f",
    "btn_bg": "#f6f8fa",
    "entry_bg": "#ffffff",
    "border": "#d0d7de",
    "section_bg": "#f6f8fa"
}

dark_theme = {
    "bg": "#0d1117",
    "fg": "#c9d1d9",
    "btn_bg": "#21262d",
    "entry_bg": "#161b22",
    "border": "#30363d",
    "section_bg": "#161b22"
}


# ========== 设置读取与保存 ==========
def parse_key_combo(value):
    return set(part.strip().lower() for part in value.split('+'))

def load_settings():
    global left_key_combo, right_key_combo, left_interval, right_interval, theme_mode
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
                elif line.startswith("theme="):
                    theme_mode = line.split("=")[1].strip()
    except:
        messagebox.showerror("读取失败", "读取 settings.txt 出错，使用默认配置。")

def save_settings(silent=False):
    global left_key_combo, right_key_combo, left_interval, right_interval, theme_mode
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
            f.write(f"theme={theme_mode}\n")
        if not silent:  # 静默模式下不显示提示
            messagebox.showinfo("保存成功", "设置已保存到 settings.txt")
    except:
        messagebox.showerror("保存失败", "无法保存设置，请检查输入格式。")

def restore_defaults():
    global theme_mode

    left_key_entry.delete(0, tk.END)
    left_key_entry.insert(0, 'Shift+R')
    right_key_entry.delete(0, tk.END)
    right_key_entry.insert(0, 'Shift+C')
    left_interval_entry.delete(0, tk.END)
    left_interval_entry.insert(0, '20')
    right_interval_entry.delete(0, tk.END)
    right_interval_entry.insert(0, '20')
    theme_mode = "light"
    apply_theme()
    save_settings(silent=True)


# ========== 连点器逻辑 ==========
def left_click_loop():
    while True:
        if clicker_enabled and left_clicking:
            mouse_controller.click(Button.left)
            time.sleep(left_interval / 1000.0)
        else:
            time.sleep(0.05)

def right_click_loop():
    while True:
        if clicker_enabled and right_clicking:
            mouse_controller.click(Button.right)
            time.sleep(right_interval / 1000.0)
        else:
            time.sleep(0.05)


# ========== 键盘输入 ==========
def is_editing_entry():
    focused = root.focus_get()
    return focused in [left_key_entry, right_key_entry, left_interval_entry, right_interval_entry]

def key_to_str(key):
    if isinstance(key, KeyCode):
        try:
            # 处理数字小键盘等特殊键
            if key.vk >= 96 and key.vk <= 105:  # 小键盘数字
                return str(key.vk - 96)
            # 通过虚拟键码获取字符（兼容Ctrl组合）
            char = chr(key.vk).lower()
            if char.isalnum():  # 接受字母和数字
                return char
        except Exception as e:
            pass
        return key.char.lower() if key.char else ''

    elif isinstance(key, Key):
        key_str = str(key).replace('Key.', '').lower()
        if key_str in ['ctrl_l', 'ctrl_r']:
            return 'ctrl'
        if key_str in ['alt_l', 'alt_r', 'alt_gr']:
            return 'alt'
        if key_str in ['shift_l', 'shift_r']:
            return 'shift'
        return key_str
    return ''

def on_key_press(key):
    global left_clicking, right_clicking
    if is_editing_entry() or not clicker_enabled:
        return

    k_str = key_to_str(key)
    if not k_str:
        return

    current_keys.add(k_str)
    
    # 使用精确匹配但允许任意顺序
    if left_key_combo == current_keys:
        toggle_left()
        current_keys.clear()
    elif right_key_combo == current_keys:
        toggle_right()
        current_keys.clear()

def on_key_release(key):
    if is_editing_entry():
        return
    
    k_str = key_to_str(key)

    if k_str in current_keys:
        current_keys.remove(k_str)

    for mod in ['ctrl', 'alt', 'shift']:
        current_keys.discard(mod)

def toggle_left():
    global left_clicking
    left_clicking = not left_clicking
    update_gui()

def toggle_right():
    global right_clicking
    right_clicking = not right_clicking
    update_gui()

def update_gui():
    gui_left_state.set("开启 ✅" if left_clicking else "关闭 ❌")
    gui_right_state.set("开启 ✅" if right_clicking else "关闭 ❌")


# ========== 主题切换 ==========
def apply_theme():
    theme = light_theme if theme_mode == "light" else dark_theme
    root.configure(bg=theme["bg"])
    
    for widget in root.winfo_children():
        if isinstance(widget, tk.Frame):
            widget.configure(
                bg=theme["section_bg"],                 # 设置Frame背景色
                highlightbackground=theme["border"],    # 边框颜色
                highlightthickness=1                    # 显示边框
            )
            for child in widget.winfo_children():
                try:
                    if isinstance(child, tk.Label):
                        child.configure(bg=theme["section_bg"], fg=theme["fg"])
                    elif isinstance(child, tk.Entry):
                        child.configure(
                            bg=theme["entry_bg"],
                            fg=theme["fg"],
                            insertbackground=theme["fg"]  # 光标颜色
                        )
                except:
                    pass

        # 处理勾选框的特殊颜色
        if isinstance(widget, tk.Checkbutton):
            widget.configure(
                selectcolor=theme["bg"],        # 勾选框背景色（选中时）
                fg=theme["fg"],                 # 文本颜色
                bg=theme["bg"],                 # 背景色
                activebackground=theme["bg"],   # 激活状态背景色
                activeforeground=theme["fg"]    # 激活状态文本颜色
            )

        elif isinstance(widget, tk.Entry):
            widget.configure(
                bg=theme["entry_bg"],
                fg=theme["fg"],
                insertbackground=theme["fg"],           # 光标颜色
                highlightbackground=theme["border"],    # 外边框颜色（失焦）
                highlightcolor=theme["border"]          # 聚焦时边框颜色
            )

        elif isinstance(widget, tk.Button):
            widget.configure(
                bg=theme["btn_bg"],
                fg=theme["fg"],
                activebackground=theme["border"],
                activeforeground=theme["fg"],
                relief=tk.RAISED
            )

        elif isinstance(widget, tk.Label):
            widget.configure(bg=theme["bg"], fg=theme["fg"])

    # 更新主题切换按钮本身
    theme_button.configure(
        text="🌙 深色" if theme_mode == "light" else "☀️ 浅色",
        bg=theme["btn_bg"],
        fg=theme["fg"],
        activebackground=theme["border"],
        activeforeground=theme["fg"]
    )


def toggle_theme():
    global theme_mode
    theme_mode = "dark" if theme_mode == "light" else "light"
    apply_theme()
    save_settings(silent=True)


# ========== GUI ==========
def toggle_clicker(enabled):
    global clicker_enabled, left_clicking, right_clicking
    clicker_enabled = enabled
    if not enabled:
        left_clicking = False
        right_clicking = False
        update_gui()

def start_keyboard_listener():
    with KeyboardListener(
        on_press=on_key_press,
        on_release=on_key_release
    ) as listener:
        listener.join()

def create_gui():
    global gui_left_state, gui_right_state, gui_enabled_var
    global left_key_entry, right_key_entry, left_interval_entry, right_interval_entry
    global root, theme_button
    load_settings()

    root = tk.Tk()
    root.title("🖱 刘牢板连点器")
    root.geometry("420x300")
    root.resizable(False, False)

    gui_enabled_var = tk.BooleanVar(value=True)
    gui_left_state = tk.StringVar(value="关闭 ❌")
    gui_right_state = tk.StringVar(value="关闭 ❌")

    # ===== 总开关 =====
    tk.Checkbutton(root, text="启用连点器", variable=gui_enabled_var,
                command=lambda: toggle_clicker(gui_enabled_var.get()),
                font=("Consola", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

    # ===== 右上角主题按钮 =====
    theme_button = tk.Button(root, text="🌙 深色", command=toggle_theme)
    theme_button.place(x=360, y=10)

    # ===== 左键区域 =====
    left_frame = tk.Frame(root)
    left_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    tk.Label(left_frame, text="左键快捷键：").pack(anchor="w", padx=5)
    left_key_entry = tk.Entry(left_frame, width=15)
    left_key_entry.insert(0, '+'.join(left_key_combo).upper())
    left_key_entry.pack(fill="x", padx=5)
    left_key_entry.bind("<Return>", lambda e: save_settings(silent=True))
    left_key_entry.bind("<FocusOut>", lambda e: save_settings(silent=True))
    left_key_entry.bind("<Return>", lambda e: root.focus())

    tk.Label(left_frame, text="左键间隔（ms）：").pack(anchor="w", padx=5, pady=(8,0))
    left_interval_entry = tk.Entry(left_frame, width=15)
    left_interval_entry.insert(0, str(left_interval))
    left_interval_entry.pack(fill="x", padx=5)
    left_interval_entry.bind("<Return>", lambda e: save_settings(silent=True))
    left_interval_entry.bind("<FocusOut>", lambda e: save_settings(silent=True))
    left_interval_entry.bind("<Return>", lambda e: root.focus())

    tk.Label(left_frame, text="当前状态：").pack(anchor="w", padx=5, pady=(8,0))
    tk.Label(left_frame, textvariable=gui_left_state, fg='green').pack(anchor="w", padx=5)

    # ===== 右键区域 =====
    right_frame = tk.Frame(root)
    right_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

    tk.Label(right_frame, text="右键快捷键：").pack(anchor="w", padx=5)
    right_key_entry = tk.Entry(right_frame, width=15)
    right_key_entry.insert(0, '+'.join(right_key_combo).upper())
    right_key_entry.pack(fill="x", padx=5)
    right_key_entry.bind("<Return>", lambda e: save_settings(silent=True))
    right_key_entry.bind("<FocusOut>", lambda e: save_settings(silent=True))
    right_key_entry.bind("<Return>", lambda e: root.focus())

    tk.Label(right_frame, text="右键间隔（ms）：").pack(anchor="w", padx=5, pady=(8,0))
    right_interval_entry = tk.Entry(right_frame, width=15)
    right_interval_entry.insert(0, str(right_interval))
    right_interval_entry.pack(fill="x", padx=5)
    right_interval_entry.bind("<Return>", lambda e: save_settings(silent=True))
    right_interval_entry.bind("<FocusOut>", lambda e: save_settings(silent=True))
    right_interval_entry.bind("<Return>", lambda e: root.focus())

    tk.Label(right_frame, text="当前状态：").pack(anchor="w", padx=5, pady=(8,0))
    tk.Label(right_frame, textvariable=gui_right_state, fg='blue').pack(anchor="w", padx=5)

    # ===== 底部按钮区域 =====
    tk.Button(root, text="♻️ 恢复默认", command=restore_defaults).grid(row=2, column=0, pady=15)
    tk.Button(root, text="❌ 退出程序", command=root.destroy).grid(row=2, column=1, pady=15)

    # ===== 列宽配置 =====
    root.columnconfigure(0, weight=1, minsize=180)  # 最小宽度限制
    root.columnconfigure(1, weight=1, minsize=180)

    def remove_focus(event):
        widget = root.winfo_containing(event.x_root, event.y_root)
        if not isinstance(widget, tk.Entry):
            root.focus()
    root.bind("<Button-1>", remove_focus)

    apply_theme()
    threading.Thread(target=start_keyboard_listener, daemon=True).start()
    root.mainloop()


# 启动程序
if __name__ == "__main__":

    # 启动左右键点击线程
    left_thread = threading.Thread(target=left_click_loop, daemon=True)
    right_thread = threading.Thread(target=right_click_loop, daemon=True)
    left_thread.start()
    right_thread.start()

    # 启动GUI
    create_gui()