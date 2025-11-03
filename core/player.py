"""
音频播放引擎
支持播放队列系统
"""

import pygame
import threading
import queue
import os
import time

class AudioPlayer:
    """音频播放器类，支持播放队列"""
    
    def __init__(self, on_playback_start=None, on_playback_end=None):
        """
        初始化播放器
        :param on_playback_start: 播放开始时的回调函数(file_path)
        :param on_playback_end: 播放结束时的回调函数()
        """
        pygame.mixer.init()
        self.play_queue = queue.Queue()
        self.is_playing = False
        self.current_file = None
        self.on_playback_start = on_playback_start
        self.on_playback_end = on_playback_end
        self.play_thread = None
        self.stop_flag = False
        
    def enqueue_files(self, file_paths):
        """
        将文件加入播放队列
        :param file_paths: 文件路径列表
        """
        for file_path in file_paths:
            if os.path.exists(file_path):
                self.play_queue.put(file_path)
                print(f"已加入队列: {file_path}")
            else:
                print(f"文件不存在，跳过: {file_path}")
        
        # 如果当前没有在播放，启动播放线程
        if not self.is_playing and self.play_thread is None:
            self._start_playback_thread()
    
    def _start_playback_thread(self):
        """启动播放线程"""
        if self.play_thread is None or not self.play_thread.is_alive():
            self.stop_flag = False  # 重置停止标志
            self.play_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.play_thread.start()
    
    def _playback_worker(self):
        """播放工作线程"""
        while not self.stop_flag:
            try:
                # 从队列获取文件（阻塞，最多等待1秒）
                file_path = self.play_queue.get(timeout=1)
                if not self.stop_flag:
                    self._play_file(file_path)
                self.play_queue.task_done()
            except queue.Empty:
                # 队列为空，等待新任务
                continue
            except Exception as e:
                print(f"播放工作线程错误: {e}")
                continue
    
    def _play_file(self, file_path):
        """播放单个文件"""
        try:
            self.is_playing = True
            self.current_file = file_path
            
            # 触发播放开始回调
            if self.on_playback_start:
                self.on_playback_start(file_path)
            
            # 加载并播放音频
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # 等待播放完成或被停止
            while pygame.mixer.music.get_busy() and not self.stop_flag:
                time.sleep(0.1)
            
            # 如果被停止，停止播放
            if self.stop_flag:
                pygame.mixer.music.stop()
            
            # 触发播放结束回调
            if self.on_playback_end:
                self.on_playback_end()
                
        except pygame.error as e:
            print(f"播放错误: {e}")
            if self.on_playback_end:
                self.on_playback_end()
        except Exception as e:
            print(f"播放文件时发生错误: {file_path}, {e}")
            if self.on_playback_end:
                self.on_playback_end()
        finally:
            self.is_playing = False
            self.current_file = None
    
    def play_files(self, file_paths):
        """立即播放文件列表（加入队列）"""
        self.enqueue_files(file_paths)
    
    def stop(self):
        """停止播放并清空队列"""
        self.stop_flag = True
        try:
            pygame.mixer.music.stop()
        except:
            pass
        # 清空队列
        while not self.play_queue.empty():
            try:
                self.play_queue.get_nowait()
                self.play_queue.task_done()
            except queue.Empty:
                break
        self.is_playing = False
        self.current_file = None
        self.stop_flag = False  # 重置标志，以便后续可以继续播放
    
    def get_queue_size(self):
        """获取队列中的文件数量"""
        return self.play_queue.qsize()
    
    def get_status(self):
        """获取播放状态"""
        if self.is_playing:
            return f"播放中: {os.path.basename(self.current_file)}"
        elif self.get_queue_size() > 0:
            return f"队列中: {self.get_queue_size()} 个文件"
        else:
            return "空闲"
    
    def cleanup(self):
        """清理资源"""
        self.stop()
        pygame.mixer.quit()

