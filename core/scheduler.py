"""
播放调度器
定时检查并触发播放任务
"""

import threading
import time
from datetime import datetime

class Scheduler:
    """播放调度器类"""
    
    def __init__(self, on_schedule_trigger=None):
        """
        初始化调度器
        :param on_schedule_trigger: 触发播放时的回调函数(schedule)
        """
        self.schedules = []
        self.on_schedule_trigger = on_schedule_trigger
        self.running = False
        self.scheduler_thread = None
        self.last_checked_days = {}  # 记录每个计划上次触发的日期，避免同一天重复触发
    
    def add_schedule(self, schedule):
        """添加播放计划"""
        self.schedules.append(schedule)
    
    def remove_schedule(self, schedule_id):
        """移除播放计划"""
        self.schedules = [s for s in self.schedules if s.get('id') != schedule_id]
        # 清除该计划的触发记录
        if schedule_id in self.last_checked_days:
            del self.last_checked_days[schedule_id]
    
    def update_schedule(self, schedule_id, updated_schedule):
        """更新播放计划"""
        for i, s in enumerate(self.schedules):
            if s.get('id') == schedule_id:
                self.schedules[i] = updated_schedule
                # 清除触发记录，允许重新触发
                if schedule_id in self.last_checked_days:
                    del self.last_checked_days[schedule_id]
                break
    
    def set_schedules(self, schedules):
        """设置所有播放计划"""
        self.schedules = schedules
        self.last_checked_days = {}  # 清除所有触发记录
    
    def start(self):
        """启动调度器"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_worker, daemon=True)
            self.scheduler_thread.start()
    
    def stop(self):
        """停止调度器"""
        self.running = False
    
    def _scheduler_worker(self):
        """调度器工作线程"""
        while self.running:
            try:
                now = datetime.now()
                current_time = now.strftime("%H:%M")
                current_weekday = now.strftime("%A").lower()  # monday, tuesday, etc.
                
                for schedule in self.schedules:
                    schedule_id = schedule.get('id')
                    schedule_time = schedule.get('time', '')
                    schedule_days = schedule.get('days', [])
                    
                    # 检查是否匹配当前时间和周几
                    if (current_time == schedule_time and 
                        current_weekday in schedule_days):
                        
                        # 检查今天是否已经触发过（避免重复触发）
                        today = now.strftime("%Y-%m-%d")
                        last_trigger_date = self.last_checked_days.get(schedule_id)
                        
                        if last_trigger_date != today:
                            # 触发播放
                            if self.on_schedule_trigger:
                                self.on_schedule_trigger(schedule)
                            self.last_checked_days[schedule_id] = today
                
                # 每秒检查一次
                time.sleep(1)
                
            except Exception as e:
                print(f"调度器错误: {e}")
                time.sleep(1)
    
    def get_next_play_time(self):
        """获取下一个播放时间"""
        if not self.schedules:
            return None
        
        now = datetime.now()
        current_time = now.time()
        current_weekday = now.strftime("%A").lower()
        
        next_times = []
        
        for schedule in self.schedules:
            schedule_time_str = schedule.get('time', '')
            schedule_days = schedule.get('days', [])
            
            if not schedule_time_str or not schedule_days:
                continue
            
            try:
                schedule_time = datetime.strptime(schedule_time_str, "%H:%M").time()
                
                # 检查是否在今天且还未到时间
                if current_weekday in schedule_days and schedule_time > current_time:
                    next_times.append({
                        'time': schedule_time_str,
                        'schedule': schedule
                    })
                
                # 检查下周的播放时间
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
        
        # 返回最近的播放时间
        next_times.sort(key=lambda x: x.get('time', ''))
        return next_times[0]

