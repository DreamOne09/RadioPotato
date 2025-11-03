"""
音訊播放引擎
支援播放佇列系統
"""

import pygame
import threading
import queue
import os
import time

class AudioPlayer:
    """音訊播放器類別，支援播放佇列"""
    
    def __init__(self, on_playback_start=None, on_playback_end=None):
        """
        初始化播放器
        :param on_playback_start: 播放開始時的回調函數(file_path)
        :param on_playback_end: 播放結束時的回調函數()
        """
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except pygame.error:
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
        將檔案加入播放佇列
        :param file_paths: 檔案路徑列表
        """
        for file_path in file_paths:
            if os.path.exists(file_path):
                self.play_queue.put(file_path)
                print(f"已加入佇列: {file_path}")
            else:
                print(f"檔案不存在，跳過: {file_path}")
        
        # 如果目前沒有在播放，啟動播放執行緒
        if not self.is_playing and self.play_thread is None:
            self._start_playback_thread()
    
    def _start_playback_thread(self):
        """啟動播放執行緒"""
        if self.play_thread is None or not self.play_thread.is_alive():
            self.stop_flag = False  # 重置停止標誌
            self.play_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.play_thread.start()
    
    def _playback_worker(self):
        """播放工作執行緒"""
        while not self.stop_flag:
            try:
                # 從佇列獲取檔案（阻塞，最多等待1秒）
                file_path = self.play_queue.get(timeout=1)
                if not self.stop_flag:
                    self._play_file(file_path)
                self.play_queue.task_done()
            except queue.Empty:
                # 佇列為空，等待新任務
                continue
            except Exception as e:
                print(f"播放工作執行緒錯誤: {e}")
                continue
    
    def _play_file(self, file_path):
        """播放單個檔案"""
        try:
            self.is_playing = True
            self.current_file = file_path
            
            # 觸發播放開始回調
            if self.on_playback_start:
                self.on_playback_start(file_path)
            
            # 載入並播放音訊
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # 等待播放完成或被停止
            while pygame.mixer.music.get_busy() and not self.stop_flag:
                time.sleep(0.1)
            
            # 如果被停止，停止播放
            if self.stop_flag:
                pygame.mixer.music.stop()
            
            # 觸發播放結束回調
            if self.on_playback_end:
                self.on_playback_end()
                
        except pygame.error as e:
            print(f"播放錯誤: {e}")
            if self.on_playback_end:
                self.on_playback_end()
        except Exception as e:
            print(f"播放檔案時發生錯誤: {file_path}, {e}")
            if self.on_playback_end:
                self.on_playback_end()
        finally:
            self.is_playing = False
            self.current_file = None
    
    def play_files(self, file_paths):
        """立即播放檔案列表（加入佇列）"""
        self.enqueue_files(file_paths)
    
    def stop(self):
        """停止播放並清空佇列"""
        self.stop_flag = True
        try:
            pygame.mixer.music.stop()
        except:
            pass
        # 清空佇列
        while not self.play_queue.empty():
            try:
                self.play_queue.get_nowait()
                self.play_queue.task_done()
            except queue.Empty:
                break
        self.is_playing = False
        self.current_file = None
        self.stop_flag = False  # 重置標誌，以便後續可以繼續播放
    
    def get_queue_size(self):
        """獲取佇列中的檔案數量"""
        return self.play_queue.qsize()
    
    def get_status(self):
        """獲取播放狀態"""
        if self.is_playing:
            return f"播放中: {os.path.basename(self.current_file)}"
        elif self.get_queue_size() > 0:
            return f"佇列中: {self.get_queue_size()} 個檔案"
        else:
            return "空閒"
    
    def cleanup(self):
        """清理資源"""
        self.stop()
        pygame.mixer.quit()
