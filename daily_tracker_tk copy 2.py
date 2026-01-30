import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import csv
import os
import json
import shutil
import calendar
from datetime import datetime

# --- 1. 基礎設定與資料管理 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'daily_records.csv')
CONFIG_FILE = os.path.join(BASE_DIR, 'budget_config.json')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)

class DataManager:
    def __init__(self): self.init_db()
    def init_db(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w', newline='', encoding='utf-8-sig') as f:
                csv.writer(f).writerow(['日期', '時間', '類別', '金額', '用途'])
    def add_record(self, d, c, a, u):
        with open(DATA_FILE, 'a', newline='', encoding='utf-8-sig') as f:
            csv.writer(f).writerow([d, datetime.now().strftime('%H:%M'), c, a, u])
    def get_records(self):
        r = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f); next(reader, None)
                for row in reader: r.append(row)
        return r
    def delete_record_by_data(self, target):
        recs = self.get_records(); new_recs = []; deleted = False
        for row in recs:
            if not deleted and row == target: deleted = True; continue
            new_recs.append(row)
        with open(DATA_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f); w.writerow(['日期', '時間', '類別', '金額', '用途']); w.writerows(new_recs)
    def get_budget(self):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f).get('budget', 0)
        except: return 0
    def set_budget(self, a): 
        with open(CONFIG_FILE, 'w') as f: json.dump({'budget': int(a)}, f)
    def backup_data(self):
        t = os.path.join(BACKUP_DIR, f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        shutil.copy2(DATA_FILE, t); return t

# --- 2. 簡易月曆 ---
class SimpleCalendar(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.title("Select Date")
        self.geometry("280x280")
        self.transient(parent); self.grab_set(); self.focus_set()
        self.current_date = datetime.now()
        h = tk.Frame(self); h.pack(fill="x", pady=5)
        tk.Button(h, text="<", command=self.prev_month).pack(side="left", padx=10)
        self.lbl_m = tk.Label(h, text="", font=("Arial", 14, "bold"))
        self.lbl_m.pack(side="left", expand=True)
        tk.Button(h, text=">", command=self.next_month).pack(side="right", padx=10)
        self.cf = tk.Frame(self); self.cf.pack(fill="both", expand=True)
        self.draw()
    def draw(self):
        for w in self.cf.winfo_children(): w.destroy()
        y, m = self.current_date.year, self.current_date.month
        self.lbl_m.config(text=f"{y} / {m}")
        days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for i, d in enumerate(days):
            tk.Label(self.cf, text=d, fg="blue" if i < 5 else "red", font=("Arial", 10)).grid(row=0, column=i, padx=5, pady=5)
        cal = calendar.monthcalendar(y, m)
        for r, week in enumerate(cal):
            for c, d in enumerate(week):
                if d != 0:
                    btn = tk.Button(self.cf, text=str(d), width=4, pady=5, command=lambda x=d: self.on_select(x))
                    if (y == datetime.now().year and m == datetime.now().month and d == datetime.now().day): btn.config(bg="yellow")
                    btn.grid(row=r+1, column=c, padx=2, pady=2)
    def prev_month(self):
        import datetime as dt
        self.current_date = (self.current_date.replace(day=1) - dt.timedelta(days=1)).replace(day=1)
        self.draw()
    def next_month(self):
        m = self.current_date.month + 1 if self.current_date.month < 12 else 1
        y = self.current_date.year + 1 if self.current_date.month == 12 else self.current_date.year
        self.current_date = self.current_date.replace(year=y, month=m)
        self.draw()
    def on_select(self, d):
        self.callback(self.current_date.replace(day=d).strftime('%Y-%m-%d')); self.destroy()

# --- 3. 介面設計 ---
class BudgetApp:
    def __init__(self, root):
        self.root = root
        self.root.title("日常收支")
        self.root.geometry("400x750")
        self.dm = DataManager()
        
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Microsoft JhengHei", 12), padding=[5, 8])
        style.configure("Treeview", font=("Microsoft JhengHei", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Microsoft JhengHei", 11, "bold"))
        
        # 頂部概況
        self.sum_fr = tk.Frame(root, bg="#0078d7", pady=15)
        self.sum_fr.pack(fill="x")
        tk.Label(self.sum_fr, text="本月收支概況", bg="#0078d7", fg="white", font=("Microsoft JhengHei", 14, "bold")).pack()
        self.st_fr = tk.Frame(self.sum_fr, bg="#0078d7"); self.st_fr.pack(fill="x", pady=5)
        self.lbl_bud = self.mk_stat("預算", 0); self.lbl_sp = self.mk_stat("支出", 1); self.lbl_rem = self.mk_stat("剩餘", 2)

        self.nb = ttk.Notebook(root); self.nb.pack(expand=True, fill="both")
        self.t1 = ttk.Frame(self.nb); self.nb.add(self.t1, text=" 記 帳 ")
        self.setup_add_tab()
        self.t2 = ttk.Frame(self.nb); self.nb.add(self.t2, text=" 查 詢 ")
        self.setup_history_tab()
        self.t3 = ttk.Frame(self.nb); self.nb.add(self.t3, text=" 日 期 ")
        self.setup_search_tab()
        self.update_ui()

    def mk_stat(self, t, c):
        f = tk.Frame(self.st_fr, bg="#0078d7"); f.pack(side="left", expand=True)
        tk.Label(f, text=t, bg="#0078d7", fg="#b3e5fc", font=("Arial", 10)).pack()
        l = tk.Label(f, text="0", bg="#0078d7", fg="white", font=("Arial", 16, "bold")); l.pack()
        return l

    def setup_add_tab(self):
        f = tk.Frame(self.t1, padx=15, pady=15); f.pack(fill="both", expand=True)
        
        # 1. 日期
        r1 = tk.Frame(f); r1.pack(fill="x", pady=5)
        tk.Label(r1, text="日期:", font=("Microsoft JhengHei", 12), width=5, anchor="w").pack(side="left")
        self.e_date = ttk.Entry(r1, font=("Arial", 12), width=12)
        self.e_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.e_date.pack(side="left", padx=5) # 移除 fill/expand
        tk.Button(r1, text="選", command=lambda: self.open_cal(self.e_date)).pack(side="left")

        # 2. 金額
        r2 = tk.Frame(f); r2.pack(fill="x", pady=5)
        tk.Label(r2, text="金額:", font=("Microsoft JhengHei", 12), width=5, anchor="w").pack(side="left")
        self.e_amt = tk.Entry(r2, font=("Arial", 14, "bold"), bg="#fffde7", width=12)
        self.e_amt.pack(side="left", padx=5) # 移除 fill/expand
        # 移動游標即清除 (聚焦或點擊都觸發)
        self.e_amt.bind("<FocusIn>", self.clear_ok_msg)
        self.e_amt.bind("<Button-1>", self.clear_ok_msg)

        # 3. 用途
        r3 = tk.Frame(f); r3.pack(fill="x", pady=5)
        tk.Label(r3, text="用途:", font=("Microsoft JhengHei", 12), width=5, anchor="w").pack(side="left")
        self.e_use = tk.Entry(r3, font=("Microsoft JhengHei", 12), width=15)
        self.e_use.pack(side="left", padx=5) # 移除 fill/expand
        # 移動游標即清除 (聚焦或點擊都觸發)
        self.e_use.bind("<FocusIn>", self.clear_ok_msg)
        self.e_use.bind("<Button-1>", self.clear_ok_msg)

        # 4. 類別
        tk.Label(f, text="類別:", font=("Microsoft JhengHei", 12, "bold")).pack(anchor="w", pady=(15,0))
        cat_fr = tk.Frame(f); cat_fr.pack(fill="x", pady=5)
        self.sel_cat = tk.StringVar(value="餐飲")
        cats = ["餐飲", "交通", "購物", "娛樂", "醫療", "其他"]
        self.c_btns = {}
        for c in cats:
            b = tk.Button(cat_fr, text=c, font=("Microsoft JhengHei", 10),
                            command=lambda x=c: self.set_cat(x), relief="flat", bg="#e0e0e0")
            b.pack(side="left", expand=True, fill="x", padx=1)
            self.c_btns[c] = b

        tk.Label(f, text="", height=1).pack()
        self.btn_save = tk.Button(f, text="儲存記錄", bg="#0078d7", fg="white", font=("Microsoft JhengHei", 14, "bold"), 
                  command=self.save_rec)
        self.btn_save.pack(fill="x", pady=10)
        self.set_cat("餐飲")

    def clear_ok_msg(self, event=None):
        if self.e_use.get() == "儲存OK":
            self.e_use.delete(0, tk.END)
            self.e_use.config(foreground="black")

    def save_rec(self):
        d, c, a, u = self.e_date.get(), self.sel_cat.get(), self.e_amt.get(), self.e_use.get()
        if not a.replace('.','').isdigit() or not a: return
        self.dm.add_record(d, c, a, u)
        self.e_amt.delete(0, tk.END)
        self.e_use.delete(0, tk.END)
        self.e_use.insert(0, "儲存OK")
        self.e_use.config(foreground="gray")
        self.update_ui()

    def set_cat(self, c):
        self.clear_ok_msg() # 點選類別也清除儲存OK
        self.sel_cat.set(c)
        for k, b in self.c_btns.items(): b.config(bg="#0078d7" if k==c else "#e0e0e0", fg="white" if k==c else "black")
        self.e_use.delete(0, tk.END); self.e_use.insert(0, c)

    def setup_history_tab(self):
        f = tk.Frame(self.t2, padx=10, pady=10); f.pack(fill="both", expand=True)
        btn_fr = tk.Frame(f); btn_fr.pack(fill="x", pady=5)
        ttk.Button(btn_fr, text="設定預算", command=self.ask_bud).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btn_fr, text="備份資料", command=self.bkp).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(btn_fr, text="刪除選取", command=self.dele).pack(side="left", expand=True, fill="x", padx=2)
        cols = ("date", "cat", "use", "amt")
        self.tree = ttk.Treeview(f, columns=cols, show="headings")
        self.tree.heading("date", text="日期"); self.tree.column("date", width=110, anchor="center")
        self.tree.heading("cat", text="類別"); self.tree.column("cat", width=50, anchor="center")
        self.tree.heading("use", text="用途"); self.tree.column("use", width=100, anchor="center")
        self.tree.heading("amt", text="金額"); self.tree.column("amt", width=80, anchor="e")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        vsb = ttk.Scrollbar(f, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=vsb.set); vsb.pack(side="right", fill="y")

    def setup_search_tab(self):
        f = tk.Frame(self.t3, padx=10, pady=10); f.pack(fill="both", expand=True)
        rf = tk.LabelFrame(f, text="日期範圍", font=("Arial", 11), padx=5, pady=5); rf.pack(fill="x")
        r1 = tk.Frame(rf); r1.pack(fill="x", pady=2)
        tk.Label(r1, text="起:", font=("Arial", 11)).pack(side="left")
        self.s_start = ttk.Entry(r1, font=("Arial", 11)); self.s_start.pack(side="left", fill="x", expand=True, padx=5)
        self.s_start.insert(0, datetime.now().strftime('%Y-%m-01'))
        tk.Button(r1, text="選", command=lambda: self.open_cal(self.s_start)).pack(side="left")
        r2 = tk.Frame(rf); r2.pack(fill="x", pady=2)
        tk.Label(r2, text="迄:", font=("Arial", 11)).pack(side="left")
        self.s_end = ttk.Entry(r2, font=("Arial", 11)); self.s_end.pack(side="left", fill="x", expand=True, padx=5)
        self.s_end.insert(0, datetime.now().strftime('%Y-%m-%d'))
        tk.Button(r2, text="選", command=lambda: self.open_cal(self.s_end)).pack(side="left")
        tk.Button(rf, text="查詢", bg="#fff9c4", font=("Arial", 12, "bold"), command=self.do_search).pack(fill="x", pady=5)
        self.lbl_search_total = tk.Label(f, text="總計: $0", font=("Arial", 16, "bold"), fg="red"); self.lbl_search_total.pack(pady=5)
        cols = ("date", "cat", "use", "amt")
        self.s_tree = ttk.Treeview(f, columns=cols, show="headings")
        self.s_tree.heading("date", text="日期"); self.s_tree.column("date", width=110, anchor="center")
        self.s_tree.heading("cat", text="類別"); self.s_tree.column("cat", width=50, anchor="center")
        self.s_tree.heading("use", text="用途"); self.s_tree.column("use", width=100, anchor="center")
        self.s_tree.heading("amt", text="金額"); self.s_tree.column("amt", width=80, anchor="e")
        self.s_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def ask_bud(self):
        v = simpledialog.askinteger("預算", "本月預算：", parent=self.root)
        if v: self.dm.set_budget(v); self.update_ui()
    def bkp(self):
        try: messagebox.showinfo("OK", f"Save:\n{self.dm.backup_data()}")
        except Exception as e: messagebox.showerror("Err", str(e))
    def open_cal(self, e): SimpleCalendar(self.root, lambda d: (e.delete(0, tk.END), e.insert(0, d)))
    def update_ui(self):
        bud = self.dm.get_budget(); recs = self.dm.get_records()
        cm = datetime.now().strftime('%Y-%m')
        sp = sum(int(float(r[3])) for r in recs if r[0].startswith(cm))
        self.lbl_bud.config(text=f"{bud:,}"); self.lbl_sp.config(text=f"{sp:,}")
        self.lbl_rem.config(text=f"{bud-sp:,}", fg="red" if bud-sp < 0 else "white")
        for i in self.tree.get_children(): self.tree.delete(i)
        self.cur_data = []
        for r in reversed(recs): self.tree.insert("", "end", values=(r[0], r[2], r[4], r[3])); self.cur_data.append(r)
    def dele(self):
        s = self.tree.selection()
        if not s: return
        if messagebox.askyesno("?", "刪除?"): self.dm.delete_record_by_data(self.cur_data[self.tree.index(s[0])]); self.update_ui()
    def do_search(self):
        try: s = datetime.strptime(self.s_start.get(), "%Y-%m-%d"); e = datetime.strptime(self.s_end.get(), "%Y-%m-%d")
        except: return
        rs = self.dm.get_records(); self.s_tree.delete(*self.s_tree.get_children()); tot = 0
        for r in reversed(rs):
            try:
                rd = datetime.strptime(r[0], "%Y-%m-%d")
                if s <= rd <= e: self.s_tree.insert("", "end", values=(r[0], r[2], r[4], r[3])); tot += int(float(r[3]))
            except: pass
        self.lbl_search_total.config(text=f"總計: ${tot:,}")

if __name__ == "__main__":
    root = tk.Tk(); app = BudgetApp(root); root.mainloop()
