# -*- coding: utf-8 -*-
"""
Created on Mon Dec 15 09:58:16 2025
Modified for Pandas 2.0+ compatibility
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from tkcalendar import DateEntry
from datetime import datetime
import os
import sys

# =================================================================
# 核心應用程式類別
# =================================================================


class AccountLogApp:
    """一個使用 Tkinter 創建的簡單記帳日誌系統應用程式。"""

    def __init__(self, master):
        self.master = master
        master.title("Tkinter 記帳日誌系統")
        master.geometry("800x600")

        self.data_file = self.get_data_path("account_log.csv")
        self.df = self.load_data()

        self.setup_main_gui()

    # --- 數據處理與路徑修正 ---
    def get_data_path(self, relative_path):
        if getattr(sys, "frozen", False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(application_path, relative_path)

    def load_data(self):
        """
        [修正說明]
        針對 Pandas 2.0+ 版本進行修正。
        移除了 date_parser 參數，改為讀取後使用 pd.to_datetime 進行轉換。
        """
        try:
            # 1. 先讀取 CSV (不使用 date_parser)
            df = pd.read_csv(self.data_file)

            # 2. 手動將 '日期' 欄位轉換為 datetime 物件
            # errors='coerce' 代表如果遇到無法轉換的格式，將設為 NaT (空值)，避免報錯
            if "日期" in df.columns:
                df["日期"] = pd.to_datetime(df["日期"], errors="coerce")

            return df

        except FileNotFoundError:
            return pd.DataFrame(columns=["日期", "時間", "類別", "金額", "用途"])
        except Exception as e:
            messagebox.showerror(
                "資料載入錯誤", f"載入數據檔案時發生致命錯誤：{e}。\n將創建新的空檔案。"
            )
            return pd.DataFrame(columns=["日期", "時間", "類別", "金額", "用途"])

    def save_data(self):
        try:
            self.df.to_csv(self.data_file, index=False, encoding="utf-8-sig")
        except Exception as e:
            messagebox.showerror("儲存錯誤", f"儲存數據檔案時發生錯誤：{e}")

    # --- GUI 界面與操作 ---

    def setup_main_gui(self):
        """設置主視窗的介面佈局。"""

        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="記帳日誌總覽", font=("Helvetica", 16, "bold")).pack(
            pady=10
        )

        # 恢復主按鈕，並直接調用新增 GUI
        ttk.Button(main_frame, text="💰 新增記錄", command=self.add_record_gui).pack(
            pady=10
        )

        self.tree = ttk.Treeview(
            main_frame, columns=list(self.df.columns), show="headings"
        )
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor=tk.CENTER)

        self.tree.pack(fill="both", expand=True)

        self.refresh_treeview()

    def refresh_treeview(self):
        """清空 Treeview 並載入當前 DataFrame 中的數據。"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, row in self.df.iterrows():
            if pd.notna(row["日期"]):
                date_str = row["日期"].strftime("%Y-%m-%d")
            else:
                date_str = "日期無效"

            time_str = row["時間"] if pd.notna(row["時間"]) else ""

            try:
                money_str = f"{float(row['金額']):,}"
            except (ValueError, TypeError):
                money_str = "金額無效"

            self.tree.insert(
                "",
                tk.END,
                iid=idx,
                values=(date_str, time_str, row["類別"], money_str, row["用途"]),
            )

    def add_record_gui(self):
        """
        [修正核心] 創建新增記錄視窗，並定位在主視窗中央。
        """
        input_window = tk.Toplevel(self.master)
        input_window.title("新增記錄")

        # --- 核心修正：定位在主視窗中央 ---
        self.master.update_idletasks()

        win_width = 350
        win_height = 280

        # 計算主視窗中心點
        main_win_width = self.master.winfo_width()
        main_win_height = self.master.winfo_height()
        main_win_x = self.master.winfo_rootx()
        main_win_y = self.master.winfo_rooty()

        # 計算 Toplevel 視窗左上角的座標
        new_x = main_win_x + (main_win_width // 2) - (win_width // 2)
        new_y = main_win_y + (main_win_height // 2) - (win_height // 2)

        input_window.geometry(f"{win_width}x{win_height}+{new_x}+{new_y}")
        # ------------------------------------

        input_window.transient(self.master)
        input_window.grab_set()
        input_window.protocol(
            "WM_DELETE_WINDOW", lambda: self.close_input_window(input_window)
        )

        frame = ttk.Frame(input_window, padding="10")
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # === 界面元素定義與佈局 (保持不變) ===
        row_idx = 0

        ttk.Label(frame, text="日期:").grid(
            row=row_idx, column=0, padx=5, pady=5, sticky="w"
        )
        self.date_entry = DateEntry(
            frame,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="yyyy-mm-dd",
        )
        self.date_entry.set_date(datetime.now().date())
        self.date_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        ttk.Label(frame, text="時間 (HH:MM):").grid(
            row=row_idx, column=0, padx=5, pady=5, sticky="w"
        )
        self.time_entry = ttk.Entry(frame, width=15)
        self.time_entry.insert(0, datetime.now().strftime("%H:%M"))
        self.time_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        ttk.Label(frame, text="類別:").grid(
            row=row_idx, column=0, padx=5, pady=5, sticky="w"
        )
        categories = ["支出", "收入"]
        self.category_var = tk.StringVar(frame)
        self.category_combobox = ttk.Combobox(
            frame, textvariable=self.category_var, values=categories, state="readonly"
        )
        self.category_combobox.current(0)
        self.category_combobox.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        ttk.Label(frame, text="金額:").grid(
            row=row_idx, column=0, padx=5, pady=5, sticky="w"
        )
        self.money_entry = ttk.Entry(frame, width=15)
        self.money_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        ttk.Label(frame, text="用途/備註:").grid(
            row=row_idx, column=0, padx=5, pady=5, sticky="w"
        )
        self.usage_entry = ttk.Entry(frame, width=15)
        self.usage_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        self.status_label = ttk.Label(frame, text="", foreground="red")
        self.status_label.grid(row=row_idx, column=0, columnspan=2, pady=5)
        row_idx += 1

        # 提交按鈕
        self.submit_button = ttk.Button(
            frame, text="💾 確認", command=self.submit_new_record
        )
        self.submit_button.grid(
            row=row_idx, column=0, columnspan=2, pady=10, sticky="ew"
        )

        # 「確認」後，這個按鈕會顯示出來 (用於關閉連續新增視窗)
        self.close_button = ttk.Button(
            frame,
            text="❌ 關閉視窗",
            command=lambda: self.close_input_window(input_window),
        )
        self.close_button.grid(
            row=row_idx + 1, column=0, columnspan=2, pady=5, sticky="ew"
        )
        self.close_button.grid_remove()

        self.master.wait_window(input_window)

    def close_input_window(self, input_window):
        """釋放鎖定並銷毀 Toplevel 視窗。"""
        try:
            input_window.grab_release()
        except tk.TclError:
            pass
        input_window.destroy()

    def submit_new_record(self):
        """處理提交數據。確認後不關閉視窗，清除輸入框，進入連續新增模式。"""

        try:
            # 1. 數據獲取和驗證
            date_obj = self.date_entry.get_date()
            time_str = self.time_entry.get()
            category = self.category_var.get()
            money_val = self.money_entry.get()
            usage = self.usage_entry.get()

            if not usage or not usage.strip():
                raise ValueError("用途欄位不能為空。")

            try:
                money = float(money_val)
            except ValueError:
                raise ValueError("金額必須是數字。")

            if money <= 0:
                raise ValueError("金額必須大於零。")

            # 2. 數據處理
            new_record = {
                "日期": date_obj,
                "時間": time_str,
                "類別": category,
                "金額": money,
                "用途": usage,
            }

            self.df.loc[len(self.df)] = new_record
            self.save_data()
            self.refresh_treeview()

            # 3. 流程結束邏輯：連續新增模式
            self.status_label.config(
                text=f"✅ 新增成功！金額: {money:,}，請繼續輸入下一筆。",
                foreground="green",
            )

            self.money_entry.delete(0, tk.END)
            self.usage_entry.delete(0, tk.END)

            self.money_entry.focus_set()

            self.close_button.grid()

        except ValueError as e:
            self.status_label.config(text=f"錯誤: {e}", foreground="red")
        except Exception as e:
            self.status_label.config(text=f"發生未知錯誤: {e}", foreground="red")


# =================================================================
# 主程式運行區塊
# =================================================================

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AccountLogApp(root)
        root.mainloop()
    except Exception as e:
        print(f"程式啟動時發生致命錯誤: {e}")
