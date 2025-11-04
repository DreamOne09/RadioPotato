"""
播放排程器
定時檢查並觸發播放任務
"""

import threading
import time
from datetime import datetime

class Scheduler:
    """播放排程器類別"""
    
    def __init__(self, on_schedule_trigger=None):
        """
        初始化排程器
        :param on_schedule_trigger: 觸發播放時的回調函數(schedule)
        """
        self.schedules = []
        self.on_schedule_trigger = on_schedule_trigger
        self.running = False
        self.scheduler_thread = None
        self.last_checked_days = {}  # 記錄每個計劃上次觸發的日期，避免同一天重複觸發
    
    def add_schedule(self, schedule):
        """添加播放計劃"""
        self.schedules.append(schedule)
    
    def remove_schedule(self, schedule_id):
        """移除播放計劃"""
        self.schedules = [s for s in self.schedules if s.get('id') != schedule_id]
        # 清除該計劃的觸發記錄
        if schedule_id in self.last_checked_days:
            del self.last_checked_days[schedule_id]
    
    def update_schedule(self, schedule_id, updated_schedule):
        """更新播放計劃"""
        for i, s in enumerate(self.schedules):
            if s.get('id') == schedule_id:
                self.schedules[i] = updated_schedule
                # 清除觸發記錄，允許重新觸發
                if schedule_id in self.last_checked_days:
                    del self.last_checked_days[schedule_id]
                break
    
    def set_schedules(self, schedules):
        """設定所有播放計劃"""
        self.schedules = schedules
        self.last_checked_days = {}  # 清除所有觸發記錄
    
    def start(self):
        """啟動排程器"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
            self.scheduler_thread.start()
    
    def stop(self):
        """停止排程器"""
        self.running = False
    
    def _scheduler_worker(self):
        """排程器工作執行緒"""
        # 星期名映射（使用weekday()數字避免語言依賴）
        weekday_map = {
            0: 'monday',      # 週一
            1: 'tuesday',     # 週二
            2: 'wednesday',   # 週三
            3: 'thursday',    # 週四
            4: 'friday',      # 週五
            5: 'saturday',    # 週六
            6: 'sunday'       # 週日
        }
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                # 使用weekday()獲取數字(0=週一, 6=週日)，避免語言依賴
                current_weekday = weekday_map[now.weekday()]
                
                for schedule in self.schedules:
                    schedule_id = schedule.get('id')
                    schedule_time = schedule.get('time', '')
                    schedule_days = schedule.get('days', [])
                    
                    # 檢查是否匹配當前時間和周幾
                    if (current_time == schedule_time and 
                        current_weekday in schedule_days):
                        
                        # 檢查今天是否已經觸發過（避免重複觸發）
                        today = now.strftime("%Y-%m-%d")
                        last_trigger_date = self.last_checked_days.get(schedule_id)
                        
                        # 使用更精確的時間戳記（包含秒），防止1秒內重複觸發
                        trigger_key = f"{schedule_id}_{today}_{current_time}"
                        last_trigger_time = self.last_checked_days.get(trigger_key)
                        current_timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
                        
                        if last_trigger_date != today or last_trigger_time is None:
                            # 觸發播放
                            if self.on_schedule_trigger:
                                self.on_schedule_trigger(schedule)
                            # 記錄觸發日期和時間戳
                            self.last_checked_days[schedule_id] = today
                            self.last_checked_days[trigger_key] = current_timestamp
                            print(f"✓ 觸發播放計劃: {schedule.get('name')} ({schedule_time})")
                
                # 每秒檢查一次
                time.sleep(1)
                
            except Exception as e:
                print(f"排程器錯誤: {e}")
                time.sleep(1)
    
    def get_next_play_time(self):
        """獲取下一個播放時間"""
        if not self.schedules:
            return None
        
        # 星期名映射（使用weekday()數字避免語言依賴）
        weekday_map = {
            0: 'monday',      # 週一
            1: 'tuesday',     # 週二
            2: 'wednesday',   # 週三
            3: 'thursday',    # 週四
            4: 'friday',      # 週五
            5: 'saturday',    # 週六
            6: 'sunday'       # 週日
        }
        
        now = datetime.now()
        current_time = now.time()
        # 使用weekday()獲取數字(0=週一, 6=週日)，避免語言依賴
        current_weekday = weekday_map[now.weekday()]
        
        next_times = []
        
        for schedule in self.schedules:
            schedule_time_str = schedule.get('time', '')
            schedule_days = schedule.get('days', [])
            
            if not schedule_time_str or not schedule_days:
                continue
            
            try:
                schedule_time = datetime.strptime(schedule_time_str, "%H:%M").time()
                
                # 檢查是否在今天且還未到時間
                if current_weekday in schedule_days and schedule_time > current_time:
                    next_times.append({
                        'time': schedule_time_str,
                        'schedule': schedule
                    })
                
                # 檢查下週的播放時間
                days_ahead = []
                weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                current_index = weekdays.index(current_weekday)
                
                for day in schedule_days:
                    day_index = weekdays.index(day)
                    if day_index > current_index:
                        days_ahead.append(day_index - current_index)
                    else:
                        days_ahead.append(7 - current_index + day_index)
                
                if days_ahead:
                    min_days = min(days_ahead)
                    next_times.append({
                        'time': schedule_time_str,
                        'schedule': schedule,
                        'days': min_days
                    })
            except ValueError:
                continue
        
        if not next_times:
            return None
        
        # 返回最近的播放時間
        next_times.sort(key=lambda x: x.get('time', ''))
        return next_times[0]
