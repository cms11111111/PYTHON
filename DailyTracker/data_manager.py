import pandas as pd
import os
from datetime import datetime
import shutil

class DataManager:
    def __init__(self, data_file='records.csv', config_file='config.json'):
        # 取得 data_manager.py 所在的目錄 (即 DailyTracker 資料夾的絕對路徑)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.data_file = os.path.join(base_dir, data_file)
        self.config_file = os.path.join(base_dir, config_file)
        self.backup_dir = os.path.join(base_dir, 'backups')
        self._init_files()

    def _init_files(self):
        # 初始化 CSV
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=['日期', '時間', '類別', '金額', '用途'])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
        
        # 初始化備份目錄
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def add_record(self, date, time, category, amount, description):
        df = pd.read_csv(self.data_file, encoding='utf-8-sig')
        new_row = {
            '日期': date,
            '時間': time,
            '類別': category,
            '金額': float(amount),
            '用途': description
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(self.data_file, index=False, encoding='utf-8-sig')

    def get_records(self):
        if not os.path.exists(self.data_file):
            return pd.DataFrame()
        return pd.read_csv(self.data_file, encoding='utf-8-sig')

    def get_monthly_stats(self, month_str=None):
        """
        month_str: '2026-01'
        """
        if month_str is None:
            month_str = datetime.now().strftime('%Y-%m')
        
        df = self.get_records()
        if df.empty:
            return 0, 0
            
        # 轉換日期格式以便計算
        df['日期'] = pd.to_datetime(df['日期'])
        monthly_df = df[df['日期'].dt.strftime('%Y-%m') == month_str]
        total_spent = monthly_df['金額'].sum()
        
        return total_spent, monthly_df

    def export_backup(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'backup_{timestamp}.csv')
        shutil.copy2(self.data_file, backup_path)
        return backup_path

    def save_budget(self, amount):
        import json
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump({'budget': float(amount)}, f)

    def get_budget(self):
        import json
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('budget', 0)
        return 0
