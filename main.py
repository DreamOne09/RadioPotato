"""
自动广播系统 - 主程序入口

本程式由僑務委員會外交替代役 李孟一老師所開發
如有問題可用line聯繫：dreamone09

GitHub: https://github.com/DreamOne09/RadioPotato
"""

import sys
import os

# 确保程序目录在Python路径中
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是开发模式
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from ui.main_window import MainWindow

def main():
    """主程序入口"""
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()

