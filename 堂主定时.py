# -*- coding: utf-8 -*-
"""堂主定时：按 Windows 系统时间执行一次鼠标单击或双击。"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pyautogui
from PIL import Image, ImageTk

APP_TITLE = "堂主定时"
APP_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))

def asset_path(name):
    base = getattr(sys, "_MEIPASS", APP_DIR)
    return os.path.join(base, name)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("570x620")
        self.root.minsize(520, 570)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)
        self._set_icon()
        self.target_dt = None
        self.running = False
        self.paused = False
        self.after_id = None
        self.picker = None
        self.picker_photo = None
        self.remaining = 0
        self.x_var = tk.StringVar(value=str(pyautogui.position().x))
        self.y_var = tk.StringVar(value=str(pyautogui.position().y))
        self.button_var = tk.StringVar(value="左键")
        self.mode_var = tk.StringVar(value="单击")
        now = datetime.now()
        self.date_var = tk.StringVar(value=now.strftime("%Y-%m-%d"))
        self.time_var = tk.StringVar(value=(now.replace(second=0, microsecond=0)).strftime("%H:%M:%S"))
        self.status_var = tk.StringVar(value="状态：等待设置")
        self.countdown_var = tk.StringVar(value="剩余时间：--:--:--")
        self._build_ui()
        self.root.bind("<Escape>", self._escape_picker)

    def _set_icon(self):
        try:
            self.root.iconbitmap(asset_path("icon.ico"))
        except Exception:
            pass

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=APP_TITLE, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="center", pady=(0, 4))
        ttk.Label(outer, text="按电脑系统时间，到点后执行一次鼠标操作", foreground="#555").pack(anchor="center", pady=(0, 16))

        timebox = ttk.LabelFrame(outer, text=" 触发时间（使用 Windows 系统时间） ", padding=12)
        timebox.pack(fill="x", pady=5)
        row = ttk.Frame(timebox); row.pack(fill="x", pady=4)
        ttk.Label(row, text="日期 (YYYY-MM-DD)", width=20).pack(side="left")
        ttk.Entry(row, textvariable=self.date_var, width=18).pack(side="left", padx=4)
        row = ttk.Frame(timebox); row.pack(fill="x", pady=4)
        ttk.Label(row, text="时间 (HH:MM:SS)", width=20).pack(side="left")
        ttk.Entry(row, textvariable=self.time_var, width=18).pack(side="left", padx=4)
        ttk.Label(timebox, text="例如：2026-10-23 14:30:00", foreground="#666").pack(anchor="w", pady=(3, 0))

        coordbox = ttk.LabelFrame(outer, text=" 点击位置 ", padding=12)
        coordbox.pack(fill="x", pady=5)
        row = ttk.Frame(coordbox); row.pack(fill="x", pady=4)
        ttk.Label(row, text="X 坐标").pack(side="left")
        ttk.Entry(row, textvariable=self.x_var, width=9).pack(side="left", padx=(6, 16))
        ttk.Label(row, text="Y 坐标").pack(side="left")
        ttk.Entry(row, textvariable=self.y_var, width=9).pack(side="left", padx=6)
        ttk.Button(row, text="选择屏幕位置…", command=self.open_picker).pack(side="right")
        ttk.Label(coordbox, text="选择位置时会显示桌面截图；单击目标位置即可记录坐标。", foreground="#666", wraplength=500).pack(anchor="w", pady=(3, 0))

        opbox = ttk.LabelFrame(outer, text=" 鼠标操作 ", padding=12)
        opbox.pack(fill="x", pady=5)
        row = ttk.Frame(opbox); row.pack(fill="x", pady=4)
        ttk.Label(row, text="鼠标按键").pack(side="left")
        ttk.Combobox(row, textvariable=self.button_var, values=["左键", "右键", "中键"], state="readonly", width=9).pack(side="left", padx=(6, 18))
        ttk.Label(row, text="点击方式").pack(side="left")
        ttk.Combobox(row, textvariable=self.mode_var, values=["单击", "双击"], state="readonly", width=9).pack(side="left", padx=6)
        ttk.Button(row, text="测试点击", command=self.test_click).pack(side="right")

        ttk.Label(outer, textvariable=self.countdown_var, font=("Microsoft YaHei UI", 14, "bold")).pack(pady=(12, 4))
        ttk.Label(outer, textvariable=self.status_var, wraplength=500).pack(pady=3)
        row = ttk.Frame(outer); row.pack(fill="x", pady=(12, 0))
        self.start_btn = ttk.Button(row, text="开始定时", command=self.start)
        self.start_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.pause_btn = ttk.Button(row, text="暂停", command=self.pause, state="disabled")
        self.pause_btn.pack(side="left", expand=True, fill="x", padx=5)
        self.cancel_btn = ttk.Button(row, text="取消任务", command=self.cancel, state="disabled")
        self.cancel_btn.pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(row, text="退出", command=self.close_app).pack(side="left", expand=True, fill="x", padx=(5, 0))
        ttk.Label(outer, text="提示：测试点击会立即操作指定位置。鼠标移到左上角可触发 PyAutoGUI 紧急停止。", foreground="#777", wraplength=500).pack(anchor="w", pady=(12, 0))

    def _coords(self):
        try:
            x, y = int(self.x_var.get().strip()), int(self.y_var.get().strip())
            if x < 0 or y < 0 or x >= pyautogui.size().width or y >= pyautogui.size().height:
                raise ValueError
            return x, y
        except Exception:
            raise ValueError("坐标无效，请填写屏幕范围内的整数 X、Y 坐标。")

    def _button(self):
        return {"左键": "left", "右键": "right", "中键": "middle"}[self.button_var.get()]

    def perform_click(self):
        x, y = self._coords()
        btn = self._button()
        if self.mode_var.get() == "双击":
            pyautogui.doubleClick(x=x, y=y, button=btn, interval=0.12)
        else:
            pyautogui.click(x=x, y=y, button=btn)
        return x, y

    def test_click(self):
        try:
            x, y = self.perform_click()
            self.status_var.set(f"状态：测试完成，已在 ({x}, {y}) 执行{self.mode_var.get()}")
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"测试点击失败：\n{e}")

    def start(self):
        if self.running:
            return
        try:
            x, y = self._coords()
            target = datetime.strptime(self.date_var.get().strip() + " " + self.time_var.get().strip(), "%Y-%m-%d %H:%M:%S")
            if target <= datetime.now():
                messagebox.showwarning(APP_TITLE, "设定时间必须晚于当前电脑系统时间。")
                return
        except Exception as e:
            messagebox.showerror(APP_TITLE, f"请检查日期、时间和坐标格式。\n{e}")
            return
        self.target_dt = target
        self.running = True
        self.paused = False
        self.status_var.set(f"状态：已启动，目标时间 {target.strftime('%Y-%m-%d %H:%M:%S')}，位置 ({x}, {y})")
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal", text="暂停")
        self.cancel_btn.configure(state="normal")
        self._tick()

    def _tick(self):
        if not self.running or self.paused:
            return
        now = datetime.now()
        seconds = max(0, (self.target_dt - now).total_seconds())
        total = int(seconds)
        h, rem = divmod(total, 3600); m, s = divmod(rem, 60)
        self.countdown_var.set(f"剩余时间：{h:02d}:{m:02d}:{s:02d}")
        if now >= self.target_dt:
            self.after_id = None
            try:
                x, y = self.perform_click()
                self.running = False
                self.status_var.set(f"状态：执行成功，位置 ({x}, {y})。程序即将关闭。")
                self.countdown_var.set("剩余时间：00:00:00")
                self.root.after(900, self.close_app)
                return
            except Exception as e:
                self.running = False
                self._reset_buttons()
                self.status_var.set("状态：执行失败")
                messagebox.showerror(APP_TITLE, f"定时点击失败，程序不会自动关闭。\n{e}")
                return
        self.after_id = self.root.after(100, self._tick)

    def pause(self):
        if not self.running:
            return
        if not self.paused:
            self.remaining = max(0, (self.target_dt - datetime.now()).total_seconds())
            self.paused = True
            if self.after_id:
                self.root.after_cancel(self.after_id); self.after_id = None
            self.pause_btn.configure(text="继续")
            self.status_var.set("状态：已暂停")
        else:
            if self.remaining <= 0:
                messagebox.showinfo(APP_TITLE, "剩余时间已结束，请重新设置任务。")
                self.cancel()
                return
            from datetime import timedelta
            self.target_dt = datetime.now() + timedelta(seconds=self.remaining)
            self.paused = False
            self.pause_btn.configure(text="暂停")
            self.status_var.set("状态：已继续倒计时")
            self._tick()

    def _reset_buttons(self):
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="暂停")
        self.cancel_btn.configure(state="disabled")

    def cancel(self):
        self.running = False; self.paused = False
        if self.after_id:
            try: self.root.after_cancel(self.after_id)
            except Exception: pass
            self.after_id = None
        self._reset_buttons()
        self.countdown_var.set("剩余时间：--:--:--")
        self.status_var.set("状态：任务已取消")

    def open_picker(self):
        if self.picker is not None:
            return
        try:
            shot = pyautogui.screenshot()
            self.root.withdraw()
            overlay = tk.Toplevel(self.root)
            self.picker = overlay
            overlay.overrideredirect(True)
            overlay.attributes("-topmost", True)
            overlay.geometry(f"{shot.width}x{shot.height}+0+0")
            photo = ImageTk.PhotoImage(shot)
            self.picker_photo = photo
            canvas = tk.Canvas(overlay, width=shot.width, height=shot.height, highlightthickness=0, cursor="crosshair")
            canvas.pack(fill="both", expand=True)
            canvas.create_image(0, 0, image=photo, anchor="nw")
            canvas.create_rectangle(12, 12, 570, 65, fill="#111111", outline="#ffffff", width=1)
            canvas.create_text(25, 25, anchor="nw", fill="white", font=("Microsoft YaHei UI", 13, "bold"),
                               text="单击你要点击的位置；按 Esc 取消选择")
            canvas.create_text(25, 47, anchor="nw", fill="white", font=("Microsoft YaHei UI", 10),
                               text="注意：这是桌面截图，点击后只记录坐标，不会真的点击目标")
            canvas.bind("<Button-1>", self._picker_click)
            overlay.bind("<Escape>", self._escape_picker)
            overlay.focus_force()
        except Exception as e:
            self.close_picker()
            messagebox.showerror(APP_TITLE, f"无法打开屏幕位置选择器：\n{e}")

    def _picker_click(self, event):
        self.x_var.set(str(event.x)); self.y_var.set(str(event.y))
        self.close_picker()
        self.status_var.set(f"状态：已选择坐标 ({event.x}, {event.y})")

    def _escape_picker(self, _event=None):
        if self.picker is not None:
            self.close_picker()
            self.status_var.set("状态：已取消位置选择")

    def close_picker(self):
        if self.picker is not None:
            try: self.picker.destroy()
            except Exception: pass
            self.picker = None
        self.picker_photo = None
        try: self.root.deiconify(); self.root.lift()
        except Exception: pass

    def close_app(self):
        self.cancel()
        self.close_picker()
        self.root.destroy()

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
