"""
通知系統
支援Windows通知和視窗內狀態顯示
"""

try:
    from win10toast import ToastNotifier
    HAS_WIN10TOAST = True
except ImportError:
    HAS_WIN10TOAST = False

class Notifier:
    """通知管理器"""
    
    def __init__(self):
        """初始化通知系統"""
        self.toast = None
        if HAS_WIN10TOAST:
            try:
                self.toast = ToastNotifier()
            except Exception as e:
                print(f"初始化通知系統失敗: {e}")
    
    def notify_playback_start(self, file_name):
        """
        通知播放開始
        :param file_name: 檔案名稱
        """
        title = "自動廣播系統"
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
                print(f"發送通知失敗: {e}")
    
    def notify_schedule_triggered(self, schedule_name):
        """
        通知播放計劃已觸發
        :param schedule_name: 計劃名稱
        """
        title = "自動廣播系統"
        message = f"播放計劃已觸發: {schedule_name}"
        
        if self.toast:
            try:
                self.toast.show_toast(
                    title,
                    message,
                    duration=3,
                    threaded=True
                )
            except Exception as e:
                print(f"發送通知失敗: {e}")
