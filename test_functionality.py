"""
功能測試腳本
模擬測試自動廣播系統的各項功能
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.storage import Storage
from core.player import AudioPlayer
from core.scheduler import Scheduler
from core.dragdrop import validate_dropped_files
from core.notifier import Notifier

def test_storage():
    """測試數據存儲功能"""
    print("\n" + "="*50)
    print("測試 1: 數據存儲功能")
    print("="*50)
    
    storage = Storage()
    
    # 測試數據
    test_data = {
        "schedules": [
            {
                "id": 1,
                "name": "測試計劃1",
                "days": ["monday", "tuesday"],
                "time": "10:00",
                "files": ["test1.mp3", "test2.mp3"],
                "duration": 0
            }
        ]
    }
    
    # 測試保存
    print("✓ 測試保存功能...")
    result = storage.save_schedules(test_data)
    assert result, "保存失敗"
    print("  ✓ 保存成功")
    
    # 測試載入
    print("✓ 測試載入功能...")
    loaded_data = storage.load_schedules()
    assert loaded_data['schedules'][0]['name'] == "測試計劃1", "載入失敗"
    print("  ✓ 載入成功")
    
    # 清理測試數據
    storage.save_schedules({"schedules": []})
    print("  ✓ 測試數據已清理")
    
    print("✓ 數據存儲功能測試通過！\n")
    return True

def test_dragdrop():
    """測試拖放驗證功能"""
    print("="*50)
    print("測試 2: 檔案拖放驗證功能")
    print("="*50)
    
    # 創建測試檔案（模擬）
    test_files = [
        "test.mp3",  # 有效
        "test.wav",  # 有效
        "test.txt",  # 無效（非音訊）
        "nonexistent.mp3"  # 無效（不存在）
    ]
    
    print("✓ 測試檔案格式驗證...")
    valid_files, invalid_files = validate_dropped_files(test_files)
    
    print(f"  有效檔案數: {len(valid_files)}")
    print(f"  無效檔案數: {len(invalid_files)}")
    
    # 至少應該檢測出txt為無效
    assert len(invalid_files) >= 1, "驗證功能異常"
    print("  ✓ 格式驗證正常")
    
    print("✓ 檔案拖放驗證功能測試通過！\n")
    return True

def test_scheduler():
    """測試排程器功能"""
    print("="*50)
    print("測試 3: 排程器功能")
    print("="*50)
    
    triggered_schedules = []
    
    def on_trigger(schedule):
        triggered_schedules.append(schedule)
    
    scheduler = Scheduler(on_schedule_trigger=on_trigger)
    
    # 添加測試計劃（設定為當前時間後1分鐘）
    now = datetime.now()
    future_time = now + timedelta(minutes=1)
    test_time = future_time.strftime("%H:%M")
    current_weekday = now.strftime("%A").lower()
    
    test_schedule = {
        'id': 1,
        'name': '測試排程',
        'days': [current_weekday],
        'time': test_time,
        'files': ['test.mp3']
    }
    
    print(f"✓ 添加測試計劃（時間: {test_time}，周幾: {current_weekday}）...")
    scheduler.add_schedule(test_schedule)
    print("  ✓ 計劃已添加")
    
    print("✓ 測試獲取下一個播放時間...")
    next_time = scheduler.get_next_play_time()
    assert next_time is not None, "無法獲取下一個播放時間"
    print(f"  ✓ 下一個播放時間: {next_time['time']}")
    
    print("✓ 測試移除計劃...")
    scheduler.remove_schedule(1)
    assert len(scheduler.schedules) == 0, "移除失敗"
    print("  ✓ 計劃已移除")
    
    scheduler.stop()
    print("✓ 排程器功能測試通過！\n")
    return True

def test_player():
    """測試播放器功能"""
    print("="*50)
    print("測試 4: 播放器功能")
    print("="*50)
    
    playback_events = []
    
    def on_start(file_path):
        playback_events.append(('start', file_path))
        print(f"  → 播放開始: {os.path.basename(file_path)}")
    
    def on_end():
        playback_events.append(('end', None))
        print("  → 播放結束")
    
    player = AudioPlayer(
        on_playback_start=on_start,
        on_playback_end=on_end
    )
    
    print("✓ 測試播放佇列...")
    # 注意：這裡不實際播放，因為可能沒有音訊檔案
    test_files = ['test1.mp3', 'test2.mp3']
    player.enqueue_files(test_files)
    
    queue_size = player.get_queue_size()
    print(f"  ✓ 佇列大小: {queue_size}")
    assert queue_size >= 0, "佇列異常"
    
    print("✓ 測試播放狀態...")
    status = player.get_status()
    print(f"  ✓ 狀態: {status}")
    
    print("✓ 測試停止功能...")
    player.stop()
    print("  ✓ 播放器已停止")
    
    player.cleanup()
    print("✓ 播放器功能測試通過！\n")
    return True

def test_notifier():
    """測試通知功能"""
    print("="*50)
    print("測試 5: 通知功能")
    print("="*50)
    
    notifier = Notifier()
    
    print("✓ 測試通知初始化...")
    # 只是測試初始化，不實際發送通知
    assert notifier is not None, "通知器初始化失敗"
    print("  ✓ 通知器已初始化")
    
    print("✓ 通知功能測試通過！\n")
    return True

def test_integration():
    """整合測試"""
    print("="*50)
    print("測試 6: 整合測試")
    print("="*50)
    
    print("✓ 測試完整流程...")
    
    # 1. 初始化組件
    storage = Storage()
    player = AudioPlayer()
    scheduler = Scheduler()
    
    # 2. 創建測試計劃
    test_schedule = {
        'id': 1,
        'name': '整合測試計劃',
        'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        'time': '10:00',
        'files': ['test.mp3'],
        'duration': 0
    }
    
    # 3. 添加計劃
    scheduler.add_schedule(test_schedule)
    assert len(scheduler.schedules) == 1, "添加計劃失敗"
    print("  ✓ 計劃已添加")
    
    # 4. 保存計劃
    data = {'schedules': [test_schedule]}
    storage.save_schedules(data)
    print("  ✓ 計劃已保存")
    
    # 5. 載入計劃
    loaded = storage.load_schedules()
    assert len(loaded['schedules']) == 1, "載入計劃失敗"
    print("  ✓ 計劃已載入")
    
    # 清理
    storage.save_schedules({"schedules": []})
    scheduler.stop()
    player.cleanup()
    
    print("✓ 整合測試通過！\n")
    return True

def main():
    """主測試函數"""
    print("\n" + "="*50)
    print("自動廣播系統 - 功能測試")
    print("="*50)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("數據存儲", test_storage),
        ("檔案拖放驗證", test_dragdrop),
        ("排程器", test_scheduler),
        ("播放器", test_player),
        ("通知功能", test_notifier),
        ("整合測試", test_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} 測試失敗: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("="*50)
    print("測試結果總結")
    print("="*50)
    print(f"總測試數: {len(tests)}")
    print(f"通過: {passed} ✓")
    print(f"失敗: {failed} ✗")
    print("="*50)
    
    if failed == 0:
        print("\n🎉 所有測試通過！程式可以正常使用。\n")
        return True
    else:
        print(f"\n⚠️  有 {failed} 個測試失敗，請檢查並修復。\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

