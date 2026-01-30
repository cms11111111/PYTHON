import os
import csv
import json
import shutil
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.core.window import Window
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
from kivy.clock import Clock

# --- 1. 資料管理 (與原版邏輯相同) ---
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
                try:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader: r.append(row)
                except StopIteration: pass
        return r
    def delete_record(self, index): # Kivy版改用索引刪除較方便
        recs = self.get_records()
        # 因為列表是倒序顯示的，所以要反向計算真實索引
        real_index = len(recs) - 1 - index
        if 0 <= real_index < len(recs):
            del recs[real_index]
            with open(DATA_FILE, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.writer(f)
                w.writerow(['日期', '時間', '類別', '金額', '用途'])
                w.writerows(recs)
    def get_budget(self):
        try:
            with open(CONFIG_FILE, 'r') as f: return json.load(f).get('budget', 0)
        except: return 0
    def set_budget(self, a): 
        with open(CONFIG_FILE, 'w') as f: json.dump({'budget': int(a)}, f)

# --- 2. Kivy 介面元件 ---

# 設定中文字型 (嘗試尋找常見中文字型)
# 注意：在 Android 上通常需要將 .ttf 檔案放在專案目錄下並指定檔名
# 這裡為了 PC 測試，先嘗試抓系統字型
def find_chinese_font():
    font_paths = [
        "msjh.ttc", # Windows 微軟正黑體
        "simhei.ttf", # 常見黑體
        "/system/fonts/DroidSansFallback.ttf", # Android 舊版
        "/system/fonts/NotoSansCJK-Regular.ttc", # Android 新版
    ]
    # 如果有自帶 font.ttf 最好
    if os.path.exists("font.ttf"): return "font.ttf"
    
    # Windows 系統路徑搜尋
    if os.name == 'nt':
        win_font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        if os.path.exists(os.path.join(win_font_dir, 'msjh.ttc')):
            return os.path.join(win_font_dir, 'msjh.ttc')
            
    return None # 使用預設

CHINESE_FONT = find_chinese_font()
if CHINESE_FONT:
    LabelBase.register(DEFAULT_FONT, CHINESE_FONT)

class SelectableRow(RecycleDataViewBehavior, BoxLayout):
    ''' 列表中的每一列 '''
    text_date = StringProperty("")
    text_cat = StringProperty("")
    text_use = StringProperty("")
    text_amt = StringProperty("")
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.text_date = data['text_date']
        self.text_cat = data['text_cat']
        self.text_use = data['text_use']
        self.text_amt = data['text_amt']
        return super(SelectableRow, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if super(SelectableRow, self).on_touch_down(touch): return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    ''' 列表佈局管理 '''
    pass

class DailyTrackerApp(App):
    def build(self):
        self.dm = DataManager()
        self.title = "日常收支"
        
        # 主佈局 (垂直)
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # --- 1. 頂部概況 ---
        self.lbl_stats = Label(text="預算: 0 | 支出: 0 | 剩餘: 0", size_hint_y=None, height=40, font_size='16sp')
        root.add_widget(self.lbl_stats)
        
        # --- 2. 輸入區 ---
        input_grid = GridLayout(cols=2, size_hint_y=None, height=120, spacing=5)
        
        input_grid.add_widget(Label(text="日期"))
        self.txt_date = TextInput(text=datetime.now().strftime('%Y-%m-%d'), multiline=False)
        input_grid.add_widget(self.txt_date)
        
        input_grid.add_widget(Label(text="金額"))
        self.txt_amt = TextInput(multiline=False, input_type='number')
        input_grid.add_widget(self.txt_amt)
        
        input_grid.add_widget(Label(text="用途"))
        self.txt_use = TextInput(multiline=False)
        input_grid.add_widget(self.txt_use)
        
        root.add_widget(input_grid)
        
        # --- 3. 類別按鈕 (Grid) ---
        cat_grid = GridLayout(cols=3, size_hint_y=None, height=80, spacing=5)
        cats = ["餐飲", "交通", "購物", "娛樂", "醫療", "其他"]
        self.cat_btns = []
        for c in cats:
            btn = Button(text=c)
            btn.bind(on_release=self.on_cat_select)
            cat_grid.add_widget(btn)
            self.cat_btns.append(btn)
        root.add_widget(cat_grid)
        self.selected_cat = "餐飲"
        
        # --- 4. 功能按鈕 ---
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_save = Button(text="儲存記錄", background_color=(0, 0.7, 1, 1))
        btn_save.bind(on_release=self.save_record)
        btn_box.add_widget(btn_save)
        
        btn_del = Button(text="刪除選取", background_color=(1, 0, 0, 1))
        btn_del.bind(on_release=self.delete_selected)
        btn_box.add_widget(btn_del)
        
        root.add_widget(btn_box)
        
        # --- 5. 資料列表 (Header + RecycleView) ---
        header = BoxLayout(size_hint_y=None, height=30)
        header.add_widget(Label(text="日期", size_hint_x=0.3))
        header.add_widget(Label(text="類別", size_hint_x=0.15))
        header.add_widget(Label(text="用途", size_hint_x=0.35))
        header.add_widget(Label(text="金額", size_hint_x=0.2))
        root.add_widget(header)
        
        self.rv = RecycleView()
        self.rv.viewclass = 'SelectableRow'
        self.rv_layout = SelectableRecycleBoxLayout(default_size=(None, 40), default_size_hint=(1, None), size_hint_y=None, orientation='vertical')
        self.rv_layout.bind(minimum_height=self.rv_layout.setter('height'))
        self.rv.add_widget(self.rv_layout)
        root.add_widget(self.rv)
        
        self.update_ui()
        return root

    def on_cat_select(self, instance):
        self.selected_cat = instance.text
        self.txt_use.text = instance.text
        # 簡單的高亮效果
        for btn in self.cat_btns:
            btn.background_color = (1, 1, 1, 1) if btn != instance else (0, 1, 0, 1)

    def save_record(self, instance):
        d = self.txt_date.text
        a = self.txt_amt.text
        u = self.txt_use.text
        if not a or not a.isdigit(): return
        
        self.dm.add_record(d, self.selected_cat, a, u)
        self.txt_amt.text = ""
        self.txt_use.text = "儲存OK"
        self.update_ui()
        Clock.schedule_once(lambda dt: setattr(self.txt_use, 'text', self.selected_cat), 1)

    def delete_selected(self, instance):
        # 取得選取的索引
        for i in self.rv_layout.selected_nodes:
            self.dm.delete_record(i)
        self.rv_layout.clear_selection()
        self.update_ui()

    def update_ui(self):
        bud = self.dm.get_budget()
        recs = self.dm.get_records()
        
        # 統計
        cm = datetime.now().strftime('%Y-%m')
        sp = sum(int(float(r[3])) for r in recs if r[0].startswith(cm))
        self.lbl_stats.text = f"預算: {bud} | 支出: {sp} | 剩餘: {bud-sp}"
        
        # 更新列表 (倒序)
        data = []
        for r in reversed(recs):
            data.append({
                'text_date': r[0],
                'text_cat': r[2],
                'text_use': r[4],
                'text_amt': r[3]
            })
        self.rv.data = data

# KV Language 定義列表樣式
from kivy.lang import Builder
Builder.load_string('''
<SelectableRow>:
    canvas.before:
        Color:
            rgba: (.0, 0.9, .1, .3) if self.selected else (0, 0, 0, 1)
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.text_date
        size_hint_x: 0.3
    Label:
        text: root.text_cat
        size_hint_x: 0.15
    Label:
        text: root.text_use
        size_hint_x: 0.35
    Label:
        text: root.text_amt
        size_hint_x: 0.2
''')

if __name__ == '__main__':
    # 設定視窗大小以便電腦預覽 (模擬手機)
    Window.size = (360, 680)
    DailyTrackerApp().run()
