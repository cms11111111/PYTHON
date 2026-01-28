import flet as ft
from datetime import datetime
import os
import sys

# 嘗試匯入 pandas，如果失敗則使用簡易模式
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("警告: 找不到 pandas，將使用簡易模式執行")
    # 建立一個假的 pd 物件防止報錯
    class DummyPD:
        def to_datetime(self, val, errors='coerce'):
            return val
        def DataFrame(self, columns):
            return []
        def notna(self, val):
            return val is not None
        def concat(self, objs, ignore_index=True):
            return objs[0] # 簡化
    pd = DummyPD()

# =================================================================
# 資料處理邏輯
# =================================================================

class DataManager:
    def __init__(self):
        self.data_file = "account_log.csv"
        self.df = self.load_data()

    def get_data_path(self, relative_path):
        return relative_path

    def load_data(self):
        try:
            df = pd.read_csv(self.data_file)
            if "日期" in df.columns:
                df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=["日期", "時間", "類別", "金額", "用途"])
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame(columns=["日期", "時間", "類別", "金額", "用途"])

    def save_data(self):
        try:
            self.df.to_csv(self.data_file, index=False, encoding="utf-8-sig")
        except Exception as e:
            print(f"Error saving data: {e}")

    def add_record(self, date_val, time_val, category, money, usage):
        new_record = {
            "日期": pd.to_datetime(date_val),
            "時間": time_val,
            "類別": category,
            "金額": money,
            "用途": usage,
        }
        new_row = pd.DataFrame([new_record])
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        self.save_data()
        
    def filter_data(self, start_date=None, end_date=None, category="全部"):
        filtered_df = self.df.copy()
        filtered_df = filtered_df.dropna(subset=['日期'])
        
        if start_date:
            filtered_df = filtered_df[filtered_df['日期'] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df['日期'] <= pd.to_datetime(end_date)]
        
        if category != "全部":
            filtered_df = filtered_df[filtered_df['類別'] == category]
            
        return filtered_df

# =================================================================
# Flet UI 介面
# =================================================================

def main(page: ft.Page):
    page.title = "手機記帳助手"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 420
    page.window_height = 800
    page.bgcolor = "#f0f0f0"

    data_manager = DataManager()

    # --- 狀態控制 ---
    current_date_target = "add" 

    # --- UI 元件: 新增頁面 ---
    txt_date = ft.Text(datetime.now().strftime("%Y-%m-%d"), size=16, weight="bold")
    txt_time = ft.TextField(label="時間 (HH:MM)", value=datetime.now().strftime("%H:%M"), border_radius=10)
    dd_category = ft.Dropdown(
        label="類別",
        options=[ft.dropdown.Option("支出"), ft.dropdown.Option("收入")],
        value="支出",
        border_radius=10
    )
    txt_money = ft.TextField(label="金額", keyboard_type="number", border_radius=10)
    txt_usage = ft.TextField(label="用途/備註", border_radius=10)
    lbl_status = ft.Text("", color="red")

    # --- UI 元件: 查詢頁面 ---
    search_start_date_txt = ft.Text("開始日期", size=12)
    search_end_date_txt = ft.Text("結束日期", size=12)
    search_category = ft.Dropdown(
        label="類別",
        options=[ft.dropdown.Option("全部"), ft.dropdown.Option("支出"), ft.dropdown.Option("收入")],
        value="全部",
        width=110,
        text_size=12
    )
    total_amount_txt = ft.Text("總計: $0", size=18, weight="bold", color="blue")
    
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("日期")),
            ft.DataColumn(ft.Text("類別")),
            ft.DataColumn(ft.Text("金額")),
            ft.DataColumn(ft.Text("用途")),
        ],
        rows=[],
        column_spacing=15
    )

    # --- 日期選擇器 ---
    def on_date_change(e):
        if not date_picker.value: return
        d_str = date_picker.value.strftime("%Y-%m-%d")
        if current_date_target == "add": txt_date.value = d_str
        elif current_date_target == "start": search_start_date_txt.value = d_str
        elif current_date_target == "end": search_end_date_txt.value = d_str
        page.update()

    date_picker = ft.DatePicker(on_change=on_date_change)
    page.overlay.append(date_picker)

    def open_picker(target):
        nonlocal current_date_target
        current_date_target = target
        date_picker.pick_date()

    # --- 邏輯: 查詢功能 ---
    def run_search(e=None):
        start = search_start_date_txt.value if search_start_date_txt.value != "開始日期" else None
        end = search_end_date_txt.value if search_end_date_txt.value != "結束日期" else None
        res = data_manager.filter_data(start, end, search_category.value)
        
        if not res.empty:
            res = res.sort_values(by='日期', ascending=False)

        data_table.rows.clear()
        total = 0
        for _, row in res.iterrows():
            m = row['金額']
            total += m
            color = "red" if row["類別"] == "支出" else "green"
            data_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(row["日期"].strftime("%m/%d"), size=12)),
                    ft.DataCell(ft.Text(row["類別"], size=12)),
                    ft.DataCell(ft.Text(f"{m:,.0f}", color=color, weight="bold")),
                    ft.DataCell(ft.Text(row["用途"], size=12)),
                ])
            )
        total_amount_txt.value = f"總計: ${total:,.0f}"
        page.update()

    # --- 畫面構建 ---
    def build_add_view():
        return ft.Column([
            ft.Text("📝 新增記錄", size=22, weight="bold", color="blue"),
            ft.Divider(),
            ft.Row([ft.ElevatedButton("選日期", on_click=lambda _: open_picker("add")), txt_date], alignment="center"),
            txt_time, dd_category, txt_money, txt_usage,
            ft.ElevatedButton("儲存記錄", on_click=save_record, bgcolor="blue", color="white", width=250, height=50),
            lbl_status
        ], horizontal_alignment="center", spacing=15)

    def build_history_view():
        return ft.Column([
            ft.Text("🔍 查詢清單", size=22, weight="bold", color="blue"),
            ft.Divider(),
            ft.Container(
                bgcolor="#eeeeee", padding=10, border_radius=10,
                content=ft.Column([
                    ft.Row([
                        ft.TextButton("起", on_click=lambda _: open_picker("start")), search_start_date_txt,
                        ft.Text("~"),
                        ft.TextButton("迄", on_click=lambda _: open_picker("end")), search_end_date_txt,
                    ], alignment="center"),
                    ft.Row([search_category, ft.ElevatedButton("執行查詢", on_click=run_search, bgcolor="green", color="white")], alignment="center")
                ])
            ),
            ft.Container(padding=5, content=total_amount_txt),
            ft.Column([data_table], scroll="always", height=350, expand=True)
        ], horizontal_alignment="center")

    def save_record(e):
        try:
            val = float(txt_money.value)
            data_manager.add_record(txt_date.value, txt_time.value, dd_category.value, val, txt_usage.value)
            lbl_status.value = "✅ 儲存成功！"; lbl_status.color = "green"
            txt_money.value = ""; txt_usage.value = ""; txt_money.focus()
            page.update()
        except:
            lbl_status.value = "❌ 金額錯誤"; lbl_status.color = "red"; page.update()

    # --- 主佈局 ---
    content_area = ft.Container(padding=20, bgcolor="white", border_radius=15, expand=True)
    
    def change_tab(e):
        idx = e.control.data
        if idx == 0:
            content_area.content = build_add_view()
            b1.bgcolor="blue"; b1.color="white"; b2.bgcolor="white"; b2.color="black"
        else:
            content_area.content = build_history_view()
            run_search() # 自動查詢一次
            b1.bgcolor="white"; b1.color="black"; b2.bgcolor="blue"; b2.color="white"
        page.update()

    b1 = ft.ElevatedButton("新增", on_click=change_tab, data=0, bgcolor="blue", color="white")
    b2 = ft.ElevatedButton("查詢", on_click=change_tab, data=1, bgcolor="white", color="black")
    
    page.add(
        ft.Column([
            ft.Container(expand=True, alignment=ft.Alignment(0, -1), content=ft.Container(width=400, content=content_area)),
            ft.Container(bgcolor="white", padding=10, content=ft.Row([b1, b2], alignment="center", spacing=30))
        ], expand=True)
    )
    content_area.content = build_add_view() # 預設畫面
    page.update()

if __name__ == "__main__":
    ft.app(target=main)