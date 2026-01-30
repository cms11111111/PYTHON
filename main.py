import os
import csv
import json
import shutil
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.core.window import Window
from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line

# --- 1. 資料管理 ---
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
                    reader = csv.reader(f); next(reader, None)
                    for row in reader: r.append(row)
                except: pass
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

# --- 2. 介面元件 ---
class TkLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = (0, 0, 0, 1)
        self.bind(size=self._update_text_size)
    def _update_text_size(self, *args): self.text_size = self.size

class TkButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.9, 0.9, 0.9, 1)
        self.color = (0, 0, 0, 1)

class TkTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False; self.write_tab = False
        self.background_normal = ''; self.background_active = ''
        self.background_color = (0.95, 0.95, 0.95, 1)
        self.foreground_color = (0, 0, 0, 1)
        self.padding = [5, 5]; self.font_size = 16
        self.halign = 'center'

class RecordRow(BoxLayout):
    def __init__(self, data, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'; self.size_hint_y = None; self.height = 50; self.padding = 5
        self.data = data; self.is_selected = is_selected
        with self.canvas.before:
            self.bg_color = Color(*(0.8, 0.9, 1, 1) if is_selected else (1, 1, 1, 1))
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            Color(0.8, 0.8, 0.8, 1)
            self.line = Line(points=[self.x, self.y, self.width, self.y], width=1)
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.add_widget(TkLabel(text=data[0], size_hint_x=0.3, font_size=12, halign='center',valign='middle'))
        self.add_widget(TkLabel(text=data[2], size_hint_x=0.15, font_size=12, halign='center',valign='middle'))
        self.add_widget(TkLabel(text=data[4], size_hint_x=0.35, font_size=12, halign='center',valign='middle'))
        self.add_widget(TkLabel(text=data[3], size_hint_x=0.2, font_size=12, halign='center',valign='middle'))
    def update_graphics(self, *args):
        self.bg_rect.pos = self.pos; self.bg_rect.size = self.size
        self.line.points = [self.x, self.y, self.x + self.width, self.y]
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            App.get_running_app().on_row_selected(self)
            return True
        return super().on_touch_down(touch)

# --- 3. 主程式 ---
class DailyTrackerApp(App):
    def find_chinese_font(self):
        font_paths = ["font.ttf", "msjh.ttc", "C:\\Windows\\Fonts\\msjh.ttc"]
        for p in font_paths:
            if os.path.exists(p): return p
        return None

    def build(self):
        font_path = self.find_chinese_font()
        if font_path: LabelBase.register(DEFAULT_FONT, font_path)
        self.dm = DataManager(); self.title = "日常收支"; self.selected_row_data = None
        
        root = BoxLayout(orientation='vertical')
        with root.canvas.before:
            Color(1, 1, 1, 1); self.root_rect = Rectangle(pos=root.pos, size=Window.size)
        root.bind(pos=lambda i,v: setattr(self.root_rect, 'pos', i.pos), size=lambda i,v: setattr(self.root_rect, 'size', i.size))

        # 頂部概況
        self.header_stats = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        with self.header_stats.canvas.before:
            Color(0, 0.47, 0.84, 1); self.rect = Rectangle(pos=self.header_stats.pos, size=self.header_stats.size)
        self.header_stats.bind(pos=lambda i,v: setattr(self.rect, 'pos', i.pos), size=lambda i,v: setattr(self.rect, 'size', i.size))
        self.header_stats.add_widget(Label(text="本月收支概況", bold=True, font_size=18, color=(1,1,1,1)))
        self.lbl_stats = Label(text="預算: 0  淨額: 0  剩餘: 0", font_size=16, color=(1,1,1,1))
        self.header_stats.add_widget(self.lbl_stats)
        root.add_widget(self.header_stats)

        # Tabs
        tp = TabbedPanel(do_default_tab=False, background_color=(1, 1, 1, 1), background_image='', tab_width=80)
        
        # Tab 1: 記帳
        tab1 = TabbedPanelItem(text="記帳")
        t1 = BoxLayout(orientation='vertical', padding=10, spacing=8)
        # 日期
        r_d = BoxLayout(size_hint_y=None, height=35, spacing=5)
        r_d.add_widget(TkLabel(text="日期:", size_hint_x=None, width=50, bold=True, halign='center'))
        self.t1_date = TkTextInput(text=datetime.now().strftime('%Y-%m-%d'), font_size=12); r_d.add_widget(self.t1_date)
        t1.add_widget(r_d)
        # 類型
        r_t = BoxLayout(size_hint_y=None, height=35, spacing=10)
        r_t.add_widget(TkLabel(text="類型:", size_hint_x=None, width=50, bold=True, halign='center'))
        self.btn_exp = ToggleButton(text='支出', group='type', state='down', background_normal='', background_color=(0, 0.47, 0.84, 1), color=(1,1,1,1))
        self.btn_inc = ToggleButton(text='收入', group='type', background_normal='', background_color=(0.9, 0.9, 0.9, 1), color=(0,0,0,1))
        def on_type(w, v):
            w.background_color = (0, 0.47, 0.84, 1) if v=='down' else (0.9, 0.9, 0.9, 1)
            w.color = (1,1,1,1) if v=='down' else (0,0,0,1)
        self.btn_exp.bind(state=on_type); self.btn_inc.bind(state=on_type)
        r_t.add_widget(self.btn_exp); r_t.add_widget(self.btn_inc); t1.add_widget(r_t)
        # 金額/用途
        for l, a in [("金額:", "t1_amt"), ("用途:", "t1_use")]:
            r = BoxLayout(size_hint_y=None, height=35, spacing=5)
            r.add_widget(TkLabel(text=l, size_hint_x=None, width=50, bold=True, halign='center'))
            ti = TkTextInput(); setattr(self, a, ti); r.add_widget(ti); t1.add_widget(r)
        self.t1_amt.background_color = (1, 1, 0.8, 1)
        # 類別
        t1.add_widget(TkLabel(text="類別:", size_hint_y=None, height=20, halign='left'))
        cat_g = GridLayout(cols=3, spacing=3, size_hint_y=None, height=60)
        self.cat_btns = {}
        for c in ["餐飲", "交通", "購物", "娛樂", "醫療", "其他"]:
            b = TkButton(text=c, font_size=12); b.bind(on_release=self.on_cat_select); cat_g.add_widget(b); self.cat_btns[c] = b
        t1.add_widget(cat_g)
        btn_s = Button(text="儲存記錄", background_color=(0, 0.47, 0.84, 1), size_hint_y=None, height=45, bold=True); btn_s.bind(on_release=self.save_record)
        t1.add_widget(btn_s); t1.add_widget(Label()); tab1.add_widget(t1); tp.add_widget(tab1)

        # Tab 2: 查詢
        tab2 = TabbedPanelItem(text="查詢")
        t2 = BoxLayout(orientation='vertical', padding=5, spacing=5)
        r_b = BoxLayout(size_hint_y=None, height=40, spacing=5)
        for text, cmd in [("設定預算", self.ask_budget), ("備份資料", self.do_backup), ("刪除選取", self.do_delete)]:
            b = Button(text=text, background_color=(0.6, 0.6, 0.6, 1) if "刪除" not in text else (0.8, 0.2, 0.2, 1))
            b.bind(on_release=cmd); r_b.add_widget(b)
        t2.add_widget(r_b); t2.add_widget(self._create_table_header())
        self.sv = ScrollView(size_hint=(1, 1)); self.list_container = GridLayout(cols=1, spacing=1, size_hint_y=None)
        self.list_container.bind(minimum_height=self.list_container.setter('height'))
        self.sv.add_widget(self.list_container); t2.add_widget(self.sv); tab2.add_widget(t2); tp.add_widget(tab2)

        # Tab 3: 日期
        tab3 = TabbedPanelItem(text="日期")
        t3 = BoxLayout(orientation='vertical', padding=5, spacing=5)
        fb = BoxLayout(orientation='vertical', size_hint_y=None, height=110, padding=10, spacing=5)
        with fb.canvas.before: Color(0.95, 0.95, 0.95, 1); self.f_rect = Rectangle(pos=fb.pos, size=fb.size)
        fb.bind(pos=lambda i,v: setattr(self.f_rect, 'pos', i.pos), size=lambda i,v: setattr(self.f_rect, 'size', i.size))
        for l, a in [("起:", "t3_start"), ("迄:", "t3_end")]:
            r = BoxLayout(height=30, size_hint_y=None)
            r.add_widget(TkLabel(text=l, size_hint_x=None, width=30, bold=True, halign='center'))
            ti = TkTextInput(text=datetime.now().strftime('%Y-%m-01' if 'start' in a else '%Y-%m-%d'), font_size=12); setattr(self, a, ti); r.add_widget(ti); fb.add_widget(r)
        btn_q = Button(text="查詢", background_color=(1, 0.8, 0.4, 1), color=(0,0,0,1), size_hint_y=None, height=35, bold=True); btn_q.bind(on_release=self.do_search)
        fb.add_widget(btn_q); t3.add_widget(fb)
        self.lbl_q_tot = TkLabel(text="總計: $0", size_hint_y=None, height=30, bold=True, color=(1, 0, 0, 1), halign='center')
        t3.add_widget(self.lbl_q_tot); t3.add_widget(self._create_table_header())
        self.sv_q = ScrollView(size_hint=(1, 1)); self.q_container = GridLayout(cols=1, spacing=1, size_hint_y=None)
        self.q_container.bind(minimum_height=self.q_container.setter('height'))
        self.sv_q.add_widget(self.q_container); t3.add_widget(self.sv_q); tab3.add_widget(t3); tp.add_widget(tab3)

        root.add_widget(tp)
        self.selected_cat = "餐飲"; self.on_cat_select(self.cat_btns["餐飲"]); self.update_ui()
        return root

    def _create_table_header(self):
        h = BoxLayout(size_hint_y=None, height=30)
        with h.canvas.before: Color(0.9, 0.9, 0.9, 1); r = Rectangle(pos=h.pos, size=h.size)
        h.bind(pos=lambda i,v: setattr(r, 'pos', i.pos), size=lambda i,v: setattr(r, 'size', i.size))
        h.add_widget(TkLabel(text="日期", size_hint_x=0.3, bold=True, halign='center'))
        h.add_widget(TkLabel(text="類別", size_hint_x=0.15, bold=True, halign='center'))
        h.add_widget(TkLabel(text="用途", size_hint_x=0.35, bold=True, halign='center'))
        h.add_widget(TkLabel(text="金額", size_hint_x=0.2, bold=True, halign='center'))
        return h

    def on_cat_select(self, inst):
        self.selected_cat = inst.text; self.t1_use.text = inst.text
        for c, b in self.cat_btns.items():
            b.background_color = (0.9, 0.9, 0.9, 1) if c != self.selected_cat else (0, 0.47, 0.84, 1)
            b.color = (0, 0, 0, 1) if c != self.selected_cat else (1, 1, 1, 1)

    def save_record(self, inst):
        d, a, u = self.t1_date.text, self.t1_amt.text, self.t1_use.text
        if not a: return
        try:
            v = float(a); v = -abs(v) if self.btn_exp.state == 'down' else abs(v)
            self.dm.add_record(d, self.selected_cat, str(int(v)), u)
            self.t1_amt.text = ""; self.t1_use.text = "儲存OK"; self.update_ui()
            Clock.schedule_once(lambda dt: setattr(self.t1_use, 'text', self.selected_cat), 1)
        except: pass

    def on_row_selected(self, row):
        for c in self.list_container.children: c.bg_color.rgba = (1, 1, 1, 1)
        row.bg_color.rgba = (0.8, 0.9, 1, 1); self.selected_row_data = row.data

    def do_delete(self, inst):
        if self.selected_row_data: self.dm.delete_record_by_data(self.selected_row_data); self.selected_row_data = None; self.update_ui()

    def do_search(self, inst):
        self.q_container.clear_widgets()
        try:
            s = datetime.strptime(self.t3_start.text, "%Y-%m-%d"); e = datetime.strptime(self.t3_end.text, "%Y-%m-%d")
            recs = self.dm.get_records(); tot = 0
            for r in reversed(recs):
                try:
                    rd = datetime.strptime(r[0], "%Y-%m-%d")
                    if s <= rd <= e: self.q_container.add_widget(RecordRow(r)); tot += int(float(r[3]))
                except: pass
            self.lbl_q_tot.text = f"總計: ${tot:,}"
        except: pass

    def ask_budget(self, inst):
        c = BoxLayout(orientation='vertical', padding=10, spacing=10); ti = TkTextInput(text=str(self.dm.get_budget()), input_type='number'); c.add_widget(ti)
        b = Button(text="確定", size_hint_y=None, height=40); p = Popup(title="設定預算", content=c, size_hint=(0.8, 0.4))
        def ok(btn):
            if ti.text.isdigit(): self.dm.set_budget(ti.text); self.update_ui()
            p.dismiss()
        b.bind(on_release=ok); c.add_widget(b); p.open()

    def do_backup(self, inst): self.dm.backup_data(); self.update_ui()

    def update_ui(self):
        bud = self.dm.get_budget(); recs = self.dm.get_records(); cm = datetime.now().strftime('%Y-%m')
        exp = sum(abs(int(float(r[3]))) for r in recs if r[0].startswith(cm) and int(float(r[3])) < 0)
        net = sum(int(float(r[3])) for r in recs if r[0].startswith(cm))
        self.lbl_stats.text = f"預算: {bud:,}  淨額: {net:,}  剩餘: {bud-exp:,}"
        self.list_container.clear_widgets()
        for r in reversed(recs): self.list_container.add_widget(RecordRow(r))

from kivy.lang import Builder
Builder.load_string('''
<TabbedPanelItem>:
    background_normal: ''
    background_color: (0.4, 0.4, 0.4, 1) if self.state == 'normal' else (0, 0.47, 0.84, 1)
    color: (1, 1, 1, 1)
''')

if __name__ == '__main__':
    Window.size = (360, 680); DailyTrackerApp().run()
