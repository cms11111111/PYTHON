import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import threading
import pandas as pd
import datetime
import os
import time

# 設定檔案名稱
PORTFOLIO_FILE = "stock_portfolio.xlsx"
HISTORY_FILE = "stock_daily_history.xlsx"

file_lock = threading.Lock()

class StockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("台股損益管理 (漲紅跌綠版)")
        self.root.geometry("1150x650")
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        font=("Microsoft JhengHei", 10), 
                        rowheight=30)
        style.configure("Treeview.Heading", 
                        font=("Microsoft JhengHei", 10, "bold"))
        
        self.setup_ui()
        self.load_from_excel()

    def setup_ui(self):
        ctrl_frame = ttk.Frame(self.root, padding="15")
        ctrl_frame.pack(fill="x")
        
        input_inner = ttk.Frame(ctrl_frame)
        input_inner.pack()

        self.entries = {}
        fields = [("代碼:", "sym"), ("每股成本:", "cost"), ("總股數:", "qty")]
        for i, (lab, key) in enumerate(fields):
            ttk.Label(input_inner, text=lab).grid(row=0, column=i*2, padx=5)
            ent = ttk.Entry(input_inner, width=12)
            ent.grid(row=0, column=i*2+1, padx=10)
            self.entries[key] = ent

        ttk.Button(input_inner, text="查詢/存檔", command=self.fetch_stock).grid(row=0, column=6, padx=5)
        self.btn_all = ttk.Button(input_inner, text="🔄 全部更新", command=self.update_all_stocks)
        self.btn_all.grid(row=0, column=7, padx=5)
        ttk.Button(input_inner, text="刪除選取", command=self.delete_record).grid(row=0, column=8, padx=5)
        ttk.Button(input_inner, text="📂 歷史紀錄", command=self.open_history_file).grid(row=0, column=9, padx=5)

        table_frame = ttk.Frame(self.root, padding="10")
        table_frame.pack(fill="both", expand=True)

        self.cols = {
            "time": ("最後更新時間", 120),
            "symbol": ("股票代碼", 80),
            "name": ("股票名稱", 150),
            "price": ("目前成交價", 90),
            "change": ("今日漲跌", 80),
            "pct": ("漲跌幅%", 80), # 目標欄位
            "qty": ("持有股數", 100),
            "cost": ("購買成本", 100),
            "diff": ("總損益", 120),
            "roi": ("報酬率%", 90)
        }

        self.tree = ttk.Treeview(table_frame, columns=list(self.cols.keys()), show="headings")
        
        for col_id, (name, width) in self.cols.items():
            self.tree.heading(col_id, text=name)
            align = "e" if col_id in ["price", "change", "pct", "qty", "cost", "diff", "roi"] else "center"
            self.tree.column(col_id, width=width, anchor=align)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # --- 重要：設定顏色標籤 (台灣標配：漲紅跌綠) ---
        self.tree.tag_configure("up", foreground="#FF0000")   # 紅色
        self.tree.tag_configure("down", foreground="#008000") # 綠色
        self.tree.tag_configure("even", foreground="black")   # 平盤

    def fetch_stock(self):
        sym = self.entries["sym"].get().strip().upper()
        if not sym: return
        threading.Thread(target=self.query_logic, args=(sym, self.entries["cost"].get(), self.entries["qty"].get()), daemon=True).start()

    def query_logic(self, raw_s, cost_in, qty_in, is_auto=False):
        try:
            candidates = [raw_s] if ".TW" in raw_s else [f"{raw_s}.TWO", f"{raw_s}.TW"] 
            
            found = False
            for sym in candidates:
                ticker = yf.Ticker(sym)
                df = ticker.history(period="5d")
                
                if not df.empty:
                    p = float(df['Close'].iloc[-1])
                    prev = float(df['Close'].iloc[-2]) if len(df) > 1 else p
                    
                    # 計算今日漲跌狀況
                    raw_change = p - prev
                    
                    e_cost, e_qty = self.get_portfolio_data(sym)
                    f_cost = float(cost_in) if cost_in else e_cost
                    f_qty = float(qty_in) if qty_in else e_qty
                    
                    valid = (f_cost > 0 and f_qty > 0)
                    diff = (p - f_cost) * f_qty if valid else 0
                    roi = ((p - f_cost) / f_cost * 100) if valid else 0
                    
                    stock_name = ticker.info.get('shortName') or ticker.info.get('longName') or sym
                    
                    res = {
                        "time": datetime.datetime.now().strftime("%H:%M:%S"),
                        "symbol": sym, 
                        "name": stock_name,
                        "price": f"{p:.2f}", 
                        "change": f"{raw_change:+.2f}", 
                        "pct": f"{(raw_change)/prev*100:+.2f}%",
                        "qty": f"{int(f_qty):,}", 
                        "cost": f"{f_cost:.2f}",
                        "diff": f"{diff:+,.0f}" if valid else "-",
                        "roi": f"{roi:+.2f}%" if valid else "-",
                        "raw_change": raw_change, # 用於判斷顏色
                        "raw_price": p, "raw_qty": f_qty, "raw_cost": f_cost, "raw_diff": diff, "raw_roi": roi
                    }
                    self.root.after(0, self.update_table, res)
                    self.save_portfolio(sym, f_cost, f_qty, stock_name)
                    self.save_daily_log(res)
                    if not is_auto: self.root.after(0, self.clear_ui)
                    found = True
                    break
            
            if not found and not is_auto:
                self.root.after(0, lambda: messagebox.showwarning("搜尋失敗", f"找不到代碼 {raw_s}"))
        except Exception as e: print(f"Error: {e}")

    def update_table(self, data):
        found_id = None
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[1] == data["symbol"]:
                found_id = item
                break
        
        # --- 根據漲跌數值決定標籤 ---
        if data["raw_change"] > 0:
            row_tag = "up"
        elif data["raw_change"] < 0:
            row_tag = "down"
        else:
            row_tag = "even"

        ui_vals = [data[k] for k in self.cols.keys()]
        
        if found_id:
            self.tree.item(found_id, values=ui_vals, tags=(row_tag,))
        else:
            self.tree.insert("", "end", values=ui_vals, tags=(row_tag,))

    # --- 歷史紀錄功能 (每日一筆) ---
    def save_daily_log(self, data):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        new_row = {
            "Date": today, "Time": data["time"], "Symbol": data["symbol"],
            "Name": data["name"], "Price": data["raw_price"], "Qty": data["raw_qty"],
            "Cost": data["raw_cost"], "Total_Diff": data["raw_diff"], "ROI_Pct": data["raw_roi"]
        }
        with file_lock:
            try:
                df = pd.read_excel(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else pd.DataFrame()
                if not df.empty:
                    # 刪除同日重複的舊紀錄，保留最新一次查詢
                    df = df[~((df['Date'] == today) & (df['Symbol'] == data["symbol"]))]
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.sort_values(by=['Date', 'Symbol'], ascending=[False, True]).to_excel(HISTORY_FILE, index=False)
            except: pass

    # --- 其餘輔助功能 ---
    def update_all_stocks(self):
        items = self.tree.get_children()
        if not items: return
        self.btn_all.config(state="disabled")
        def worker():
            for it in items:
                s = self.tree.item(it, "values")[1]
                self.query_logic(s, "", "", True)
                time.sleep(0.5)
            self.root.after(0, lambda: self.btn_all.config(state="normal"))
        threading.Thread(target=worker, daemon=True).start()

    def get_portfolio_data(self, sym):
        if os.path.exists(PORTFOLIO_FILE):
            try:
                df = pd.read_excel(PORTFOLIO_FILE)
                m = df[df['symbol'] == sym]
                if not m.empty: return float(m.iloc[0]['cost']), float(m.iloc[0]['qty'])
            except: pass
        return 0.0, 0.0

    def save_portfolio(self, sym, cost, qty, name):
        with file_lock:
            df = pd.read_excel(PORTFOLIO_FILE) if os.path.exists(PORTFOLIO_FILE) else pd.DataFrame()
            if not df.empty and 'symbol' in df.columns: df = df[df['symbol'] != sym]
            pd.concat([pd.DataFrame([{"symbol": sym, "name": name, "cost": cost, "qty": qty}]), df], ignore_index=True).to_excel(PORTFOLIO_FILE, index=False)

    def load_from_excel(self):
        if os.path.exists(PORTFOLIO_FILE):
            try:
                df = pd.read_excel(PORTFOLIO_FILE)
                for _, r in df.iterrows():
                    v = ["-", r['symbol'], r['name'], "-", "-", "-", f"{int(r['qty']):,}", f"{r['cost']:.2f}", "-", "-"]
                    self.tree.insert("", "end", values=v)
            except: pass

    def delete_record(self):
        sel = self.tree.selection()
        if not sel: return
        s = self.tree.item(sel[0], "values")[1]
        if messagebox.askyesno("確認", f"刪除 {s} 庫存設定？"):
            self.tree.delete(sel[0])
            if os.path.exists(PORTFOLIO_FILE):
                df = pd.read_excel(PORTFOLIO_FILE)
                df[df['symbol'] != s].to_excel(PORTFOLIO_FILE, index=False)

    def open_history_file(self):
        if os.path.exists(HISTORY_FILE): os.startfile(HISTORY_FILE)

    def clear_ui(self):
        for k in ["sym", "cost", "qty"]: self.entries[k].delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = StockApp(root)
    root.mainloop()