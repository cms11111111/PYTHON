# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from datetime import datetime
import os
import sys

try:
    from tkcalendar import DateEntry
except ImportError:
    print("請執行 'pip install tkcalendar' 安裝必要套件")
    sys.exit()

class AccountLogApp:
    def __init__(self, master):
        self.master = master
        self.master.title("進階記帳系統 - 支援日期範圍查詢")
        self.master.geometry("950x700") # 稍微調寬高度以容納篩選列
        
        self.data_file = self.get_data_path('account_log.csv')
        self.df = self.load_data()
        
        self.setup_main_gui()

    def get_data_path(self, relative_path):
        if getattr(sys, 'frozen', False):
            path = os.path.dirname(sys.executable)
        else:
            path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(path, relative_path)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                df = pd.read_csv(self.data_file, encoding='utf-8-sig')
                df['日期'] = pd.to_datetime(df['日期']).dt.date
                return df
            except:
                return pd.DataFrame(columns=['日期', '時間', '類別', '金額', '用途'])
        return pd.DataFrame(columns=['日期', '時間', '類別', '金額', '用途'])

    def save_data(self):
        self.df.to_csv(self.data_file, index=False, encoding='utf-8-sig')

    def setup_main_gui(self):
        main_frame = ttk.Frame(self.master, padding="15")
        main_frame.pack(fill='both', expand=True)

        # --- 1. 頂部操作列 ---
        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill='x', pady=(0, 5))
        
        ttk.Label(top_bar, text="💰 收支管理系統", font=("Microsoft JhengHei", 14, "bold")).pack(side=tk.LEFT)
        
        btn_group = ttk.Frame(top_bar)
        btn_group.pack(side=tk.RIGHT)
        ttk.Button(btn_group, text="➕ 新增記錄", command=lambda: self.record_window("add")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_group, text="🗑️ 刪除選取", command=self.delete_record).pack(side=tk.LEFT, padx=5)

        # --- 2. 查詢篩選列 (新增區塊) ---
        filter_frame = ttk.LabelFrame(main_frame, text="🔍 日期範圍查詢", padding="10")
        filter_frame.pack(fill='x', pady=10)

        ttk.Label(filter_frame, text="從:").pack(side=tk.LEFT, padx=5)
        self.start_date_ent = DateEntry(filter_frame, width=12, background='darkblue', date_pattern='yyyy-mm-dd')
        self.start_date_ent.pack(side=tk.LEFT, padx=5)

        ttk.Label(filter_frame, text="至:").pack(side=tk.LEFT, padx=5)
        self.end_date_ent = DateEntry(filter_frame, width=12, background='darkblue', date_pattern='yyyy-mm-dd')
        self.end_date_ent.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="開始查詢", command=self.apply_filter).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="重置/顯示全部", command=self.refresh_treeview).pack(side=tk.LEFT)

        # --- 3. 表格顯示區 ---
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill='both', expand=True)

        cols = ('日期', '時間', '類別', '金額', '用途')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', selectmode="browse")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        self.tree.column('用途', width=350)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')

        self.tree.bind("<Double-1>", self.on_double_click)

        self.stat_label = ttk.Label(main_frame, text="", font=("Microsoft JhengHei", 11, "bold"))
        self.stat_label.pack(side=tk.RIGHT, pady=10)

        self.refresh_treeview()

    def apply_filter(self):
        """執行日期篩選邏輯"""
        start = self.start_date_ent.get_date()
        end = self.end_date_ent.get_date()
        
        if start > end:
            messagebox.showwarning("提示", "開始日期不能大於結束日期")
            return

        # 使用 Pandas 進行篩選
        mask = (self.df['日期'] >= start) & (self.df['日期'] <= end)
        filtered_df = self.df[mask]
        
        # 呼叫刷新方法，但傳入篩選後的結果
        self.refresh_treeview(filtered_df)

    def refresh_treeview(self, display_df=None):
        """將資料繪製到表格。若無傳入 display_df，預設顯示全部自 self.df"""
        # 如果沒有指定要顯示哪份資料，就顯示全部
        if display_df is None:
            data = self.df
        else:
            data = display_df

        # 清空舊資料
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_in, total_out = 0, 0
        # 排序 (以傳入的資料進行排序)
        data = data.sort_values(by=['日期', '時間'], ascending=False)

        for idx, row in data.iterrows():
            amt = float(row['金額'])
            if row['類別'] == '收入': total_in += amt
            else: total_out += amt

            self.tree.insert('', tk.END, iid=idx, values=(
                row['日期'], row['時間'], row['類別'], f"{amt:,.0f}", row['用途']
            ))

        # 更新統計資訊
        self.stat_label.config(text=f"篩選統計 -> 總收入: {total_in:,.0f} | 總支出: {total_out:,.0f} | 結餘: {(total_in-total_out):,.0f}")

    # --- 以下其餘方法保持不變 ---
    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請選取要刪除的記錄")
            return
        if messagebox.askyesno("確認", "確定要刪除選中的記錄嗎？"):
            self.df = self.df.drop(int(selected[0])).reset_index(drop=True)
            self.save_data()
            self.refresh_treeview()

    def on_double_click(self, event):
        selected = self.tree.selection()
        if selected:
            self.record_window("edit", selected[0])

    def record_window(self, mode="add", item_id=None):
        win_title = "新增記錄" if mode == "add" else "修改記錄"
        win = tk.Toplevel(self.master)
        win.title(win_title)
        win.geometry("320x420")
        win.grab_set()

        frm = ttk.Frame(win, padding=20)
        frm.pack(fill='both')

        ttk.Label(frm, text="日期:").grid(row=0, column=0, pady=5, sticky='w')
        de = DateEntry(frm, width=15, background='darkblue', date_pattern='yyyy-mm-dd')
        de.grid(row=0, column=1, pady=5)

        ttk.Label(frm, text="類別:").grid(row=1, column=0, pady=5, sticky='w')
        cat_var = tk.StringVar(value="支出")
        cb = ttk.Combobox(frm, textvariable=cat_var, values=["支出", "收入"], state="readonly", width=14)
        cb.grid(row=1, column=1, pady=5)

        ttk.Label(frm, text="金額:").grid(row=2, column=0, pady=5, sticky='w')
        amt_en = ttk.Entry(frm, width=17)
        amt_en.grid(row=2, column=1, pady=5)

        ttk.Label(frm, text="用途:").grid(row=3, column=0, pady=5, sticky='w')
        note_en = ttk.Entry(frm, width=17)
        note_en.grid(row=3, column=1, pady=5)

        status_msg = tk.Label(frm, text="", fg="blue", font=("Arial", 9))
        status_msg.grid(row=4, column=0, columnspan=2, pady=5)

        if mode == "edit":
            old_data = self.df.iloc[int(item_id)]
            de.set_date(old_data['日期'])
            cat_var.set(old_data['類別'])
            amt_en.insert(0, str(int(old_data['金額'])))
            note_en.insert(0, old_data['用途'])

        def save_action(event=None):
            try:
                amt = float(amt_en.get())
                note = note_en.get().strip()
                if not note: raise ValueError
                
                new_row = {
                    '日期': de.get_date(),
                    '時間': datetime.now().strftime("%H:%M") if mode == "add" else self.df.iloc[int(item_id)]['時間'],
                    '類別': cat_var.get(),
                    '金額': amt,
                    '用途': note
                }
                
                if mode == "add":
                    self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)
                    amt_en.delete(0, tk.END)
                    note_en.delete(0, tk.END)
                    amt_en.focus()
                    status_msg.config(text="✅ 已儲存", fg="green")
                else:
                    self.df.iloc[int(item_id)] = new_row
                    self.save_data()
                    self.refresh_treeview()
                    win.destroy()
                    return

                self.save_data()
                self.refresh_treeview()
            except ValueError:
                status_msg.config(text="❌ 請輸入有效金額與備註", fg="red")

        note_en.bind('<Return>', save_action)
        ttk.Button(frm, text="💾 儲存", command=save_action).grid(row=5, column=0, columnspan=2, pady=10, sticky='ew')
        ttk.Button(frm, text="🚪 關閉", command=win.destroy).grid(row=6, column=0, columnspan=2, sticky='ew')
        amt_en.focus()

if __name__ == '__main__':
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = AccountLogApp(root)
    root.mainloop()