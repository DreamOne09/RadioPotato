"""
通知系统
支持Windows通知和窗口内状态显示
"""

try:
    from win10toast import ToastNotifier
    HAS_WIN10TOAST = True
except ImportError:
    HAS_WIN10TOAST = False

class Notifier:
    """通知管理器"""
    
    def __init__(self):
        """初始化通知系统"""
        self.toast = None
        if HAS_WIN10TOAST:
            try:
                self.toast = ToastNotifier()
            except Exception as e:
                print(f"初始化通知系统失败: {e}")
    
    def notify_playback_start(self, file_name):
        """
        通知播放开始
        :param file_name: 文件名
        """
        title = "自动广播系统"
        message = f"正在播放: {file_name}"
        
        # Windows通知
        if self.toast:
            try:
                self.toast.show_toast(
                    title,
                    message,
                    duration=3,
                    threaded=True
                )
            except Exception as e:
                print(f"发送通知失败: {e}")
    
    def notify_schedule_triggered(self, schedule_name):
        """
        通知播放计划已触发
        :param schedule_name: 计划名称
        """
        title = "自动广播系统"
        message = f"播放计划已触发: {schedule_name}"
        
        if self.toast:
            try:
                self.toast.show_toast(
                    title,
                    message,
                    duration=3,
                    threaded=True
                )
            except Exception as e:
                print(f"发送通知失败: {e}")

