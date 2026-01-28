import flet as ft
from datetime import datetime
import os
import sys
import json
import shutil 

# =================================================================
# 核心邏輯
# =================================================================

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    class DummyPD:
        def to_datetime(self, val, errors='coerce'): return val
        def DataFrame(self, columns): return []
        def notna(self, val): return val is not None
        def concat(self, objs, ignore_index=True): return objs[0]
    pd = DummyPD()

class DataManager:
    def __init__(self):
        self.data_file = "account_log.csv"
        self.budget_file = "budget.json"
        self.df = self.load_data()
        self.budgets = self.load_budget()

    def load_data(self):
        if not HAS_PANDAS: return []
        try:
            df = pd.read_csv(self.data_file)
            if "日期" in df.columns:
                df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=["日期", "時間", "類別", "金額", "用途"])

    def save_data(self):
        if not HAS_PANDAS: return
        self.df.to_csv(self.data_file, index=False, encoding="utf-8-sig")

    def add_record(self, date_val, time_val, category, money, usage):
        try: date_obj = pd.to_datetime(date_val)
        except: date_obj = datetime.now()
        new_record = {"日期": date_obj, "時間": time_val, "類別": category, "金額": money, "用途": usage}
        self.df = pd.concat([self.df, pd.DataFrame([new_record])], ignore_index=True)
        self.save_data()

    def filter_data(self, start_date=None, end_date=None, category="全部"):
        df = self.df.copy().dropna(subset=['日期'])
        try:
            if start_date: df = df[df['日期'] >= pd.to_datetime(start_date, errors='coerce')]
            if end_date: df = df[df['日期'] <= pd.to_datetime(end_date, errors='coerce')]
        except: pass
        if category != "全部": df = df[df['類別'] == category]
        return df

    def load_budget(self):
        try:
            if os.path.exists(self.budget_file):
                with open(self.budget_file, 'r', encoding='utf-8') as f: return json.load(f)
            return {}
        except: return {}

    def save_budget(self):
        with open(self.budget_file, 'w', encoding='utf-8') as f: json.dump(self.budgets, f)

    def set_budget(self, ym, amt):
        self.budgets[ym] = float(amt); self.save_budget()

    def get_budget_for_month(self, ym):
        if ym in self.budgets: return self.budgets[ym]
        prev = 0
        for k in sorted(self.budgets.keys()):
            if k < ym: prev = self.budgets[k]
            else: break
        return prev
        
    def get_monthly_summary(self, ym):
        try:
            start = f"{ym}-01"
            import calendar
            last = calendar.monthrange(int(ym[:4]), int(ym[5:]))[1]
            end = f"{ym}-{last}"
            df = self.filter_data(start, end, "支出")
            return df['金額'].sum() if not df.empty else 0
        except: return 0

# =================================================================
# Flet UI 介面
# =================================================================

def main(page: ft.Page):
    page.title = "記帳助手"
    page.window_width = 450 
    page.window_height = 800
    page.bgcolor = "#F5F7FA"
    page.padding = 0

    dm = DataManager()
    
    def trigger_quick_backup(e):
        try:
            name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            shutil.copy(dm.data_file, name)
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ 備份成功: {name}"), bgcolor="green"); page.snack_bar.open=True; page.update()
        except: pass

    # --- UI 元件 ---
    lbl_ym = ft.Text("概況載入中", size=14, weight="bold", color="#1A237E")
    lbl_budget = ft.Text("$0", size=16, weight="bold")
    lbl_expense = ft.Text("$0", size=16, weight="bold", color="#D32F2F")
    lbl_remain = ft.Text("$0", size=20, weight="bold", color="#388E3C")
    
    txt_date = ft.TextField(label="日期", value=datetime.now().strftime("%Y-%m-%d"), height=48, text_size=13, width=140)
    txt_time = ft.TextField(label="時間", value=datetime.now().strftime("%H:%M"), width=90, height=48, text_size=13)
    dd_type = ft.Dropdown(label="類型", options=[ft.dropdown.Option("支出"), ft.dropdown.Option("收入")], value="支出", width=120, height=48, text_size=13)
    
    txt_amt = ft.TextField(label="金額 ($)", keyboard_type="number", height=55, text_size=18)
    txt_use = ft.TextField(label="用途說明", height=55, text_size=14)
    lbl_op_msg = ft.Text("", size=11)

    s_start = ft.TextField(label="起", value=datetime.now().replace(day=1).strftime("%Y-%m-%d"), width=105, height=40, text_size=11)
    s_end = ft.TextField(label="迄", value=datetime.now().strftime("%Y-%m-%d"), width=105, height=40, text_size=11)
    txt_set_bg = ft.TextField(label="本月預算", keyboard_type="number", width=110, height=40, text_size=11)
    
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("日期", size=11)), 
            ft.DataColumn(ft.Text("類", size=11)),
            ft.DataColumn(ft.Text("金額", size=11)), 
            ft.DataColumn(ft.Text("用途", size=11)),
            ft.DataColumn(ft.Text("當月預算", size=11)),
        ], 
        rows=[], 
        column_spacing=10, 
        heading_row_height=35,
        width=430 
    )

    def update_summary_card():
        try: d = pd.to_datetime(s_end.value, errors='coerce').strftime("%Y-%m")
        except: d = datetime.now().strftime("%Y-%m")
        b = dm.get_budget_for_month(d); e = dm.get_monthly_summary(d); r = b - e
        lbl_ym.value = f"📅 {d}"
        lbl_budget.value = f"${b:,.0f}"; lbl_expense.value = f"${e:,.0f}"; lbl_remain.value = f"${r:,.0f}"
        lbl_remain.color = "#D32F2F" if r < 0 else "#388E3C"
        page.update()

    def set_today(e):
        now = datetime.now().strftime("%Y-%m-%d")
        if e.control.data=="add": txt_date.value=now
        else: s_end.value=now
        update_summary_card(); page.update()

    def save_rec(e):
        try:
            v = float(txt_amt.value)
            dm.add_record(txt_date.value, txt_time.value, dd_type.value, v, txt_use.value)
            txt_amt.value=""; txt_use.value=""; txt_amt.focus()
            lbl_op_msg.value="✅ 已存檔"; lbl_op_msg.color="green"
            update_summary_card(); page.update()
        except: pass

    def do_search(e=None):
        df = dm.filter_data(s_start.value, s_end.value, "全部")
        if not df.empty: df = df.sort_values('日期', ascending=False)
        table.rows.clear()
        budget_cache = {}
        for _, r in df.iterrows():
            c = "#D32F2F" if r["類別"]=="支出" else "#388E3C"
            ym = r["日期"].strftime("%Y-%m")
            if ym not in budget_cache: budget_cache[ym] = dm.get_budget_for_month(ym)
            table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(r["日期"].strftime("%m/%d"), size=11)),
                ft.DataCell(ft.Text(r["類別"][0], size=11)),
                ft.DataCell(ft.Text(f"{r['金額']:,.0f}", color=c, weight="bold", size=11)),
                ft.DataCell(ft.Text(r["用途"], size=11)),
                ft.DataCell(ft.Text(f"${budget_cache[ym]:,.0f}", size=10, color="grey")),
            ]))
        update_summary_card()

    def save_bg(e):
        try:
            v = float(txt_set_bg.value); ym = pd.to_datetime(s_end.value).strftime("%Y-%m")
            dm.set_budget(ym, v); txt_set_bg.value = ""
            update_summary_card()
        except: pass

    def mini_summary_card():
        return ft.Container(
            padding=15, bgcolor="white", border_radius=12,
            shadow=ft.BoxShadow(blur_radius=5, color="#10000000"),
            content=ft.Column([
                lbl_ym,
                # 關鍵修改：移除 Divider 並設定 spacing=5 縮小空白
                ft.Row([
                    ft.Column([ft.Text("預算", size=12, color="grey"), lbl_budget], spacing=2, horizontal_alignment="center"),
                    ft.Column([ft.Text("支出", size=12, color="grey"), lbl_expense], spacing=2, horizontal_alignment="center"),
                    ft.Column([ft.Text("剩餘", size=12, color="grey"), lbl_remain], spacing=2, horizontal_alignment="center"),
                ], alignment="spaceAround") 
            ], spacing=5) # 這裡設定 Column 的元件間距
        )

    def view_add():
        return ft.Container(
            padding=15,
            content=ft.Column([
                mini_summary_card(),
                ft.Container(height=5), 
                ft.Container(
                    bgcolor="white", padding=15, border_radius=10, 
                    content=ft.Column([
                        ft.Row([txt_date, ft.ElevatedButton(content=ft.Text("設為今日", size=11), on_click=set_today, data="add", height=32, width=110)]),
                        ft.Row([dd_type, txt_time]),
                        ft.Container(height=2), 
                        txt_amt, 
                        ft.Container(height=2), 
                        txt_use,
                        ft.Container(height=5), 
                        ft.ElevatedButton(content=ft.Text("儲存記錄", size=14, weight="bold"), on_click=save_rec, bgcolor="#1A237E", color="white", height=45, expand=True),
                        lbl_op_msg
                    ], spacing=8) 
                )
            ], scroll="auto")
        )

    def view_search():
        return ft.Container(
            padding=10,
            content=ft.Column([
                mini_summary_card(),
                ft.Container(height=5), 
                ft.Container(
                    bgcolor="white", padding=10, border_radius=10,
                    content=ft.Column([
                        ft.Row([s_start, ft.Text("~", size=10), s_end, ft.ElevatedButton(content=ft.Text("查詢", size=11), on_click=do_search, height=32, width=80)], alignment="center"),
                        ft.Row([txt_set_bg, ft.ElevatedButton(content=ft.Text("設定預算", size=11), on_click=save_bg, height=32, width=100), 
                                ft.TextButton(content=ft.Text("一鍵備份", size=11), on_click=trigger_quick_backup)], alignment="spaceBetween"),
                    ], spacing=8) 
                ),
                ft.Container(
                    bgcolor="white", border_radius=10, padding=0,
                    expand=True,
                    content=ft.ListView([table], expand=True)
                )
            ])
        )

    body = ft.Container(expand=True, content=view_add())
    
    def nav_change(e):
        idx = e.control.data
        if idx == 0: 
            body.content = view_add(); update_summary_card()
            btn_add.bgcolor = "#1A237E"; btn_add.color = "white"
            btn_search.bgcolor = "white"; btn_search.color = "#757575"
        else: 
            body.content = view_search(); do_search()
            btn_add.bgcolor = "white"; btn_add.color = "#757575"
            btn_search.bgcolor = "#388E3C"; btn_search.color = "white"
        page.update()

    btn_add = ft.ElevatedButton(content=ft.Text("新增頁面", size=12, weight="bold"), data=0, on_click=nav_change, bgcolor="#1A237E", color="white", height=35, width=130)
    btn_search = ft.ElevatedButton(content=ft.Text("查詢報表", size=12, weight="bold"), data=1, on_click=nav_change, bgcolor="white", color="#757575", height=35, width=130)
    
    bottom_bar = ft.Container(
        bgcolor="white", padding=ft.padding.only(top=8, bottom=8),
        border=ft.border.only(top=ft.border.BorderSide(1, "#E0E0E0")),
        content=ft.Row([btn_add, btn_search], alignment="center", spacing=30)
    )

    page.add(ft.Column([
        ft.Container(expand=True, alignment=ft.Alignment(0, -1), content=ft.Container(width=450, content=body)),
        bottom_bar
    ], spacing=0, expand=True))
    
    update_summary_card()

if __name__ == "__main__":
    ft.app(target=main)
