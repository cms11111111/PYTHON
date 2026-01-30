import flet as ft
import pandas as pd
import os
import json
import shutil
from datetime import datetime

# --- 1. 資料管理邏輯 (內嵌) ---
class SimpleDataManager:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.base_dir, "records.csv")
        self.config_file = os.path.join(self.base_dir, "config.json")
        self.backup_dir = os.path.join(self.base_dir, "backups")
        
        if not os.path.exists(self.data_file):
            pd.DataFrame(columns=['日期', '時間', '類別', '金額', '用途']).to_csv(self.data_file, index=False, encoding='utf-8-sig')
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def add_record(self, date, time, category, amount, desc):
        df = pd.read_csv(self.data_file, encoding='utf-8-sig')
        new_data = {'日期': date, '時間': time, '類別': category, '金額': float(amount), '用途': desc}
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(self.data_file, index=False, encoding='utf-8-sig')

    def get_stats(self):
        df = pd.read_csv(self.data_file, encoding='utf-8-sig')
        month_str = datetime.now().strftime('%Y-%m')
        df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
        monthly_df = df[df['日期'].dt.strftime('%Y-%m') == month_str]
        return monthly_df['金額'].sum(), df

    def save_budget(self, val):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump({'budget': float(val)}, f)

    def get_budget(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f).get('budget', 0)
        return 0

    def backup(self):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self.backup_dir, f"backup_{ts}.csv")
        shutil.copy2(self.data_file, path)
        return path

# --- 2. 主程式介面 ---
def main(page: ft.Page):
    page.title = "日常收支記錄"
    page.theme_mode = "light"
    page.window_width = 400
    page.window_height = 750
    
    dm = SimpleDataManager()

    # --- 狀態更新函式 ---
    def update_ui():
        spent, records_df = dm.get_stats()
        budget = dm.get_budget()
        remain = budget - spent
        
        txt_budget.value = f"NT$ {budget:,.0f}"
        txt_spent.value = f"NT$ {spent:,.0f}"
        txt_remain.value = f"NT$ {remain:,.0f}"
        txt_remain.color = "red" if remain < 0 else "green"
        
        # 更新歷史清單
        list_view.controls.clear()
        if records_df.empty:
            list_view.controls.append(ft.Text("尚無資料", size=16, color="grey"))
        else:
            for _, row in records_df.iloc[::-1].iterrows():
                list_view.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Text(f"{row['日期'].date() if hasattr(row['日期'], 'date') else row['日期']}", size=12), ft.Text(row['類別'], weight="bold", color="blue")]),
                                ft.Row([ft.Text(row['用途'], size=16), ft.Text(f"NT$ {row['金額']:,.0f}", weight="bold", color="red400")], alignment="spaceBetween")
                            ]), padding=10
                        )
                    )
                )
        page.update()

    # --- UI 元件 ---
    txt_budget = ft.Text("0", size=18, weight="bold")
    txt_spent = ft.Text("0", size=18, weight="bold", color="orange")
    txt_remain = ft.Text("0", size=18, weight="bold")

    # 1. 記帳分頁
    home_content = ft.Column([
        ft.Card(ft.Container(ft.Column([
            ft.Row([ft.Icon("account_balance_wallet"), ft.Text("本月概況", size=16, weight="bold")]),
            ft.Row([ft.Text("預算:"), txt_budget], alignment="spaceBetween"),
            ft.Row([ft.Text("支出:"), txt_spent], alignment="spaceBetween"),
            ft.Row([ft.Text("剩餘:"), txt_remain], alignment="spaceBetween"),
        ]), padding=15, bgcolor="bluegrey50")),
        ft.TextField(id="date", label="日期", value=datetime.now().strftime('%Y-%m-%d')),
        ft.Dropdown(id="cat", label="類別", options=[ft.dropdown.Option(x) for x in ["餐飲", "交通", "購物", "娛樂", "其他"]]),
        ft.TextField(id="amt", label="金額", keyboard_type="number"),
        ft.TextField(id="desc", label="用途"),
        ft.ElevatedButton("新增記錄", icon="add", on_click=lambda _: do_add(), width=400)
    ], scroll="auto")

    # 2. 歷史分頁
    list_view = ft.Column(scroll="auto", expand=True)
    history_content = ft.Column([ft.Text("歷史記錄", size=20, weight="bold"), ft.Divider(), list_view], expand=True, visible=False)

    # 3. 設定分頁
    budget_input = ft.TextField(label="設定預算", keyboard_type="number")
    settings_content = ft.Column([
        ft.Text("設定", size=20, weight="bold"),
        budget_input,
        ft.ElevatedButton("儲存", icon="save", on_click=lambda _: do_save_budget()),
        ft.Divider(),
        ft.ListTile(leading=ft.Icon("backup"), title=ft.Text("備份 CSV"), on_click=lambda _: do_backup())
    ], visible=False)

    def do_add():
        # 簡單取值方式，避免 ID 報錯
        controls = home_content.controls
        dm.add_record(controls[1].value, datetime.now().strftime('%H:%M'), controls[2].value, controls[3].value, controls[4].value)
        controls[3].value = ""; controls[4].value = ""
        update_ui()

    def do_save_budget():
        dm.save_budget(budget_input.value)
        update_ui()

    def do_backup():
        p = dm.backup()
        page.snack_bar = ft.SnackBar(ft.Text(f"備份成功: {p}"))
        page.snack_bar.open = True
        page.update()

    def nav_change(e):
        idx = int(e.control.selected_index)
        home_content.visible = (idx == 0)
        history_content.visible = (idx == 1)
        settings_content.visible = (idx == 2)
        update_ui()

    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon="add_card", label="記帳"),
            ft.NavigationBarDestination(icon="history", label="歷史"),
            ft.NavigationBarDestination(icon="settings", label="設定"),
        ],
        on_change=nav_change
    )

    page.add(ft.Container(content=ft.Stack([home_content, history_content, settings_content]), expand=True))
    budget_input.value = str(dm.get_budget())
    update_ui()

if __name__ == "__main__":
    ft.app(main)
