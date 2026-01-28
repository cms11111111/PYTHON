import flet as ft
from datetime import datetime
import os
import sys
import json
import shutil
import csv

# =================================================================
# 核心邏輯 (純 Python 版，移除 Pandas)
# =================================================================

class DataManager:
    def __init__(self):
        self.data_file = "account_log.csv"
        self.budget_file = "budget.json"
        self.records = self.load_data()
        self.budgets = self.load_budget()

    def load_data(self):
        records = []
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 處理日期格式
                        try:
                            d_str = row.get("日期", "")
                            # 嘗試解析多種日期格式
                            try:
                                d_obj = datetime.strptime(d_str, "%Y-%m-%d %H:%M:%S")
                            except:
                                d_obj = datetime.strptime(d_str, "%Y-%m-%d")
                        except:
                            d_obj = datetime.now() # 格式錯誤就當作今天

                        records.append({
                            "日期": d_obj,
                            "時間": row.get("時間", ""),
                            "類別": row.get("類別", ""),
                            "金額": float(row.get("金額", 0)),
                            "用途": row.get("用途", "")
                        })
            except Exception as e:
                print(f"讀取錯誤: {e}")
        return records

    def save_data(self):
        try:
            with open(self.data_file, mode='w', encoding='utf-8-sig', newline='') as f:
                fieldnames = ["日期", "時間", "類別", "金額", "用途"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in self.records:
                    writer.writerow({
                        "日期": r["日期"].strftime("%Y-%m-%d"),
                        "時間": r["時間"],
                        "類別": r["類別"],
                        "金額": r["金額"],
                        "用途": r["用途"]
                    })
        except Exception as e:
            print(f"存檔錯誤: {e}")

    def add_record(self, date_val, time_val, category, money, usage):
        try: 
            # date_val 可能是字串或 datetime
            if isinstance(date_val, str):
                date_obj = datetime.strptime(date_val, "%Y-%m-%d")
            else:
                date_obj = date_val
        except: 
            date_obj = datetime.now()

        new_record = {
            "日期": date_obj,
            "時間": time_val,
            "類別": category,
            "金額": money,
            "用途": usage
        }
        self.records.append(new_record)
        self.save_data()

    def filter_data(self, start_date=None, end_date=None, category="全部"):
        filtered = []
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
            ed = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        except:
            sd = ed = None

        for r in self.records:
            r_date = r["日期"]
            # 日期篩選
            if sd and r_date < sd: continue
            if ed and r_date > ed: continue
            # 類別篩選
            if category != "全部" and r["類別"] != category: continue
            
            filtered.append(r)
        
        # 排序 (新到舊)
        filtered.sort(key=lambda x: x["日期"], reverse=True)
        return filtered

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
        # 計算當月總支出 (純 Python 寫法)
        total = 0
        for r in self.records:
            if r["類別"] == "支出":
                try:
                    r_ym = r["日期"].strftime("%Y-%m")
                    if r_ym == ym:
                        total += r["金額"]
                except: pass
        return total

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
        try: 
            # 驗證日期格式
            datetime.strptime(s_end.value, "%Y-%m-%d")
            ym = datetime.strptime(s_end.value, "%Y-%m-%d").strftime("%Y-%m")
        except: 
            ym = datetime.now().strftime("%Y-%m")
            
        b = dm.get_budget_for_month(ym); e = dm.get_monthly_summary(ym); r = b - e
        lbl_ym.value = f"📅 {ym}"
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
        data_list = dm.filter_data(s_start.value, s_end.value, "全部")
        table.rows.clear()
        budget_cache = {}
        
        for r in data_list:
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
            v = float(txt_set_bg.value)
            ym = datetime.strptime(s_end.value, "%Y-%m-%d").strftime("%Y-%m")
            dm.set_budget(ym, v); txt_set_bg.value = ""
            update_summary_card()
        except: pass

    def mini_summary_card():
        return ft.Container(
            padding=15, bgcolor="white", border_radius=12,
            shadow=ft.BoxShadow(blur_radius=5, color="#10000000"),
            content=ft.Column([
                lbl_ym,
                # 這裡不需要 Divider，直接用 spacing 控制
                ft.Row([
                    ft.Column([ft.Text("預算", size=12, color="grey"), lbl_budget], spacing=2, horizontal_alignment="center"),
                    ft.Column([ft.Text("支出", size=12, color="grey"), lbl_expense], spacing=2, horizontal_alignment="center"),
                    ft.Column([ft.Text("剩餘", size=12, color="grey"), lbl_remain], spacing=2, horizontal_alignment="center"),
                ], alignment="spaceAround") 
            ], spacing=5)
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