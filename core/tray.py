"""
系统托盘模块
"""

import pystray
from PIL import Image, ImageDraw
import threading

class SystemTray:
    """系统托盘管理器"""
    
    def __init__(self, on_show=None, on_quit=None, on_double_click=None):
        """
        初始化系统托盘
        :param on_show: 显示窗口的回调函数
        :param on_quit: 退出程序的回调函数
        :param on_double_click: 双击托盘图标的回调函数
        """
        self.on_show = on_show
        self.on_quit = on_quit
        self.on_double_click = on_double_click
        self.icon = None
        self.is_blinking = False
        self.blink_thread = None
        
    def create_icon(self):
        """创建托盘图标"""
        # 创建一个简单的图标
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white', outline='black')
        return image
    
    def start(self):
        """启动系统托盘"""
        image = self.create_icon()
        
        menu = pystray.Menu(
            pystray.MenuItem('显示窗口', self._show_window),
            pystray.MenuItem('退出', self._quit)
        )
        
        self.icon = pystray.Icon("RadioPotato", image, "自动广播系统", menu)
        
        # 双击事件
        if self.on_double_click:
            # pystray的双击事件需要通过其他方式实现
            pass
        
        # 在后台线程运行图标
        threading.Thread(target=self._run_icon, daemon=True).start()
    
    def _run_icon(self):
        """运行图标（需要在独立线程中）"""
        if self.icon:
            self.icon.run()
    
    def _show_window(self, icon=None, item=None):
        """显示窗口"""
        if self.on_show:
            self.on_show()
    
    def _quit(self, icon=None, item=None):
        """退出程序"""
        if self.on_quit:
            self.on_quit()
    
    def stop_blinking(self):
        """停止闪烁"""
        self.is_blinking = False
        # 确保图标可见
        if self.icon:
            try:
                self.icon.visible = True
            except Exception:
                pass
    
    def start_blinking(self):
        """开始闪烁"""
        if not self.is_blinking:
            self.is_blinking = True
            if self.blink_thread is None or not self.blink_thread.is_alive():
                self.blink_thread = threading.Thread(target=self._blink_worker, daemon=True)
                self.blink_thread.start()
    
    def _blink_worker(self):
        """闪烁工作线程"""
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
        """停止系统托盘"""
        if self.icon:
            self.icon.stop()
        self.stop_blinking()

