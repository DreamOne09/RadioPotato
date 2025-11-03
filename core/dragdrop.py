"""
檔案拖放處理模組
"""

import os

# Windows支援的檔案格式
SUPPORTED_AUDIO_FORMATS = {
    '.mp3', '.wav', '.wma', '.ogg', '.flac', '.m4a', '.aac'
}

def is_audio_file(file_path):
    """檢查檔案是否為支援的音訊格式"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_AUDIO_FORMATS

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
            valid_files.append(abs_path)
    
    return valid_files, invalid_files
