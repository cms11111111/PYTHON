import flet as ft
import csv
import os
from datetime import datetime

# --- 1. 設定絕對路徑 (確保一定找得到檔案) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "daily_log_flet.csv")
print(f"--------------------------------------------------")
print(f"資料檔路徑: {DATA_FILE}")
print(f"--------------------------------------------------")

# --- 2. 資料處理 ---
def init_csv():
    if not os.path.exists(DATA_FILE):
        print("建立新資料檔...")
        with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['日期', '時間', '類別', '金額', '用途'])
    else:
        print("資料檔已存在")

def add_data(row):
    try:
        with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(row)
        print(f"寫入成功: {row}")
        return True
    except Exception as e:
        print(f"寫入失敗: {e}")
        return False

def read_data():
    data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # 跳過標頭
            for row in reader:
                if row: data.append(row)
    print(f"讀取到 {len(data)} 筆資料")
    return data

def delete_data(target_row):
    all_data = read_data()
    new_data = []
    deleted = False
    for row in all_data:
        if not deleted and row == target_row:
            deleted = True
            print(f"刪除資料: {row}")
            continue
        new_data.append(row)
    
    with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['日期', '時間', '類別', '金額', '用途'])
        writer.writerows(new_data)

# --- 3. 主程式 (Tab 版) ---
def main(page: ft.Page):
    page.title = "除錯模式記帳"
    page.theme_mode = "light"
    page.scroll = "auto" # 讓整個頁面可以捲動
    
    init_csv()

    # --- UI 元件 ---
    t_date = ft.TextField(label="日期", value=datetime.now().strftime('%Y-%m-%d'))
    t_cat = ft.Dropdown(label="類別", options=[ft.dropdown.Option(x) for x in ["餐飲","交通","其他"]])
    t_amt = ft.TextField(label="金額", keyboard_type="number")
    t_use = ft.TextField(label="用途")
    
    # 列表容器 (這是一個 ListView，專門放資料)
    list_container = ft.Column(spacing=10)

    def on_add(e):
        if not t_amt.value: return
        add_data([t_date.value, "00:00", t_cat.value, t_amt.value, t_use.value])
        page.snack_bar = ft.SnackBar(ft.Text("寫入成功"))
        page.snack_bar.open = True
        t_amt.value = ""
        page.update()

    def load_list():
        print("開始更新列表 UI...")
        list_container.controls.clear()
        
        rows = read_data()
        if not rows:
            list_container.controls.append(ft.Text("沒有資料 (請先新增)"))
        else:
            for row in reversed(rows):
                # 建立一個簡單的文字行，不使用複雜的 Card
                row_str = f"{row[0]} | ${row[3]} | {row[2]} - {row[4]}"
                
                # 刪除按鈕邏輯
                def make_del(r):
                    return lambda e: run_del(r)
                
                # 簡單的一行：文字 + 刪除鈕
                item = ft.Row([
                    ft.Text(row_str, size=16, weight="bold"),
                    ft.ElevatedButton("刪除", on_click=make_del(row))
                ], alignment="spaceBetween")
                
                list_container.controls.append(item)
                list_container.controls.append(ft.Divider())
        
        page.update()
        print("列表 UI 更新完成")

    def run_del(row):
        delete_data(row)
        load_list() # 刪除後重新讀取

    # --- Tab 變更事件 ---
    def tabs_changed(e):
        idx = e.control.selected_index
        print(f"切換到分頁: {idx}")
        if idx == 1: # 如果切換到第二頁 (查詢頁)
            load_list()

    # --- 頁面結構 (Tabs) ---
    # 使用 Tabs 是手機 App 最穩定的結構
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        on_change=tabs_changed,
        tabs=[
            ft.Tab(
                text="記帳",
                icon="add",
                content=ft.Column([
                    ft.Text("新增資料", size=20),
                    t_date, t_cat, t_amt, t_use,
                    ft.ElevatedButton("儲存", on_click=on_add)
                ], padding=20)
            ),
            ft.Tab(
                text="查詢",
                icon="list",
                content=ft.Column([
                    ft.Text("歷史資料 (除錯版)", size=20),
                    ft.Divider(),
                    list_container # 這裡放列表
                ], padding=20, scroll="auto")
            ),
        ],
        expand=1 # 讓 Tabs 佔滿畫面
    )

    page.add(tabs)

if __name__ == "__main__":
    ft.app(target=main)
