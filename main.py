"""
自動廣播系統 - 主程式入口

本程式由僑務委員會外交替代役 李孟一老師所開發
如有問題可用line聯繫：dreamone09

GitHub: https://github.com/DreamOne09/radioone
"""

import sys
import os

# 確保程式目錄在Python路徑中
if getattr(sys, 'frozen', False):
    # 如果是打包後的exe
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是開發模式
    application_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, application_path)

from ui.main_window import MainWindow

def main():
    """主程式入口"""
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()
