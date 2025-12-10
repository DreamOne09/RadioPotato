"""
音訊工具函數
用於獲取音訊檔案資訊（時長等）
"""

import os

try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE
    from mutagen.ogg import OggVorbis
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    print("警告: mutagen未安裝，無法獲取音訊檔案時長")

def get_audio_duration(file_path):
    """
    獲取音訊檔案時長（秒）
    :param file_path: 檔案路徑
    :return: 時長（秒），如果無法獲取則返回None
    """
    if not HAS_MUTAGEN:
        return None
    
    if not os.path.exists(file_path):
        return None
    
    try:
        audio_file = MutagenFile(file_path)
        if audio_file is None:
            return None
        
        duration = audio_file.info.length
        return duration
    except Exception as e:
        print(f"獲取音訊時長失敗: {file_path}, {e}")
        return None

def format_duration(seconds):
    """
    格式化時長為 mm:ss 或 hh:mm:ss
    :param seconds: 秒數
    :return: 格式化字串
    """
    if seconds is None:
        return "未知"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def get_total_duration(file_paths):
    """
    獲取多個音訊檔案的總時長
    :param file_paths: 檔案路徑列表
    :return: 總時長（秒）
    """
    total = 0.0
    for file_path in file_paths:
        duration = get_audio_duration(file_path)
        if duration:
            total += duration
    return total if total > 0 else None





