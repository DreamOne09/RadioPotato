"""
開機自動啟動模組
支援Windows開機自動啟動功能
"""

import os
import sys
import winreg

def get_exe_path():
    """獲取exe檔案路徑"""
    if getattr(sys, 'frozen', False):
        # 打包後的exe
        return sys.executable
    else:
        # 開發模式，返回main.py的路徑
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, 'main.py')

def add_to_startup():
    """添加到開機啟動項"""
    try:
        exe_path = get_exe_path()
        
        # 如果是開發模式（main.py），需要用python運行
        if not getattr(sys, 'frozen', False):
            python_path = sys.executable
            command = f'"{python_path}" "{exe_path}"'
        else:
            command = f'"{exe_path}"'
        
        # 打開註冊表
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        # 添加啟動項
        winreg.SetValueEx(key, "RadioPotato", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        
        return True, "已添加到開機啟動"
    except Exception as e:
        return False, f"添加失敗: {str(e)}"

def remove_from_startup():
    """從開機啟動項移除"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        try:
            winreg.DeleteValue(key, "RadioPotato")
            winreg.CloseKey(key)
            return True, "已從開機啟動移除"
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False, "未找到啟動項"
    except Exception as e:
        return False, f"移除失敗: {str(e)}"

def is_in_startup():
    """檢查是否已添加到開機啟動"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        
        try:
            winreg.QueryValueEx(key, "RadioPotato")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False

