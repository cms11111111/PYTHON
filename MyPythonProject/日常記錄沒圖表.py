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
    print("請執行 'pip install tkcalendar pandas' 安裝必要套件")
    sys.exit()

class AccountLogApp:
    def __init__(self, master):
        self.master = master
        self.master.title("財務預算管理系統")
        self.master.geometry("1000x850") # 調整寬度
        
        self.cols = ('日期', '時間', '類別', '金額', '用途', '本月預算', '累計支出', '預算剩餘')
        self.data_file = self.get_data_path('account_log.csv')
        self.budget_file = self.get_data_path('budgets.csv')
        
        self.df = self.load_data()
        self.budget_df = self.load_budget_data()
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
                return pd.DataFrame(columns=self.cols)
        return pd.DataFrame(columns=self.cols)

    def load_budget_data(self):
        if os.path.exists(self.budget_file):
            try:
                return pd.read_csv(self.budget_file, encoding='utf-8-sig')
            except:
                return pd.DataFrame(columns=['月份', '金額'])
        return pd.DataFrame(columns=['月份', '金額'])

    def save_data(self):
        self.df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
        self.budget_df.to_csv(self.budget_file, index=False, encoding='utf-8-sig')

    def get_monthly_budget(self, target_month_str):
        if self.budget_df.empty: return 0.0
        # 確保型別一致
        self.budget_df["月份"] = self.budget_df["月份"].astype(str)
        match = self.budget_df[self.budget_df['月份'] == target_month_str]
        if not match.empty: return float(match.iloc[0]['金額'])
        past_budgets = self.budget_df[self.budget_df['月份'] < target_month_str]
        if not past_budgets.empty:
            past_budgets = past_budgets.sort_values(by='月份', ascending=False)
            return float(past_budgets.iloc[0]['金額'])
        return 0.0

    def setup_main_gui(self):
        main_frame = ttk.Frame(self.master, padding="15")
        main_frame.pack(fill='both', expand=True)

        top_bar = ttk.Frame(main_frame)
        top_bar.pack(fill='x', pady=(0, 10))
        ttk.Label(top_bar, text="💰 財務預算管理系統 (連續輸入)", font=("Microsoft JhengHei", 18, "bold")).pack(side=tk.LEFT)
        
        btn_group = ttk.Frame(top_bar)
        btn_group.pack(side=tk.RIGHT)
        ttk.Button(btn_group, text="🎯 設定月預算", command=self.budget_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_group, text="➕ 新增記錄", command=self.record_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_group, text="🗑️ 刪除選取", command=self.delete_record).pack(side=tk.LEFT, padx=5)

        filter_frame = ttk.LabelFrame(main_frame, text="🔍 篩選與統計", padding="10")
        filter_frame.pack(fill='x', pady=(0, 15))
        self.start_date_ent = DateEntry(filter_frame, width=12, background='darkblue', date_pattern='yyyy-mm-dd')
        self.start_date_ent.pack(side=tk.LEFT, padx=5)
        self.end_date_ent = DateEntry(filter_frame, width=12, background='darkblue', date_pattern='yyyy-mm-dd')
        self.end_date_ent.pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="套用查詢", command=self.apply_filter).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_frame, text="回到當月", command=self.show_current_month).pack(side=tk.LEFT)

        self.summary_box = ttk.LabelFrame(main_frame, text="📊 財務摘要", padding="15")
        self.summary_box.pack(fill='x', pady=(0, 15))
        self.lbl_month = ttk.Label(self.summary_box, text="月份: --", font=("Microsoft JhengHei", 11))
        self.lbl_month.grid(row=0, column=0, padx=20)
        self.lbl_budget = ttk.Label(self.summary_box, text="預算: $0", font=("Microsoft JhengHei", 12, "bold"))
        self.lbl_budget.grid(row=0, column=1, padx=20)
        self.lbl_spent = ttk.Label(self.summary_box, text="支出: $0", font=("Microsoft JhengHei", 12, "bold"), foreground="red")
        self.lbl_spent.grid(row=0, column=2, padx=20)
        self.lbl_remain = ttk.Label(self.summary_box, text="剩餘: $0", font=("Microsoft JhengHei", 14, "bold"), foreground="green")
        self.lbl_remain.grid(row=0, column=3, padx=20)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill='both', expand=True)
        # 移除原有的多欄配置，改為單欄
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        table_container = ttk.Frame(content_frame)
        # 讓表格填滿整個寬度
        table_container.grid(row=0, column=0, sticky='nsew', padx=0)
        
        self.tree = ttk.Treeview(table_container, columns=self.cols, show='headings', selectmode="browse")
        for col in self.cols:
            self.tree.heading(col, text=col)
            anchor = tk.E if col in ['金額', '本月預算', '累計支出', '預算剩餘'] else tk.CENTER
            self.tree.column(col, width=95, anchor=anchor)
        self.tree.column('用途', width=130)

        scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill='both', expand=True)
        scrollbar.pack(side=tk.RIGHT, fill='y')

        self.show_current_month()

    def refresh_treeview(self, display_df=None):
        data = self.df if display_df is None else display_df
        for item in self.tree.get_children(): self.tree.delete(item)
        data_sorted = data.sort_values(by=['日期', '時間'], ascending=False)
        
        total_out = 0
        ref_month = self.start_date_ent.get_date().strftime("%Y-%m")
        # 計算篩選區間內的總支出
        for idx, row in data_sorted.iterrows():
            self.tree.insert('', tk.END, iid=idx, values=(
                row['日期'], row['時間'], row['類別'], f"{float(row['金額']):,.0f}", row['用途'],
                f"{float(row.get('本月預算',0)):,.0f}", f"{float(row.get('累計支出',0)):,.0f}", f"{float(row.get('預算剩餘',0)):,.0f}"
            ))
            # 同時動態統計當月支出
            if str(row['日期'])[:7] == ref_month and row['類別'] == '支出':
                total_out += float(row['金額'])

        budget = self.get_monthly_budget(ref_month)
        remaining = budget - total_out
        self.lbl_month.config(text=f"統計月份: {ref_month}")
        self.lbl_budget.config(text=f"本月預算: ${budget:,.0f}")
        self.lbl_spent.config(text=f"累計支出: ${total_out:,.0f}")
        self.lbl_remain.config(text=f"預算剩餘: ${remaining:,.0f}", foreground="red" if remaining < 0 else "green")

    def record_window(self):
        # 建立視窗
        win = tk.Toplevel(self.master); win.title("連續新增模式"); win.geometry("400x620"); win.grab_set()
        frm = ttk.Frame(win, padding=20); frm.pack(fill='both')
        
        # 欄位
        ttk.Label(frm, text="日期:").grid(row=0, column=0, sticky='w', pady=5)
        de = DateEntry(frm, width=15, date_pattern='yyyy-mm-dd'); de.grid(row=0, column=1, sticky='w')
        
        ttk.Label(frm, text="類別:").grid(row=1, column=0, sticky='w', pady=5)
        cat_var = tk.StringVar(value="支出")
        ttk.Combobox(frm, textvariable=cat_var, values=["支出", "收入"], state="readonly", width=14).grid(row=1, column=1, sticky='w')
        
        ttk.Label(frm, text="金額:").grid(row=2, column=0, sticky='w', pady=5)
        amt_en = ttk.Entry(frm, width=17); amt_en.grid(row=2, column=1, sticky='w')
        
        ttk.Label(frm, text="用途:").grid(row=3, column=0, sticky='nw', pady=5)
        note_en = ttk.Entry(frm, width=17); note_en.grid(row=3, column=1, sticky='w')

        # 快速標籤
        tag_frame = ttk.Frame(frm)
        tag_frame.grid(row=4, column=0, columnspan=2, pady=10)
        def add_tag(t):
            note_en.delete(0, tk.END); note_en.insert(0, t); note_en.focus()
        tags = ["食", "衣", "住", "行", "育", "樂", "其他"]
        for i, t in enumerate(tags):
            ttk.Button(tag_frame, text=t, width=4, command=lambda x=t: add_tag(x)).grid(row=i//4, column=i%4, padx=2, pady=2)

        # 狀態顯示提示
        st_var = tk.StringVar(value="準備就緒")
        st_lbl = tk.Label(frm, textvariable=st_var, fg="blue", font=("微軟正黑體", 10))
        st_lbl.grid(row=5, columnspan=2, pady=10)

        def save(event=None): # 加入 event 參數支援鍵盤 Enter
            try:
                amt = float(amt_en.get())
                ref_m = de.get_date().strftime("%Y-%m")
                budget = self.get_monthly_budget(ref_m)
                
                # 計算即時累計
                temp = self.df.copy()
                if not temp.empty:
                    temp['日期'] = pd.to_datetime(temp['日期'])
                    mask = (temp['日期'].dt.strftime('%Y-%m') == ref_m) & (temp['類別'] == '支出')
                    current_out = temp.loc[mask, '金額'].sum() + (amt if cat_var.get() == '支出' else 0)
                else:
                    current_out = amt if cat_var.get() == '支出' else 0

                new_rec = {
                    '日期': de.get_date(), '時間': datetime.now().strftime("%H:%M"),
                    '類別': cat_var.get(), '金額': amt, '用途': note_en.get().strip(),
                    '本月預算': budget, '累計支出': current_out, '預算剩餘': budget - current_out
                }
                
                self.df = pd.concat([self.df, pd.DataFrame([new_rec])], ignore_index=True)
                self.save_data()
                self.refresh_treeview()
                
                # --- 連續輸入核心邏輯 ---
                st_var.set(f"✅ 已成功儲存: {note_en.get().strip()} ${amt}")
                st_lbl.config(fg="green")
                
                # 清空輸入框
                amt_en.delete(0, tk.END)
                note_en.delete(0, tk.END)
                # 重新聚焦到金額，方便輸入下一筆
                amt_en.focus()
                
            except ValueError:
                st_var.set("❌ 錯誤: 金額請輸入數字")
                st_lbl.config(fg="red")

        # 儲存按鈕
        save_btn = ttk.Button(frm, text="儲存並繼續下一筆 (Enter)", command=save)
        save_btn.grid(row=6, columnspan=2, pady=10, sticky='ew')
        
        # 綁定 Enter 鍵，在金額或用途欄位按 Enter 都會觸發儲存
        amt_en.bind('<Return>', save)
        note_en.bind('<Return>', save)
        
        # 視窗開啟時自動聚焦金額
        amt_en.focus()

    def budget_window(self):
        win = tk.Toplevel(self.master); win.title("設定預算"); win.geometry("300x200"); win.grab_set()
        frm = ttk.Frame(win, padding=20); frm.pack()
        mon_en = ttk.Entry(frm); mon_en.insert(0, datetime.now().strftime("%Y-%m")); mon_en.pack(pady=5)
        amt_en = ttk.Entry(frm); amt_en.pack(pady=5)
        def save():
            m, a = mon_en.get().strip(), float(amt_en.get())
            if m in self.budget_df['月份'].values: self.budget_df.loc[self.budget_df['月份'] == m, '金額'] = a
            else: self.budget_df = pd.concat([self.budget_df, pd.DataFrame([{'月份':m, '金額':a}])], ignore_index=True)
            self.save_data(); self.refresh_treeview(); win.destroy()
        ttk.Button(frm, text="確認設定", command=save).pack()

    def show_current_month(self):
        today = datetime.now().date()
        self.start_date_ent.set_date(today.replace(day=1))
        self.end_date_ent.set_date(today); self.apply_filter()

    def apply_filter(self):
        start, end = self.start_date_ent.get_date(), self.end_date_ent.get_date()
        mask = (self.df['日期'] >= start) & (self.df['日期'] <= end)
        self.refresh_treeview(self.df[mask])

    def delete_record(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("確認", "確定要刪除這筆紀錄嗎？"):
            self.df = self.df.drop(int(sel[0])).reset_index(drop=True)
            self.save_data(); self.refresh_treeview()

if __name__ == '__main__':
    root = tk.Tk(); ttk.Style().theme_use('clam')
    app = AccountLogApp(root); root.mainloop()