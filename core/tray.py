"""
系統託盤模組
"""

import pystray
from PIL import Image, ImageDraw
import threading

class SystemTray:
    """系統託盤管理器"""
    
    def __init__(self, on_show=None, on_quit=None, on_double_click=None):
        """
        初始化系統託盤
        :param on_show: 顯示視窗的回調函數
        :param on_quit: 退出程式的回調函數
        :param on_double_click: 雙擊託盤圖示的回調函數
        """
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_double_click = on_double_click
        self.icon = None
        self.is_blinking = False
        self.blink_thread = None
        
    def create_icon(self):
        """建立託盤圖示"""
        # 建立一個簡單的圖示
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white', outline='black')
        return image
    
    def start(self):
        """啟動系統託盤"""
        image = self.create_icon()
        
        menu = pystray.Menu(
            pystray.MenuItem('顯示視窗', self._show_window),
            pystray.MenuItem('退出', self._quit)
        )
        
        self.icon = pystray.Icon("radioone", image, "自動廣播系統", menu)
        
        # 雙擊事件
        if self.on_double_click:
            # pystray的雙擊事件需要通過其他方式實現
            pass
        
        # 在後台執行緒運行圖示
        threading.Thread(target=self._run_icon, daemon=True).start()
    
    def _run_icon(self):
        """運行圖示（需要在獨立執行緒中）"""
        if self.icon:
            self.icon.run()
    
    def _show_window(self, icon=None, item=None):
        """顯示視窗"""
        if self.on_show:
            self.on_show()
    
    def _quit(self, icon=None, item=None):
        """退出程式"""
        if self.on_quit:
            self.on_quit()
    
    def stop_blinking(self):
        """停止閃爍"""
        self.is_blinking = False
        # 確保圖示可見
        if self.icon:
            try:
                self.icon.visible = True
            except Exception:
                pass
    
    def start_blinking(self):
        """開始閃爍"""
        if not self.is_blinking and self.icon:
            self.is_blinking = True
            if self.blink_thread is None or not self.blink_thread.is_alive():
                self.blink_thread = threading.Thread(target=self._blink_worker, daemon=True)
                self.blink_thread.start()
    
    def _blink_worker(self):
        """閃爍工作執行緒"""
        import time
        is_visible = True
        while self.is_blinking and self.icon:
            try:
                if is_visible:
                    self.icon.visible = False
                else:
                    self.icon.visible = True
                is_visible = not is_visible
                time.sleep(0.5)
            except Exception:
                break
    
    def stop(self):
        """停止系統託盤"""
        if self.icon:
            self.icon.stop()
        self.stop_blinking()
