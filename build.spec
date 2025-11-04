# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# 檢查圖標檔案
icon_file = None
if os.path.exists('RadioOne Logo.ico'):
    icon_file = 'RadioOne Logo.ico'
elif os.path.exists('RadioOne Logo.png'):
    icon_file = 'RadioOne Logo.png'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('RadioOne Logo.png', '.'),  # 包含Logo圖標
        ('Radio One Big Logo.png', '.'),  # 包含Big Logo
    ],
    hiddenimports=[
        'pystray._win32',
        'win32timezone',
        'tkinterdnd2',
        'PIL._tkinter_finder',
        'win10toast'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas'],  # 排除不需要的大型库
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='radioone',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,  # 使用ICO或PNG圖標，內嵌到exe中，用於任務欄顯示
)
