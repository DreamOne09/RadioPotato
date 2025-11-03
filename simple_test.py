# -*- coding: utf-8 -*-
"""簡單測試腳本"""

import sys
import os

print("開始測試...")

# 測試導入模組
try:
    from core.storage import Storage
    print("✓ Storage 模組導入成功")
except Exception as e:
    print(f"✗ Storage 導入失敗: {e}")
    sys.exit(1)

try:
    from core.player import AudioPlayer
    print("✓ AudioPlayer 模組導入成功")
except Exception as e:
    print(f"✗ AudioPlayer 導入失敗: {e}")
    sys.exit(1)

try:
    from core.scheduler import Scheduler
    print("✓ Scheduler 模組導入成功")
except Exception as e:
    print(f"✗ Scheduler 導入失敗: {e}")
    sys.exit(1)

try:
    from core.dragdrop import validate_dropped_files
    print("✓ dragdrop 模組導入成功")
except Exception as e:
    print(f"✗ dragdrop 導入失敗: {e}")
    sys.exit(1)

try:
    from core.notifier import Notifier
    print("✓ Notifier 模組導入成功")
except Exception as e:
    print(f"✗ Notifier 導入失敗: {e}")
    sys.exit(1)

try:
    from core.tray import SystemTray
    print("✓ SystemTray 模組導入成功")
except Exception as e:
    print(f"✗ SystemTray 導入失敗: {e}")
    sys.exit(1)

# 測試基本功能
print("\n測試基本功能...")

# 測試 Storage
try:
    storage = Storage()
    test_data = {"schedules": []}
    storage.save_schedules(test_data)
    loaded = storage.load_schedules()
    print("✓ Storage 基本功能正常")
except Exception as e:
    print(f"✗ Storage 功能異常: {e}")

# 測試 Player
try:
    player = AudioPlayer()
    status = player.get_status()
    print(f"✓ Player 基本功能正常 (狀態: {status})")
    player.cleanup()
except Exception as e:
    print(f"✗ Player 功能異常: {e}")

# 測試 Scheduler
try:
    scheduler = Scheduler()
    next_time = scheduler.get_next_play_time()
    print(f"✓ Scheduler 基本功能正常")
    scheduler.stop()
except Exception as e:
    print(f"✗ Scheduler 功能異常: {e}")

# 測試 dragdrop
try:
    valid, invalid = validate_dropped_files(["test.mp3"])
    print("✓ dragdrop 驗證功能正常")
except Exception as e:
    print(f"✗ dragdrop 功能異常: {e}")

print("\n所有核心模組測試完成！")

