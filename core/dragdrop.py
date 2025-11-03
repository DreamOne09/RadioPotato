"""
檔案拖放處理模組
"""

import os

# Windows支援的檔案格式
SUPPORTED_AUDIO_FORMATS = {
    '.mp3', '.wav', '.wma', '.ogg', '.flac', '.m4a', '.aac'
}

# 檔案大小限制（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

def is_audio_file(file_path):
    """檢查檔案是否為支援的音訊格式"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_AUDIO_FORMATS

def get_file_size(file_path):
    """獲取檔案大小（位元組）"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def format_file_size(size_bytes):
    """格式化檔案大小顯示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def validate_dropped_files(file_paths):
    """
    驗證拖放的檔案
    :param file_paths: 檔案路徑列表
    :return: (valid_files, invalid_files)
    """
    valid_files = []
    invalid_files = []
    
    for file_path in file_paths:
        # 轉換為絕對路徑
        abs_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_path):
            invalid_files.append((abs_path, "檔案不存在"))
        elif not os.path.isfile(abs_path):
            invalid_files.append((abs_path, "不是檔案"))
        elif not is_audio_file(abs_path):
            invalid_files.append((abs_path, "不支援的音訊格式"))
        else:
            # 檢查檔案大小
            file_size = get_file_size(abs_path)
            if file_size > MAX_FILE_SIZE:
                size_str = format_file_size(file_size)
                max_str = format_file_size(MAX_FILE_SIZE)
                invalid_files.append((abs_path, f"檔案過大 ({size_str})，建議小於 {max_str}"))
            else:
                valid_files.append(abs_path)
    
    return valid_files, invalid_files
