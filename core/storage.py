"""
資料持久化模組
負責播放計劃的保存和載入
"""

import json
import os
import sys

class Storage:
    """資料存儲管理類別"""
    
    def __init__(self):
        """初始化存儲路徑"""
        if getattr(sys, 'frozen', False):
            # 打包後的exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # 開發模式
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.data_dir = os.path.join(self.base_path, 'data')
        self.schedule_file = os.path.join(self.data_dir, 'schedule.json')
        
        # 確保data目錄存在
        os.makedirs(self.data_dir, exist_ok=True)
    
    def load_schedules(self):
        """載入播放計劃"""
        if not os.path.exists(self.schedule_file):
            return {"schedules": []}
        
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 驗證檔案路徑是否存在
                for schedule in data.get('schedules', []):
                    for file_path in schedule.get('files', []):
                        if not os.path.exists(file_path):
                            schedule.setdefault('invalid_files', []).append(file_path)
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"載入播放計劃失敗: {e}")
            return {"schedules": []}
    
    def save_schedules(self, schedules_data):
        """保存播放計劃"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedules_data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存播放計劃失敗: {e}")
            return False
    
    def validate_file_path(self, file_path):
        """驗證檔案路徑是否存在"""
        return os.path.exists(file_path) and os.path.isfile(file_path)
