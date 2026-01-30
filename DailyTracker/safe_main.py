import flet as ft
import csv
import os
from datetime import datetime

# 設定檔案名稱 (強制使用絕對路徑)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "daily_log_flet.csv")

# --- 1. 資料處理 (純 Python，不依賴任何外部庫) ---
def init_csv():
    """初始化 CSV 檔案，如果不存在就建立"""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 寫入標頭
            writer.writerow(['日期', '時間', '類別', '金額', '用途'])

def add_record_to_csv(date, time, category, amount, usage):
    """新增一筆記錄"""
    with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([date, time, category, amount, usage])

def get_all_records():
    """讀取所有記錄"""
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # 跳過標頭
            for row in reader:
                if row: # 避免空行
                    records.append(row)
    return records

def delete_record_from_csv(target_row_data):
    """刪除特定記錄 (這裡用比較笨的方法：重寫整個檔案)"""
    records = get_all_records()
    new_records = []
    deleted = False
    
    for row in records:
        # 如果還沒刪除過，且內容完全一樣，就跳過這筆 (即刪除)
        if not deleted and row == target_row_data:
            deleted = True
            continue
        new_records.append(row)
        
    # 寫回檔案
    with open(DATA_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['日期', '時間', '類別', '金額', '用途'])
        writer.writerows(new_records)

# --- 2. 介面邏輯 (Flet) ---
def main(page: ft.Page):
    # 初始化資料庫
    init_csv()

    # 頁面基礎設定
    page.title = "日常記帳 (查詢/刪除版)"
    page.window_width = 400
    page.window_height = 700
    page.theme_mode = "light"  # 使用字串 "light" 避開 ft.ThemeMode 錯誤
    
    # 建立 UI 元件
    
    # [輸入區元件]
    txt_date = ft.TextField(label="日期", value=datetime.now().strftime('%Y-%m-%d'))
    txt_time = ft.TextField(label="時間", value=datetime.now().strftime('%H:%M'))
    dd_category = ft.Dropdown(
        label="類別",
        options=[
            ft.dropdown.Option("餐飲"),
            ft.dropdown.Option("交通"),
            ft.dropdown.Option("購物"),
            ft.dropdown.Option("醫療"),
            ft.dropdown.Option("其他"),
        ]
    )
    txt_amount = ft.TextField(label="金額", keyboard_type="number") # 使用字串 "number"
    txt_usage = ft.TextField(label="用途")
    
    # [訊息提示]
    def show_snack(msg):
        page.snack_bar = ft.SnackBar(ft.Text(msg))
        page.snack_bar.open = True
        page.update()

    # [事件] 新增按鈕點擊
    def btn_add_click(e):
        if not txt_amount.value:
            show_snack("請輸入金額")
            return
            
        add_record_to_csv(
            txt_date.value,
            txt_time.value,
            dd_category.value if dd_category.value else "未分類",
            txt_amount.value,
            txt_usage.value
        )
        
        show_snack("新增成功！")
        # 清空欄位
        txt_amount.value = ""
        txt_usage.value = ""
        page.update()

    # [事件] 刪除按鈕點擊
    def btn_delete_click(row_data):
        delete_record_from_csv(row_data)
        show_snack("已刪除該筆資料")
        render_query_page() # 重新整理列表

    # [頁面渲染] 1. 新增頁面
    def render_add_page():
        page.clean() # 徹底清除，避免殘留
        
        page.add(
            ft.Column([
                ft.Container(height=20),
                ft.Text("新增收支", size=24, weight="bold"), # 使用字串 "bold"
                txt_date,
                txt_time,
                dd_category,
                txt_amount,
                txt_usage,
                ft.Container(height=20),
                ft.ElevatedButton("儲存記錄", icon="save", on_click=btn_add_click, width=300) # 使用字串 icon
            ], 
            alignment=ft.MainAxisAlignment.CENTER, # 使用 Enum，若報錯可改字串
            horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        page.update()

    # [頁面渲染] 2. 查詢/刪除頁面 (傻瓜模式：使用 Column + Scroll)
    def render_query_page():
        page.clean()
        
        records = get_all_records()
        record_count = len(records)
        
        # 準備所有要顯示的元件列表
        display_controls = []
        
        # 1. 標題
        display_controls.append(ft.Text(f"歷史記錄查詢 (共 {record_count} 筆)", size=24, weight="bold", color="black"))
        display_controls.append(ft.Divider())

        # 2. 列表內容
        if not records:
            display_controls.append(ft.Container(content=ft.Text("目前沒有資料", size=18, color="grey"), padding=20))
        else:
            # 倒序顯示
            for row in reversed(records):
                # row 結構: [日期, 時間, 類別, 金額, 用途]
                def create_delete_handler(target_row):
                    return lambda e: btn_delete_click(target_row)

                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"{row[0]}", size=14, color="grey"), # 日期
                                ft.Text(f"${row[3]}", size=20, weight="bold", color="red"), # 金額
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Row([
                                ft.Text(f"[{row[2]}] {row[4]}", size=16, color="black"), # 類別+用途
                                ft.IconButton(
                                    icon="delete", 
                                    icon_color="red",
                                    on_click=create_delete_handler(row)
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        ]),
                        padding=15
                    ),
                    margin=ft.margin.only(bottom=5)
                )
                display_controls.append(card)

        # 3. 關鍵：使用單一 Column 包裝所有內容，並開啟捲動
        # 不要用 expand，不要用 ListView，就是單純的垂直排列
        main_scroll_view = ft.Column(
            controls=display_controls,
            scroll="auto",   # 內容多時自動出現捲軸
            expand=True,     # 嘗試佔滿剩餘空間 (但在 Column 內通常安全)
            spacing=10
        )
        
        page.add(main_scroll_view)
        page.update()

    # [導航欄事件]
    def nav_change(e):
        idx = e.control.selected_index
        if idx == 0:
            render_add_page()
        elif idx == 1:
            render_query_page()

    # 設定導航欄
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon="add", label="記帳"), # 修正：NavigationBarDestination
            ft.NavigationBarDestination(icon="list", label="查詢/刪除"),
        ],
        on_change=nav_change
    )

    # 程式啟動時，先顯示第一頁
    render_add_page()

if __name__ == "__main__":
    ft.app(target=main)
