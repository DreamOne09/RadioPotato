"""
文件拖放处理模块
"""

import os

# Windows支持的文件格式
SUPPORTED_AUDIO_FORMATS = {
    '.mp3', '.wav', '.wma', '.ogg', '.flac', '.m4a', '.aac'
}

def is_audio_file(file_path):
    """检查文件是否为支持的音频格式"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_AUDIO_FORMATS

def validate_dropped_files(file_paths):
    """
    验证拖放的文件
    :param file_paths: 文件路径列表
    :return: (valid_files, invalid_files)
    """
    valid_files = []
    invalid_files = []
    
    for file_path in file_paths:
        # 转换为绝对路径
        abs_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_path):
            invalid_files.append((abs_path, "文件不存在"))
        elif not os.path.isfile(abs_path):
            invalid_files.append((abs_path, "不是文件"))
        elif not is_audio_file(abs_path):
            invalid_files.append((abs_path, "不支持的音频格式"))
        else:
            valid_files.append(abs_path)
    
    return valid_files, invalid_files

