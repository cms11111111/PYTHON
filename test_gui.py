import tkinter as tk
from tkinter import messagebox
import sys

print("正在啟動 Tkinter 測試...", file=sys.stderr)

def on_click():
    print("按鈕被點擊了！")
    messagebox.showinfo("成功", "恭喜！您終於看到視窗了！\nPython 版本: " + sys.version)

try:
    root = tk.Tk()
    root.title("最終測試")
    root.geometry("300x200")

    label = tk.Label(root, text="如果您看到這個視窗\n代表 Python GUI 是正常的", font=("Arial", 12), pady=20)
    label.pack()

    btn = tk.Button(root, text="點我測試", command=on_click, font=("Arial", 14), bg="blue", fg="white")
    btn.pack(pady=20)

    print("視窗主迴圈開始...", file=sys.stderr)
    root.mainloop()
    print("視窗已關閉", file=sys.stderr)

except Exception as e:
    print(f"嚴重錯誤: {e}", file=sys.stderr)
    input("按 Enter 鍵結束...")
