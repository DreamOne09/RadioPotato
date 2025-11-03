"""
数据持久化模块
负责播放计划的保存和加载
"""

import json
import os
import sys

class Storage:
    """数据存储管理类"""
    
    def __init__(self):
        """初始化存储路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # 开发模式
            self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.data_dir = os.path.join(self.base_path, 'data')
        self.schedule_file = os.path.join(self.data_dir, 'schedule.json')
        
        # 确保data目录存在
        os.makedirs(self.data_dir, exist_ok=True)
    
    def load_schedules(self):
        """加载播放计划"""
        if not os.path.exists(self.schedule_file):
            return {"schedules": []}
        
        try:
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 验证文件路径是否存在
                for schedule in data.get('schedules', []):
                    for file_path in schedule.get('files', []):
                        if not os.path.exists(file_path):
                            schedule.setdefault('invalid_files', []).append(file_path)
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载播放计划失败: {e}")
            return {"schedules": []}
    
    def save_schedules(self, schedules_data):
        """保存播放计划"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedules_data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"保存播放计划失败: {e}")
            return False
    
    def validate_file_path(self, file_path):
        """验证文件路径是否存在"""
        return os.path.exists(file_path) and os.path.isfile(file_path)

