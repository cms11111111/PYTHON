from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import csv
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey' # 用於 flash messages

# --- 設定絕對路徑 (確保資料不迷路) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'records.csv')
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

# --- 資料處理函式 ---
def init_db():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['日期', '時間', '類別', '金額', '用途'])

def get_records():
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # 跳過標頭
            for row in reader:
                if row: records.append(row)
    return records # 原始順序 (最早在前)

def save_record(date, category, amount, usage):
    time = datetime.now().strftime('%H:%M')
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([date, time, category, amount, usage])

def delete_record_by_index(index):
    # 這是比較簡單的刪除方式：讀出全部 -> 刪除指定 index -> 寫回全部
    # index 對應的是 get_records() 反轉前的順序
    # 但因為介面是顯示反轉後的 (最新的在最上面)，所以傳入的 index 需要小心處理
    # 為了簡單起見，我們在介面直接使用 loop.index0 對應反轉後的列表
    # 所以後端要刪除的是：總長度 - 1 - index
    
    records = get_records()
    real_index = len(records) - 1 - index
    
    if 0 <= real_index < len(records):
        del records[real_index]
        
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['日期', '時間', '類別', '金額', '用途'])
            writer.writerows(records)

def get_budget():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get('budget', 0)
        except: return 0
    return 0

def set_budget(amount):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'budget': int(amount)}, f)

def get_stats():
    records = get_records()
    current_month = datetime.now().strftime('%Y-%m')
    spent = 0
    for r in records:
        # r[0] 是日期字串 'YYYY-MM-DD'
        if r[0].startswith(current_month):
            try: spent += int(float(r[3]))
            except: pass
    return spent

# --- 路由 (網頁邏輯) ---
@app.route('/')
def index():
    init_db()
    records = get_records()
    # 反轉列表，讓最新的在最上面
    reversed_records = list(reversed(records))
    
    budget = get_budget()
    spent = get_stats()
    remaining = budget - spent
    
    return render_template('index.html', 
                           records=reversed_records, 
                           budget=budget, 
                           spent=spent, 
                           remaining=remaining,
                           today=datetime.now().strftime('%Y-%m-%d'),
                           month_str=datetime.now().strftime('%Y-%m'),
                           data_file=DATA_FILE)

@app.route('/add', methods=['POST'])
def add():
    save_record(
        request.form['date'],
        request.form['category'],
        request.form['amount'],
        request.form['usage']
    )
    flash('新增成功！')
    return redirect(url_for('index'))

@app.route('/delete/<int:index>')
def delete(index):
    delete_record_by_index(index)
    flash('已刪除記錄')
    return redirect(url_for('index'))

@app.route('/set_budget', methods=['POST'])
def save_budget_route():
    set_budget(request.form['budget'])
    flash('預算已更新')
    return redirect(url_for('index'))

@app.route('/backup')
def backup():
    return send_file(DATA_FILE, as_attachment=True, download_name=f'backup_{datetime.now().strftime("%Y%m%d")}.csv')

if __name__ == '__main__':
    # 自動開啟瀏覽器
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    
    # 啟動伺服器
    app.run(debug=True, port=5000)
