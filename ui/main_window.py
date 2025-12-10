"""
主視窗介面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import threading
from collections import deque
from datetime import datetime, timedelta, time
from PIL import Image, ImageTk

# 嘗試匯入tkinterdnd2，如果失敗則使用普通Tk
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    TkinterDnD = tk.Tk
    DND_FILES = None
    HAS_DND = False
    print("警告: tkinterdnd2未安裝，拖放功能不可用，請使用「選擇音訊檔案」按鈕")

# 新增父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.storage import Storage
from core.player import AudioPlayer
from core.scheduler import Scheduler
from core.dragdrop import validate_dropped_files
from core.notifier import Notifier
from core.audio_utils import get_total_duration, format_duration
from core.tray import SystemTray

class ScheduleDialog:
    """排程設定彈窗（整合檔案選擇和排程設定）"""
    
    def __init__(self, parent, font_family, colors, schedule=None):
        """初始化彈窗
        Args:
            parent: 父視窗
            font_family: 字體
            colors: 顏色配置
            schedule: 如果提供，則為編輯模式，否則為新增模式
        """
        self.result = None  # 儲存結果：None表示取消，否則為排程字典
        self.selected_files = schedule['files'].copy() if schedule and schedule.get('files') else []
        
        # 創建彈窗
        # 創建彈窗
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("新增播放排程" if not schedule else "編輯播放排程")
        
        # 智慧型調整對話框大小
        screen_h = self.dialog.winfo_screenheight()
        dlg_h = 650
        if screen_h < 768:
            dlg_h = 550
        
        self.dialog.geometry(f"600x{dlg_h}")
        self.dialog.transient(parent)
        self.dialog.grab_set()  # 模態對話框
        self.dialog.resizable(True, True)  # 允許調整大小
        self.dialog.minsize(500, 500)  # 設置最小尺寸
        
        self.font_family = font_family
        self.colors = colors
        
        # 載入排程資料（編輯模式）
        if schedule:
            self.name = schedule['name']
            self.days = schedule['days'].copy()
            hour, minute = schedule['time'].split(':')
            self.hour = int(hour)
            self.minute = int(minute)
        else:
            self.name = "上課提醒"
            self.days = []
            self.hour = 15
            self.minute = 40
        
        self._setup_ui()
    
    def _setup_ui(self):
        """設定UI"""
        # 主內容容器（上半部可滾動、下半部固定按鈕）
        body_container = tk.Frame(self.dialog, bg=self.colors['bg_card'])
        body_container.pack(fill='both', expand=True, padx=10, pady=10)
        body_container.grid_rowconfigure(0, weight=1)
        body_container.grid_columnconfigure(0, weight=1)

        scroll_container = tk.Frame(body_container, bg=self.colors['bg_card'])
        scroll_container.grid(row=0, column=0, sticky='nsew')
        
        canvas = tk.Canvas(scroll_container, bg=self.colors['bg_card'], highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_card'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 確保canvas窗口寬度跟隨canvas
        def configure_canvas_window(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        canvas.bind('<Configure>', configure_canvas_window)
        
        canvas.pack(side='left', fill='both', expand=True, padx=(0, 6))
        scrollbar.pack(side='right', fill='y')
        
        # 綁定滑鼠滾輪
        def _on_mousewheel(event):
            delta = event.delta
            if delta == 0 and event.num in (4, 5):  # Linux support
                delta = 120 if event.num == 4 else -120
            canvas.yview_scroll(int(-1 * (delta / 120)), "units")

        def _bind_to_mousewheel(_event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_from_mousewheel(_event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        scrollable_frame.bind("<Enter>", _bind_to_mousewheel)
        scrollable_frame.bind("<Leave>", _unbind_from_mousewheel)
        
        # 主容器（在可滾動框架內）
        main_frame = scrollable_frame
        main_frame.columnconfigure(0, weight=1)
        
        # 排程名稱
        name_frame = tk.Frame(main_frame, bg=self.colors['bg_card'])
        name_frame.pack(fill='x', pady=10)
        
        tk.Label(
            name_frame,
            text="排程名稱：",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        ).pack(side='left', padx=5)
        
        self.name_var = tk.StringVar(value=self.name)
        name_entry = tk.Entry(
            name_frame,
            textvariable=self.name_var,
            font=(self.font_family, 12),
            width=30,
            relief='solid',
            borderwidth=1
        )
        name_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        # 日期選擇
        days_frame = tk.Frame(main_frame, bg=self.colors['bg_accent'], relief='flat')
        days_frame.pack(fill='x', pady=10, padx=5)
        
        tk.Label(
            days_frame,
            text="播放日期：",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(pady=(8, 5))
        
        self.day_vars = {}
        weekdays = [
            ('週一', 'monday'),
            ('週二', 'tuesday'),
            ('週三', 'wednesday'),
            ('週四', 'thursday'),
            ('週五', 'friday'),
            ('週六', 'saturday'),
            ('週日', 'sunday')
        ]
        
        days_inner = tk.Frame(days_frame, bg=self.colors['bg_accent'])
        days_inner.pack(pady=(0, 8))
        
        for i, (label, value) in enumerate(weekdays):
            var = tk.BooleanVar(value=value in self.days)
            self.day_vars[value] = var
            cb = tk.Checkbutton(
                days_inner,
                text=label,
                variable=var,
                font=(self.font_family, 11, 'bold'),
                bg=self.colors['bg_accent'],
                fg=self.colors['text_primary'],
                selectcolor=self.colors['bg_card'],
                activebackground=self.colors['bg_accent'],
                activeforeground=self.colors['text_primary']
            )
            cb.grid(row=0, column=i, padx=8, pady=3)
        
        # 時間選擇
        time_frame = tk.Frame(main_frame, bg=self.colors['bg_accent'], relief='flat')
        time_frame.pack(fill='x', pady=10, padx=5)
        
        tk.Label(
            time_frame,
            text="播放時間：",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(pady=(8, 5))
        
        time_inner = tk.Frame(time_frame, bg=self.colors['bg_accent'])
        time_inner.pack(pady=(0, 8))
        
        tk.Label(
            time_inner,
            text="時",
            font=(self.font_family, 11),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(side='left', padx=5)
        
        self.hour_var = tk.StringVar(value=str(self.hour))
        hour_spin = tk.Spinbox(
            time_inner,
            from_=0,
            to=23,
            width=5,
            textvariable=self.hour_var,
            format="%02.0f",
            font=(self.font_family, 11, 'bold'),
            relief='solid',
            borderwidth=1
        )
        hour_spin.pack(side='left', padx=8)
        
        tk.Label(
            time_inner,
            text="分",
            font=(self.font_family, 11),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(side='left', padx=5)
        
        self.minute_var = tk.StringVar(value=str(self.minute))
        minute_spin = tk.Spinbox(
            time_inner,
            from_=0,
            to=59,
            width=5,
            textvariable=self.minute_var,
            format="%02.0f",
            font=(self.font_family, 11, 'bold'),
            relief='solid',
            borderwidth=1
        )
        minute_spin.pack(side='left', padx=8)
        
        # 音訊檔案選擇區域
        files_frame = tk.Frame(main_frame, bg=self.colors['bg_card'])
        files_frame.pack(fill='both', expand=True, pady=10)
        files_frame.grid_columnconfigure(0, weight=1)
        files_frame.grid_rowconfigure(1, weight=1)

        files_header = tk.Frame(files_frame, bg=self.colors['bg_card'])
        files_header.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        files_header.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            files_header,
            text="音訊檔案：",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        ).grid(row=0, column=0, sticky='w', padx=5)

        select_btn = tk.Button(
            files_header,
            text="📂 選擇檔案",
            command=self._select_files,
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            relief='flat',
            borderwidth=0,
            padx=15,
            pady=6,
            cursor='hand2',
            activebackground=self.colors['primary_hover']
        )
        select_btn.grid(row=0, column=1, sticky='e', padx=5)
        
        # 檔案列表
        listbox_frame = tk.Frame(files_frame, bg=self.colors['bg_card'], height=240)
        listbox_frame.grid(row=1, column=0, sticky='nsew', pady=(0, 6))
        listbox_frame.pack_propagate(False)
        
        listbox_scrollbar = tk.Scrollbar(listbox_frame)
        listbox_scrollbar.pack(side='right', fill='y')
        
        self.file_listbox = tk.Listbox(
            listbox_frame,
            height=10,
            font=(self.font_family, 11),
            bg='white',
            fg='black',
            yscrollcommand=listbox_scrollbar.set,
            relief='solid',
            borderwidth=1,
            activestyle='none'
        )
        self.file_listbox.pack(side='left', fill='both', expand=True)
        listbox_scrollbar.config(command=self.file_listbox.yview)

        # 總時長與預估完播顯示
        info_frame = tk.Frame(files_frame, bg=self.colors['bg_card'])
        info_frame.grid(row=2, column=0, sticky='ew', pady=(2, 4))
        info_frame.grid_columnconfigure(0, weight=1)

        self.duration_label = tk.Label(
            info_frame,
            text="總時長：計算中...",
            font=(self.font_family, 11),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary']
        )
        self.duration_label.grid(row=0, column=0, sticky='w', pady=(0, 2))

        self.estimated_end_label = tk.Label(
            info_frame,
            text="預估完播：--:--",
            font=(self.font_family, 11),
            bg=self.colors['bg_card'],
            fg=self.colors['text_secondary']
        )
        self.estimated_end_label.grid(row=1, column=0, sticky='w')

        self.hour_var.trace_add("write", self._on_time_changed)
        self.minute_var.trace_add("write", self._on_time_changed)
        self._update_duration()
        self._update_file_listbox()
        
        # 檔案操作按鈕
        file_btn_frame = tk.Frame(files_frame, bg=self.colors['bg_card'])
        file_btn_frame.grid(row=3, column=0, sticky='ew', pady=(6, 0))
        file_btn_frame.grid_columnconfigure(0, weight=1)
        file_btn_frame.grid_columnconfigure(1, weight=1)
        
        remove_btn = tk.Button(
            file_btn_frame,
            text="🗑️ 移除選取",
            command=self._remove_selected_file,
            font=(self.font_family, 10, 'bold'),
            bg=self.colors['danger'],
            fg='white',
            relief='flat',
            borderwidth=0,
            padx=10,
            pady=6,
            cursor='hand2',
            activebackground='#C62828'
        )
        remove_btn.grid(row=0, column=0, padx=(0, 6), sticky='ew')
        
        clear_btn = tk.Button(
            file_btn_frame,
            text="🧹 清空列表",
            command=self._clear_files,
            font=(self.font_family, 10, 'bold'),
            bg=self.colors['text_secondary'],
            fg='white',
            relief='flat',
            borderwidth=0,
            padx=10,
            pady=6,
            cursor='hand2',
            activebackground='#5D6D7E'
        )
        clear_btn.grid(row=0, column=1, sticky='ew')
        
        # 確定和取消按鈕（固定在對話框底部，不在滾動區域內，始終可見）
        btn_frame = tk.Frame(body_container, bg=self.colors['bg_card'], height=72)
        btn_frame.grid(row=1, column=0, sticky='ew', pady=(12, 0))
        btn_frame.grid_columnconfigure(0, weight=1)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="取消",
            command=self._cancel,
            font=(self.font_family, 12, 'bold'),  # 增大字體
            bg='#6C757D',  # 使用明顯的灰色
            fg='white',
            relief='flat',
            borderwidth=0,
            padx=25,
            pady=12,  # 增大按鈕
            cursor='hand2',
            activebackground='#5A6268'
        )
        cancel_btn.pack(side='right', padx=(5, 0))
        
        ok_btn = tk.Button(
            btn_frame,
            text="送出",  # 改為"送出"更符合台灣用語
            command=self._confirm,
            font=(self.font_family, 12, 'bold'),  # 增大字體
            bg='#28A745',  # 使用明顯的綠色
            fg='white',
            relief='flat',
            borderwidth=0,
            padx=25,
            pady=12,  # 增大按鈕
            cursor='hand2',
            activebackground='#218838'
        )
        ok_btn.pack(side='right')
    
    def _select_files(self):
        """選擇檔案"""
        files = filedialog.askopenfilenames(
            title="選擇音訊檔案",
            filetypes=[
                ("音訊檔案", "*.mp3 *.wav *.wma *.ogg *.flac *.m4a *.aac"),
                ("所有檔案", "*.*")
            ]
        )
        
        if files:
            valid_files, invalid_files = validate_dropped_files(files)
            if invalid_files:
                messagebox.showwarning("警告", f"以下檔案無效：\n" + "\n".join(invalid_files[:5]))
            if valid_files:
                self.selected_files.extend(valid_files)
                # 限制最多50個檔案
                if len(self.selected_files) > 50:
                    self.selected_files = self.selected_files[-50:]
                    messagebox.showwarning("提示", "檔案列表已限制為最多50個檔案")
                self._update_file_listbox()
                # 更新總時長
                self._update_duration()
    
    def _update_file_listbox(self):
        """更新檔案列表顯示"""
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
        # 更新總時長
        self._update_duration()
    
    def _update_duration(self):
        """更新總時長顯示"""
        total_duration = None
        if self.selected_files:
            total_duration = get_total_duration(self.selected_files)
            if total_duration:
                formatted = format_duration(total_duration)
                self.duration_label.config(text=f"總時長：{formatted}")
            else:
                self.duration_label.config(text="總時長：無法計算")
        else:
            self.duration_label.config(text="總時長：0:00")
        self._update_estimated_end(total_duration)

    def _update_estimated_end(self, total_duration=None):
        if total_duration is None and self.selected_files:
            total_duration = get_total_duration(self.selected_files)
        if not total_duration:
            self.estimated_end_label.config(text="預估完播：--:--")
            return
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
        except (ValueError, tk.TclError):
            self.estimated_end_label.config(text="預估完播：--:--")
            return
        start_dt = datetime.combine(datetime.today().date(), time(hour, minute))
        end_dt = start_dt + timedelta(seconds=int(total_duration))
        duration_text = format_duration(total_duration)
        self.estimated_end_label.config(
            text=f"預估完播：{end_dt.strftime('%H:%M')}（長度 {duration_text}）"
        )

    def _on_time_changed(self, *_args):
        self._update_estimated_end()
    
    def _remove_selected_file(self):
        """移除選取的檔案"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.selected_files):
                del self.selected_files[index]
                self._update_file_listbox()
        else:
            messagebox.showinfo("提示", "請先選擇要移除的檔案")
    
    def _clear_files(self):
        """清空檔案列表"""
        self.selected_files = []
        self._update_file_listbox()
    
    def _confirm(self):
        """確認並關閉"""
        # 驗證
        if not self.selected_files:
            messagebox.showwarning("提示", "請至少選擇一個音訊檔案")
            return
        
        selected_days = [day for day, var in self.day_vars.items() if var.get()]
        if not selected_days:
            messagebox.showwarning("提示", "請至少選擇一天")
            return
        
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            time_str = f"{hour:02d}:{minute:02d}"
        except ValueError:
            messagebox.showerror("錯誤", "時間格式不正確")
            return
        
        name = self.name_var.get().strip()
        if not name:
            name = "播放排程"
        
        # 儲存結果
        self.result = {
            'name': name,
            'days': selected_days,
            'time': time_str,
            'files': self.selected_files.copy()
        }
        
        self.dialog.destroy()
    
    def _cancel(self):
        """取消並關閉"""
        self.result = None
        self.dialog.destroy()

class MainWindow:
    """主視窗類別"""
    
    def __init__(self):
        """初始化主視窗"""
        self.root = TkinterDnD.Tk()
        self.root.title("自動廣播系統")
        # 調整預設大小以適應舊螢幕 (Windows 2008 常見 1024x768)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 預設寬高
        default_width = 1000
        default_height = 650
        
        # 如果螢幕較小，自動調整
        if screen_width < 1050:
            default_width = 800
        if screen_height < 700:
            default_height = 550
            
        # 計算居中位置
        x_position = (screen_width - default_width) // 2
        y_position = (screen_height - default_height) // 2
        if x_position < 0: x_position = 0
        if y_position < 0: y_position = 0
            
        self.root.geometry(f"{default_width}x{default_height}+{x_position}+{y_position}")
        self.root.minsize(800, 550)
        
        # 檢測並設定字體（支援舊電腦）
        self.font_family = self._detect_font()
        print(f"使用字體: {self.font_family}")
        
        # 現代化配色方案
        self.colors = {
            'bg_main': '#F5F7FA',  # 主背景色 - 柔和的灰藍色
            'bg_card': '#FFFFFF',  # 卡片背景色
            'bg_accent': '#E8F4F8',  # 強調背景色
            'primary': '#4A90E2',  # 主色 - 現代藍色
            'primary_hover': '#357ABD',  # 主色懸停
            'success': '#52C9A6',  # 成功色 - 柔和綠色
            'success_hover': '#3BA088',  # 成功色懸停
            'danger': '#E57373',  # 危險色
            'text_primary': '#2C3E50',  # 主要文字
            'text_secondary': '#7F8C8D',  # 次要文字
            'border': '#D5DBE1',  # 邊框色
        }
        
        self.root.configure(bg=self.colors['bg_main'])
        
        # 設定視窗圖標（使用Logo）
        self._set_window_icon()
        
        # 初始化核心組件（在字體檢測後）
        self._init_components()
    
    def _detect_font(self):
        """檢測可用的字體，優先使用微軟正黑體或思源黑體"""
        # 優先順序：微軟正黑體 > 思源黑體 > 微軟雅黑 > 其他中文字體 > 系統預設
        font_candidates = [
            'Microsoft JhengHei UI',  # 微軟正黑體 UI（Windows 8+，優先使用）
            'Microsoft JhengHei',  # 微軟正黑體（Windows 8+，優先使用）
            'Source Han Sans TC',  # 思源黑體 繁體中文（如果安裝）
            'Source Han Sans',  # 思源黑體（如果安裝）
            'Noto Sans CJK TC',  # Noto Sans 繁體中文（如果安裝）
            'Microsoft YaHei UI',  # 微軟雅黑 UI（回退）
            'Microsoft YaHei',  # 微軟雅黑（回退）
            'Segoe UI',  # Windows 10+ 現代字體（回退）
            'MingLiU',  # 舊系統回退
            'PMingLiU',
            'SimHei',
            'SimSun'
        ]
        
        # 測試字體是否可用
        test_label = tk.Label(self.root, text="測試")
        for font_name in font_candidates:
            try:
                test_label.config(font=(font_name, 10))
                # 如果字體存在，Tkinter不會報錯
                test_label.destroy()
                print(f"✓ 使用字體: {font_name}")
                return font_name
            except:
                continue
        
        # 如果都不可用，使用系統預設字體
        test_label.destroy()
        print("⚠ 使用系統預設字體")
        return 'TkDefaultFont'
    
    def _init_components(self):
        """初始化核心組件（在字體檢測後調用）"""
        # 初始化核心組件
        self.storage = Storage()
        self.player = AudioPlayer(
            on_playback_start=self._on_playback_start,
            on_playback_end=self._on_playback_end
        )
        self.scheduler = Scheduler(on_schedule_trigger=self._on_schedule_trigger)
        self.notifier = Notifier()
        self.tray = None
        
        # 資料
        self.schedules = []
        self.selected_files = []  # 目前選擇的檔案列表
        self.next_schedule_id = 1
        self.max_selected_files = 50  # 限制最多選擇50個檔案
        self.pending_schedules = deque()
        self.current_schedule = None
        
        # UI組件
        self.setup_ui()
        
        # 載入保存的資料
        self.load_schedules()
        
        # 啟動排程器（確認真的在運行）
        self.scheduler.start()
        if self.scheduler.running:
            print("✓ 排程器已成功啟動，會自動在指定時間播放")
        else:
            print("⚠ 排程器啟動失敗")
        
        # 啟動系統託盤
        self.setup_tray()
        
        # 啟動時間更新
        self.update_time_display()
        
        # 處理視窗關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_modern_button(self, parent, text, command, bg_color=None, fg_color='white', font_size=14):
        """創建現代化按鈕"""
        if bg_color is None:
            bg_color = self.colors['success']
        
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=fg_color,
            font=(self.font_family, font_size, 'bold'),
            relief='flat',
            borderwidth=0,
            padx=20,
            pady=12,
            cursor='hand2',
            activebackground=bg_color,
            activeforeground=fg_color
        )
        
        # 滑鼠懸停效果
        def on_enter(e):
            btn.config(bg=self.colors.get('success_hover', bg_color))
        def on_leave(e):
            btn.config(bg=bg_color)
        
        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        
        return btn
    
    def _set_window_icon(self):
        """設定視窗圖標（使用Logo）"""
        try:
            # 獲取logo文件路徑
            if getattr(sys, 'frozen', False):
                # 打包後的exe
                base_path = os.path.dirname(sys.executable)
            else:
                # 開發模式
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            logo_path = os.path.join(base_path, 'RadioOne Logo.png')
            if os.path.exists(logo_path):
                # 載入並設定圖標
                icon = Image.open(logo_path)
                # 轉換為PhotoImage
                photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(False, photo)
                # 保存引用以避免被垃圾回收
                self._icon_photo = photo
                print(f"✓ 視窗圖標載入成功: {logo_path}")
            else:
                print(f"⚠ Logo檔案不存在: {logo_path}")
                print(f"   請確保 RadioOne Logo.png 與程式在同一目錄")
        except Exception as e:
            print(f"⚠ 設定視窗圖標失敗: {e}")
    
    def _on_window_resize(self, event=None):
        """處理窗口大小變化，動態調整版權資訊換行寬度，並確保時間顯示完整"""
        if event and event.widget == self.root:
            # 獲取窗口寬度
            window_width = self.root.winfo_width()
            window_height = self.root.winfo_height()
            
            # 動態調整版權資訊換行寬度
            available_width = max(window_width - 40, 300)  # 至少300px
            if hasattr(self, 'copyright_top'):
                self.copyright_top.config(wraplength=available_width)
            
            # 防呆機制：如果窗口太窄或太矮，強制恢復最小尺寸
            if window_width < 800:
                self.root.after(100, lambda: self.root.geometry(f"800x{max(window_height, 550)}"))
                print(f"⚠ 窗口寬度過小 ({window_width}px)，已強制恢復至最小寬度 800px")
            if window_height < 550:
                self.root.after(100, lambda: self.root.geometry(f"{max(window_width, 800)}x550"))
                print(f"⚠ 窗口高度過小 ({window_height}px)，已強制恢復至最小高度 550px")
            
            # 更新狀態列提示
            self._update_status_hint()
    
    def _toggle_fullscreen(self, event=None):
        """切換全屏模式（F11快捷鍵）"""
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
        return "break"
    
    def _exit_fullscreen(self, event=None):
        """退出全屏模式（ESC快捷鍵）"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
        return "break"
    
    def _reset_window_size(self, event=None):
        """重置窗口大小為預設大小（Ctrl+0快捷鍵）"""
        self.root.geometry("1100x700")
        if event is None:  # 如果是按鈕點擊，不顯示訊息框
            messagebox.showinfo("提示", "已重置窗口大小為預設大小\n\n快捷鍵說明：\nF11 - 全屏/退出全屏\nCtrl+0 - 重置大小\nCtrl+= - 放大窗口\nCtrl+- - 縮小窗口\nESC - 退出全屏")
        return "break"
    
    def _increase_window_size(self, event=None):
        """放大窗口（Ctrl+= 或 Ctrl++ 快捷鍵）"""
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        new_width = min(current_width + 100, 1920)
        new_height = min(current_height + 100, 1080)
        self.root.geometry(f"{new_width}x{new_height}")
        return "break"
    
    def _decrease_window_size(self, event=None):
        """縮小窗口（Ctrl+- 快捷鍵）"""
        current_width = self.root.winfo_width()
        current_height = self.root.winfo_height()
        new_width = max(current_width - 100, 800)
        new_height = max(current_height - 100, 550)
        self.root.geometry(f"{new_width}x{new_height}")
        return "break"
    
    def _update_status_hint(self):
        """更新狀態列提示（顯示快捷鍵）"""
        if hasattr(self, 'status_hint_label'):
            # 獲取當前窗口尺寸
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # 如果窗口太小，顯示警告提示
            if width < 900 or height < 600:
                hint = f"⚠ 視窗過小 ({width}x{height}) | F11全屏 | Ctrl+0重置"
                self.status_hint_label.config(text=hint, fg='orange')
            else:
                hint = "F11全屏 | Ctrl+0重置 | Ctrl+=/-調整大小"
                self.status_hint_label.config(text=hint, fg=self.colors['text_secondary'])
    
    def _show_shortcuts_help(self):
        """顯示完整快捷鍵說明"""
        help_text = """【快捷鍵說明】

視窗操作：
• F11          - 全屏/退出全屏
• ESC          - 退出全屏
• Ctrl + 0      - 重置視窗大小為預設值
• Ctrl + =      - 放大視窗（每次+100px，注意：+鍵需要Shift，所以用=）
• Ctrl + -      - 縮小視窗（每次-100px）

自救機制：
• 如果元素被隱藏，按 F11 進入全屏模式
• 或按 Ctrl+0 重置視窗大小
• 或點擊底部「🔄 重置視窗」按鈕

視窗最小尺寸：800x550
預設尺寸：1100x700

提示：視窗太小時，底部會顯示警告提示"""
        messagebox.showinfo("快捷鍵說明", help_text)
    
    def _create_tooltip(self, widget, text):
        """創建工具提示（滑鼠懸停顯示）"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(
                tooltip,
                text=text,
                bg='#FFFFCC',
                fg='black',
                font=(self.font_family, 9),
                relief='solid',
                borderwidth=1,
                padx=5,
                pady=3
            )
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def setup_ui(self):
        """設定UI介面"""
        # 頂部區域 - 標題和時間顯示（移除Big Logo，優化空間）
        top_frame = tk.Frame(self.root, bg=self.colors['bg_main'], height=75)
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.pack_propagate(False)
        
        # 標題和時間（強化防呆機制，防止時間被截斷）
        title_row = tk.Frame(top_frame, bg=self.colors['bg_main'])
        title_row.pack(fill='x', pady=(5, 3))
        
        # 左側：標題（放大字體）
        title_label = tk.Label(
            title_row,
            text="自動廣播系統",
            font=(self.font_family, 22, 'bold'),  # 從18放大到22
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary']
        )
        title_label.pack(side='left', padx=10)
        
        # 右側：時間顯示（回到右上角，更明顯）
        time_container = tk.Frame(title_row, bg=self.colors['bg_main'])
        time_container.pack(side='right', padx=15)
        
        # 時間標籤（明顯顯示，右對齊）
        self.time_label = tk.Label(
            time_container,
            text="目前時間: --:--:--",
            font=(self.font_family, 13, 'bold'),  # 增大字體並加粗，更明顯
            bg=self.colors['bg_main'],
            fg=self.colors['primary'],  # 使用主色，更醒目
            anchor='e',
            padx=10,
            pady=3
        )
        self.time_label.pack()
        
        # 版權資訊（放大字體，新增換行，防止截斷，動態調整wraplength）
        self.copyright_top = tk.Label(
            top_frame,
            text="本程式由僑務委員會外交替代役 李孟一老師所開發，如有問題可用line聯繫：dreamone09",
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            font=(self.font_family, 12),  # 從10放大到12
            anchor='w',
            wraplength=680,  # 初始寬度，會根據窗口大小動態調整
            justify='left'
        )
        self.copyright_top.pack(fill='x', padx=10, pady=(2, 3))  # 減少底部padding
        
        # 綁定窗口大小變化事件，動態調整版權資訊換行寬度
        self.root.bind('<Configure>', self._on_window_resize)
        
        # 綁定鍵盤快捷鍵（Windows原生機制）
        self.root.bind('<F11>', self._toggle_fullscreen)  # F11 全屏/退出全屏
        self.root.bind('<Control-0>', self._reset_window_size)  # Ctrl+0 重置窗口大小
        self.root.bind('<Control-equal>', self._increase_window_size)  # Ctrl+= 放大窗口（注意：+鍵需要Shift，所以用=）
        self.root.bind('<Control-minus>', self._decrease_window_size)  # Ctrl+- 縮小窗口
        self.root.bind('<Escape>', self._exit_fullscreen)  # ESC 退出全屏
        
        # 中間區域 - 左右並排布局（可捲動）
        # 創建外層容器和捲動條
        scroll_container = tk.Frame(self.root, bg=self.colors['bg_main'])
        scroll_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 創建Canvas和Scrollbar
        canvas = tk.Canvas(scroll_container, bg=self.colors['bg_main'], highlightthickness=0)
        scrollbar_y = ttk.Scrollbar(scroll_container, orient='vertical', command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_main'])
        
        # 更新scrollregion的函數
        def update_scrollregion(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", update_scrollregion)
        
        # 創建canvas窗口並綁定更新事件
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set)
        
        # 確保canvas窗口大小跟隨canvas（重要：讓內容可見）
        def configure_canvas_window(event):
            canvas_width = max(event.width, 800)  # 確保最小寬度
            canvas.itemconfig(canvas_window, width=canvas_width)
            update_scrollregion()
        canvas.bind('<Configure>', configure_canvas_window)
        
        # 綁定滑鼠滾輪
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar_y.pack(side='right', fill='y')
        
        # 保存引用以便後續更新
        self.canvas = canvas
        self.scrollable_frame = scrollable_frame
        self.canvas_window = canvas_window
        
        # 播放控制區域（一行布局：左邊狀態+進度條，右邊停止按鈕）
        playback_control_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_main'])
        playback_control_frame.pack(fill='x', padx=5, pady=(5, 10))
        
        # 左側：播放狀態和進度條
        playback_left = tk.Frame(playback_control_frame, bg=self.colors['bg_main'])
        playback_left.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # 狀態標籤
        self.playback_status_label = tk.Label(
            playback_left,
            text="目前無播放",
            font=(self.font_family, 11),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            anchor='w'
        )
        self.playback_status_label.pack(fill='x', pady=(0, 3))
        
        # 進度條和時間（並排）
        progress_row = tk.Frame(playback_left, bg=self.colors['bg_main'])
        progress_row.pack(fill='x')
        
        self.progress_bar = ttk.Progressbar(
            progress_row,
            mode='determinate',
            length=300,
            maximum=100
        )
        self.progress_bar.pack(side='left', fill='x', expand=True, padx=(0, 8))
        
        self.progress_time_label = tk.Label(
            progress_row,
            text="--:-- / --:--",
            font=(self.font_family, 9),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            anchor='e',
            width=12
        )
        self.progress_time_label.pack(side='right')
        
        # 右側：停止按鈕
        self.stop_btn = tk.Button(
            playback_control_frame,
            text="⏹ 中斷播放",
            command=self.stop_playback,
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['danger'],
            fg='white',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=20,
            pady=8,
            cursor='hand2',
            activebackground='#C62828',
            activeforeground='white',
            state='disabled'  # 初始狀態為禁用
        )
        self.stop_btn.pack(side='right')
        
        # 主內容區域：播放排程設定（單欄布局）
        right_container = tk.Frame(scrollable_frame, bg=self.colors['bg_main'])
        
        right_card = tk.Frame(
            right_container,
            bg=self.colors['bg_card'],
            relief='flat',
            borderwidth=1,
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        right_card.pack(fill='both', expand=True, padx=5, pady=5)
        right_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 右側標題
        right_title = tk.Label(
            right_card,
            text="播放排程設定",
            font=(self.font_family, 14, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        right_title.pack(pady=(8, 5))  # 減少padding
        
        # 排程設定區域
        settings_frame = tk.Frame(right_card, bg=self.colors['bg_card'])
        settings_frame.pack(fill='x', padx=15, pady=5)
        
        # 日期和時間選擇（並排）
        datetime_row = tk.Frame(settings_frame, bg=self.colors['bg_card'])
        datetime_row.pack(fill='x', pady=5)
        
        # 左側：日期選擇
        days_frame = tk.Frame(datetime_row, bg=self.colors['bg_accent'], relief='flat')
        days_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        days_title = tk.Label(
            days_frame,
            text="日期",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        )
        days_title.pack(pady=(6, 4))
        
        self.day_vars = {}
        weekdays = [
            ('一', 'monday'),
            ('二', 'tuesday'),
            ('三', 'wednesday'),
            ('四', 'thursday'),
            ('五', 'friday'),
            ('六', 'saturday'),
            ('日', 'sunday')
        ]
        
        days_inner = tk.Frame(days_frame, bg=self.colors['bg_accent'])
        days_inner.pack(pady=(0, 6))
        
        for i, (label, value) in enumerate(weekdays):
            var = tk.BooleanVar()
            self.day_vars[value] = var
            cb = tk.Checkbutton(
                days_inner,
                text=label,
                variable=var,
                font=(self.font_family, 12, 'bold'),
                bg=self.colors['bg_accent'],
                fg=self.colors['text_primary'],
                selectcolor=self.colors['bg_card'],
                activebackground=self.colors['bg_accent'],
                activeforeground=self.colors['text_primary'],
                width=4,
                height=1
            )
            cb.grid(row=0, column=i, padx=5, pady=3, sticky='ew')
        
        for i in range(7):
            days_inner.grid_columnconfigure(i, weight=1, uniform='day')
        
        # 右側：時間選擇
        time_frame = tk.Frame(datetime_row, bg=self.colors['bg_accent'], relief='flat')
        time_frame.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        time_title = tk.Label(
            time_frame,
            text="時間",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        )
        time_title.pack(pady=(6, 4))
        
        time_inner = tk.Frame(time_frame, bg=self.colors['bg_accent'])
        time_inner.pack(pady=(0, 6))
        
        tk.Label(
            time_inner,
            text="時",
            font=(self.font_family, 12),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(side='left', padx=8)
        
        self.hour_var = tk.StringVar(value="15")
        hour_spin = tk.Spinbox(
            time_inner,
            from_=0,
            to=23,
            width=6,
            textvariable=self.hour_var,
            format="%02.0f",
            font=(self.font_family, 12, 'bold'),
            relief='solid',
            borderwidth=1,
            highlightthickness=1
        )
        hour_spin.pack(side='left', padx=8)
        
        tk.Label(
            time_inner,
            text="分",
            font=(self.font_family, 12),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(side='left', padx=8)
        
        self.minute_var = tk.StringVar(value="40")
        minute_spin = tk.Spinbox(
            time_inner,
            from_=0,
            to=59,
            width=6,
            textvariable=self.minute_var,
            format="%02.0f",
            font=(self.font_family, 12, 'bold'),
            relief='solid',
            borderwidth=1,
            highlightthickness=1
        )
        minute_spin.pack(side='left', padx=8)
        
        # 排程名稱和新增按鈕
        name_btn_row = tk.Frame(settings_frame, bg=self.colors['bg_card'])
        name_btn_row.pack(fill='x', pady=8)
        
        name_label = tk.Label(
            name_btn_row,
            text="名稱：",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        name_label.pack(side='left', padx=(0, 8))
        
        self.schedule_name_var = tk.StringVar(value="上課提醒")
        name_entry = tk.Entry(
            name_btn_row,
            textvariable=self.schedule_name_var,
            width=18,
            font=(self.font_family, 12),
            relief='solid',
            borderwidth=1,
            highlightthickness=1
        )
        name_entry.pack(side='left', padx=(0, 10), fill='x', expand=True)
        
        # 新增排程按鈕（放大）- 打開彈窗
        add_btn = tk.Button(
            name_btn_row,
            text="➕ 新增排程",
            command=self.add_schedule_with_dialog,
            font=(self.font_family, 13, 'bold'),
            bg=self.colors['success'],
            fg='white',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=25,
            pady=12,  # 增大按鈕高度
            cursor='hand2',
            activebackground=self.colors['success_hover'],
            activeforeground='white'
        )
        add_btn.pack(side='right')
        
        # 播放排程列表
        schedule_card = tk.Frame(
            right_card,
            bg=self.colors['bg_card']
        )
        schedule_card.pack(fill='both', expand=True, padx=15, pady=(5, 3))  # 減少padding
        
        schedule_title = tk.Label(
            schedule_card,
            text="播放排程列表",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        schedule_title.pack(pady=(0, 5))
        
        # 創建Treeview顯示播放排程
        tree_frame = tk.Frame(schedule_card, bg=self.colors['bg_card'])
        tree_frame.pack(fill='both', expand=True, pady=(0, 5))
        
        columns = ('名稱', '週幾', '時間', '預估完播', '音訊檔案', '檔案數')
        self.schedule_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=10
        )
        
        # 設定Treeview樣式（緊湊但可見）
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', 
                       font=(self.font_family, 11),  # 增大字體
                       rowheight=32,  # 增加行高
                       background='white',
                       foreground='black',
                       fieldbackground='white')
        style.configure('Treeview.Heading', 
                       font=(self.font_family, 11, 'bold'),  # 增大字體
                       background=self.colors['primary'],
                       foreground='white')
        style.map('Treeview', 
                  background=[('selected', self.colors['primary'])],
                  foreground=[('selected', 'white')])
        
        # 隱藏預設的#0列（避免重複顯示）
        self.schedule_tree.column('#0', width=0, stretch=False)
        
        for col in columns:
            self.schedule_tree.heading(col, text=col)
            if col == '名稱':
                self.schedule_tree.column(col, width=160, minwidth=120)
            elif col == '週幾':
                self.schedule_tree.column(col, width=160, minwidth=120)
            elif col == '時間':
                self.schedule_tree.column(col, width=90, minwidth=70, anchor='center')
            elif col == '預估完播':
                self.schedule_tree.column(col, width=140, minwidth=110, anchor='center')
            elif col == '音訊檔案':
                self.schedule_tree.column(col, width=320, minwidth=200)
            else:
                self.schedule_tree.column(col, width=90, minwidth=60, anchor='center')
        
        scrollbar_tree = ttk.Scrollbar(tree_frame, orient='vertical', command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=scrollbar_tree.set)
        
        self.schedule_tree.pack(side='left', fill='both', expand=True)
        scrollbar_tree.pack(side='right', fill='y')
        
        # 綁定雙擊編輯
        self.schedule_tree.bind('<Double-1>', self.edit_schedule)
        
        # 排程操作按鈕（使用grid防止截斷，減少padding）
        schedule_btn_frame = tk.Frame(schedule_card, bg=self.colors['bg_card'])
        schedule_btn_frame.pack(pady=3, fill='x')  # 從6減少到3
        
        # 按鈕容器，使用grid讓按鈕均勻分布，防止截斷
        btn_container = tk.Frame(schedule_btn_frame, bg=self.colors['bg_card'])
        btn_container.pack(fill='x', padx=3)
        
        test_btn = tk.Button(
            btn_container,
            text="🎵 測試播放",
            command=self.test_selected_schedule,
            font=(self.font_family, 12, 'bold'),  # 增大字體
            bg=self.colors['primary'],
            fg='white',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=12,  # 增大按鈕高度
            cursor='hand2',
            activebackground=self.colors['primary_hover'],
            activeforeground='white'
        )
        test_btn.grid(row=0, column=0, padx=3, sticky='ew')
        btn_container.grid_columnconfigure(0, weight=1)
        
        edit_btn = tk.Button(
            btn_container,
            text="✏️ 編輯",
            command=self.edit_selected_schedule,
            font=(self.font_family, 12, 'bold'),  # 增大字體
            bg=self.colors['text_secondary'],
            fg='white',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=12,  # 增大按鈕高度
            cursor='hand2',
            activebackground='#5D6D7E',
            activeforeground='white'
        )
        edit_btn.grid(row=0, column=1, padx=3, sticky='ew')
        btn_container.grid_columnconfigure(1, weight=1)
        
        delete_btn = tk.Button(
            btn_container,
            text="🗑️ 刪除",
            command=self.delete_selected_schedule,
            font=(self.font_family, 12, 'bold'),  # 增大字體
            bg=self.colors['danger'],
            fg='white',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=12,  # 增大按鈕高度
            cursor='hand2',
            activebackground='#C62828',
            activeforeground='white'
        )
        delete_btn.grid(row=0, column=2, padx=3, sticky='ew')
        btn_container.grid_columnconfigure(2, weight=1)
        
        # 底部狀態列（強化：添加快捷鍵提示和重置按鈕）
        status_frame = tk.Frame(
            self.root,
            bg=self.colors['bg_main'],
            height=70  # 增加高度以容納更多資訊
        )
        status_frame.pack(fill='x', side='bottom', padx=15, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        # 狀態列（第一行：狀態和快捷鍵提示）
        status_inner = tk.Frame(status_frame, bg=self.colors['bg_main'])
        status_inner.pack(fill='x', padx=15, pady=(5, 2))
        
        # Logo圖片（左側，小尺寸）
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            logo_path = os.path.join(base_path, 'RadioOne Logo.png')
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                # 放大Logo，適合狀態列的大小（高度約30px）
                logo_img = logo_img.resize((30, 30), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_img)
                self._status_logo_photo = logo_photo  # 保存引用
                
                logo_label = tk.Label(
                    status_inner,
                    image=logo_photo,
                    bg=self.colors['bg_main']
                )
                logo_label.pack(side='left', padx=(0, 8))
            else:
                print(f"⚠ Logo檔案不存在: {logo_path}")
        except Exception as e:
            print(f"⚠ 載入狀態列Logo失敗: {e}")
        
        self.status_label = tk.Label(
            status_inner,
            text="就緒",
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            font=(self.font_family, 12),
            anchor='w'
        )
        self.status_label.pack(side='left', fill='x', expand=True)
        
        # 快捷鍵提示標籤（動態顯示）
        self.status_hint_label = tk.Label(
            status_inner,
            text="F11全屏 | Ctrl+0重置 | Ctrl+±調整大小",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=(self.font_family, 9),
            cursor='hand2'
        )
        self.status_hint_label.pack(side='right', padx=10)
        
        # 綁定提示標籤點擊事件，顯示完整快捷鍵說明
        self.status_hint_label.bind('<Button-1>', lambda e: self._show_shortcuts_help())
        
        # 第二行：下次播放時間和重置按鈕
        status_row2 = tk.Frame(status_frame, bg=self.colors['bg_main'])
        status_row2.pack(fill='x', padx=15, pady=(0, 5))
        
        self.next_time_label = tk.Label(
            status_row2,
            text="",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=(self.font_family, 10),
            anchor='w'
        )
        self.next_time_label.pack(side='left', fill='x', expand=True)
        
        # 重置視窗按鈕（自救機制）
        reset_btn = tk.Button(
            status_row2,
            text="🔄 重置視窗",
            command=self._reset_window_size,
            font=(self.font_family, 9),
            bg=self.colors['text_secondary'],
            fg='white',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            padx=8,
            pady=4,
            cursor='hand2',
            activebackground='#5D6D7E',
            activeforeground='white'
        )
        reset_btn.pack(side='right', padx=(5, 0))
        
        # 添加工具提示
        self._create_tooltip(reset_btn, "重置視窗大小為預設值\n快捷鍵：Ctrl+0")
        
        # 開機自動啟動選項（放在第二行右側）
        try:
            from core.autostart import is_in_startup, add_to_startup, remove_from_startup
            
            self.autostart_var = tk.BooleanVar(value=is_in_startup())
            autostart_check = tk.Checkbutton(
                status_row2,
                text="開機時自動啟動",
                variable=self.autostart_var,
                command=self.toggle_autostart,
                bg=self.colors['bg_main'],
                fg=self.colors['text_primary'],
                font=(self.font_family, 9),
                activebackground=self.colors['bg_main'],
                activeforeground=self.colors['text_primary'],
                selectcolor=self.colors['bg_card']
            )
            autostart_check.pack(side='right', padx=(10, 0))
        except Exception as e:
            print(f"無法載入自動啟動模組: {e}")
        
        # UI設置完成後，強制更新Canvas以確保內容可見
        self.root.update_idletasks()
        if hasattr(self, 'canvas') and hasattr(self, 'scrollable_frame') and hasattr(self, 'canvas_window'):
            # 設置scrollable_frame的寬度跟隨canvas
            canvas_width = max(self.canvas.winfo_width(), 800)
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            # 強制更新scrollregion
            self.scrollable_frame.update_idletasks()
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def setup_tray(self):
        """設定系統託盤"""
        try:
            self.tray = SystemTray(
                on_show=self.show_window,
                on_quit=self.quit_app
            )
            self.tray.start()
        except Exception as e:
            print(f"系統託盤初始化失敗: {e}")
    
    def show_window(self):
        """顯示視窗"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def on_closing(self):
        """視窗關閉事件"""
        # 最小化到託盤而不是關閉
        self.root.withdraw()
    
    def quit_app(self):
        """退出應用"""
        # 保存資料
        self.save_schedules()
        # 清理資源
        self.player.cleanup()
        self.scheduler.stop()
        if self.tray:
            self.tray.stop()
        self.root.quit()
        self.root.destroy()
    
    def update_time_display(self):
        """更新時間顯示（優化：避免遞迴深度問題，確保時間完整顯示）"""
        try:
            now = datetime.now()
            # 使用較短的格式，確保在窄視窗也能完整顯示
            # 格式：2025-11-05 06:47:32 → 11/05 06:47（更短更易讀）
            time_str = now.strftime("%m/%d %H:%M:%S")
            self.time_label.config(text=f"目前時間：{time_str}")
            
            # 更新下一個播放時間
            next_info = self.scheduler.get_next_play_time()
            if next_info:
                if 'days' in next_info:
                    self.next_time_label.config(text=f"下次播放：{next_info['days']}天後 {next_info['time']}")
                else:
                    self.next_time_label.config(text=f"下次播放：今天 {next_info['time']}")
            else:
                self.next_time_label.config(text="")
        except Exception as e:
            print(f"更新時間顯示錯誤: {e}")
        finally:
            # 使用after而不是遞迴調用，避免堆疊問題
            if hasattr(self, 'root') and self.root:
                self.root.after(1000, self.update_time_display)
    
    def on_drop(self, event):
        """處理檔案拖放（非阻塞驗證）"""
        files = self.root.tk.splitlist(event.data)
        
        # 如果檔案數量少（<=10），直接驗證；否則使用背景執行緒
        if len(files) <= 10:
            valid_files, invalid_files = validate_dropped_files(files)
            self._handle_validation_result(valid_files, invalid_files)
        else:
            # 大量檔案時使用背景執行緒驗證
            self.status_label.config(text="正在驗證檔案...")
            threading.Thread(
                target=self._validate_files_async,
                args=(files,),
                daemon=True
            ).start()
    
    def _validate_files_async(self, files):
        """在背景執行緒中驗證檔案"""
        valid_files, invalid_files = validate_dropped_files(files)
        # 在主執行緒中更新UI
        self.root.after(0, self._handle_validation_result, valid_files, invalid_files)
    
    def _handle_validation_result(self, valid_files, invalid_files):
        """處理驗證結果"""
        if invalid_files:
            error_msg = "以下檔案無法新增：\n"
            for file_path, reason in invalid_files[:5]:  # 最多顯示5個錯誤
                error_msg += f"{os.path.basename(file_path)}: {reason}\n"
            if len(invalid_files) > 5:
                error_msg += f"...還有 {len(invalid_files) - 5} 個檔案無法新增\n"
            messagebox.showwarning("檔案驗證失敗", error_msg)
        
        # 檢查檔案列表大小限制
        remaining_slots = self.max_selected_files - len(self.selected_files)
        if remaining_slots <= 0:
            messagebox.showwarning("提示", f"已達到檔案列表上限（{self.max_selected_files}個），請先移除部分檔案")
            self.update_file_listbox()
            self.status_label.config(text="就緒")
            return
        
        # 只新增可容納的檔案數量
        files_to_add = valid_files[:remaining_slots]
        if len(valid_files) > remaining_slots:
            messagebox.showinfo("提示", 
                f"已新增 {remaining_slots} 個檔案（達到上限）。\n"
                f"還有 {len(valid_files) - remaining_slots} 個檔案未新增。")
        
        self.selected_files.extend(files_to_add)
        self.update_file_listbox()
        self.status_label.config(text="就緒")
    
    def select_files(self):
        """選擇檔案（非阻塞驗證）"""
        files = filedialog.askopenfilenames(
            title="選擇音訊檔案",
            filetypes=[
                ("音訊檔案", "*.mp3 *.wav *.wma *.ogg *.flac *.m4a *.aac"),
                ("所有檔案", "*.*")
            ]
        )
        
        if files:
            # 如果檔案數量少（<=10），直接驗證；否則使用背景執行緒
            if len(files) <= 10:
                valid_files, invalid_files = validate_dropped_files(files)
                self._handle_validation_result(valid_files, invalid_files)
            else:
                # 大量檔案時使用背景執行緒驗證
                self.status_label.config(text="正在驗證檔案...")
                threading.Thread(
                    target=self._validate_files_async,
                    args=(files,),
                    daemon=True
                ).start()
    
    def update_file_listbox(self):
        """更新檔案列表顯示"""
        # 限制檔案列表大小（最多50個檔案）
        MAX_FILES = 50
        if len(self.selected_files) > MAX_FILES:
            # 保留最新的50個檔案
            self.selected_files = self.selected_files[-MAX_FILES:]
            messagebox.showwarning("提示", f"檔案列表已限制為最多{MAX_FILES}個檔案，已移除舊的檔案")
        
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
    
    def remove_selected_file(self):
        """移除選取的檔案"""
        selection = self.file_listbox.curselection()
        if selection:
            try:
                index = selection[0]
                if 0 <= index < len(self.selected_files):
                    del self.selected_files[index]
                    self.update_file_listbox()
                else:
                    messagebox.showwarning("提示", "選取的檔案索引無效")
            except Exception as e:
                messagebox.showerror("錯誤", f"移除檔案時發生錯誤：{str(e)}")
        else:
            messagebox.showinfo("提示", "請先選擇要移除的檔案")
    
    def clear_files(self):
        """清空檔案列表"""
        self.selected_files = []
        self.update_file_listbox()
    
    def add_schedule_with_dialog(self):
        """新增播放排程（使用彈窗，預載右側設定）"""
        # 從右側設定區域獲取預設值
        selected_days = [day for day, var in self.day_vars.items() if var.get()]
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            time_str = f"{hour:02d}:{minute:02d}"
        except ValueError:
            time_str = "15:40"
        
        name = self.schedule_name_var.get().strip()
        if not name:
            name = "上課提醒"
        
        # 創建臨時排程對象用於預載入彈窗
        preset_schedule = {
            'name': name,
            'days': selected_days,
            'time': time_str,
            'files': []
        }
        
        # 打開彈窗（預載入右側設定）
        dialog = ScheduleDialog(self.root, self.font_family, self.colors, schedule=preset_schedule)
        self.root.wait_window(dialog.dialog)
        
        # 檢查結果
        if dialog.result is None:
            return  # 用戶取消
        
        # 創建播放排程
        schedule = {
            'id': self.next_schedule_id,
            'name': dialog.result['name'],
            'days': dialog.result['days'],
            'time': dialog.result['time'],
            'files': dialog.result['files'],
            'duration': 0
        }
        self._ensure_schedule_duration(schedule, recompute=True)
        
        self.next_schedule_id += 1
        
        # 新增到列表
        self.schedules.append(schedule)
        
        # 更新顯示和調度器
        self.update_schedule_tree()
        
        # 自動保存
        self.save_schedules()
        
        messagebox.showinfo("成功", "播放排程已新增")
    
    def update_schedule_tree(self):
        """更新播放排程樹形顯示"""
        # 清空現有項
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # 新增所有排程
        for schedule in self.schedules:
            # 格式化週幾顯示
            day_names = {
                'monday': '週一',
                'tuesday': '週二',
                'wednesday': '週三',
                'thursday': '週四',
                'friday': '週五',
                'saturday': '週六',
                'sunday': '週日'
            }
            days_display = ','.join([day_names.get(day, day) for day in schedule['days']])
            
            # 格式化音訊檔案顯示（顯示前3個檔案名，超過顯示...）
            files = schedule.get('files', [])
            if files:
                file_names = [os.path.basename(f) for f in files[:3]]
                files_display = '、'.join(file_names)
                if len(files) > 3:
                    files_display += f'... (共{len(files)}個)'
            else:
                files_display = '無檔案'
            
            duration_seconds = self._ensure_schedule_duration(schedule)
            end_display = self._compose_end_time_label(schedule.get('time'), duration_seconds)
            
            self.schedule_tree.insert('', 'end', values=(
                schedule['name'],
                days_display,
                schedule['time'],
                end_display,
                files_display,
                len(files)
            ), tags=(schedule['id'],))
        
        # 更新排程器
        self.scheduler.set_schedules(self.schedules)
    
    def edit_selected_schedule(self):
        """編輯選取的播放排程（使用彈窗）"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇一個播放排程")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = int(item['tags'][0])
        
        # 找到對應的排程
        schedule = None
        for s in self.schedules:
            if s['id'] == schedule_id:
                schedule = s
                break
        
        if not schedule:
            return
        
        # 打開彈窗（編輯模式）
        dialog = ScheduleDialog(self.root, self.font_family, self.colors, schedule=schedule)
        self.root.wait_window(dialog.dialog)
        
        # 檢查結果
        if dialog.result is None:
            return  # 用戶取消
        
        # 刪除舊排程
        self.delete_schedule_by_id(schedule_id)
        
        # 創建新排程（保持原ID）
        new_schedule = {
            'id': schedule_id,  # 保持原ID
            'name': dialog.result['name'],
            'days': dialog.result['days'],
            'time': dialog.result['time'],
            'files': dialog.result['files'],
            'duration': 0
        }
        self._ensure_schedule_duration(new_schedule, recompute=True)
        
        # 新增到列表
        self.schedules.append(new_schedule)
        
        # 更新顯示和調度器
        self.update_schedule_tree()
        
        # 自動保存
        self.save_schedules()
        
        messagebox.showinfo("成功", "播放排程已更新")
    
    def edit_schedule(self, event):
        """雙擊編輯（綁定事件）"""
        self.edit_selected_schedule()
    
    def delete_selected_schedule(self):
        """刪除選取的播放排程"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇一個播放排程")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = int(item['tags'][0])
        
        if messagebox.askyesno("確認", "確定要刪除這個播放排程嗎？"):
            self.delete_schedule_by_id(schedule_id)
    
    def delete_schedule_by_id(self, schedule_id):
        """根據ID刪除播放排程"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        self.scheduler.remove_schedule(schedule_id)
        self.update_schedule_tree()
        self.save_schedules()
    
    def test_selected_schedule(self):
        """測試播放選取的排程"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇一個播放排程")
            return
        
        try:
            item = self.schedule_tree.item(selection[0])
            if not item['tags']:
                messagebox.showerror("錯誤", "無法獲取排程資訊")
                return
            schedule_id = int(item['tags'][0])
            
            # 找到對應的排程
            schedule = None
            for s in self.schedules:
                if s['id'] == schedule_id:
                    schedule = s
                    break
            
            if not schedule:
                messagebox.showerror("錯誤", "找不到對應的播放排程")
                return
            
            # 檢查檔案
            if not schedule.get('files'):
                messagebox.showwarning("錯誤", "排程中沒有音訊檔案")
                return
            
            # 測試播放
            valid_files = [f for f in schedule['files'] if os.path.exists(f)]
            if not valid_files:
                messagebox.showwarning("錯誤", "排程中的檔案不存在或無法存取")
                return
            
            self.pending_schedules.clear()
            self.current_schedule = None
            self.player.play_immediately(valid_files)
            messagebox.showinfo("提示", "測試播放已開始")
        except (ValueError, IndexError, KeyError) as e:
            messagebox.showerror("錯誤", f"測試播放時發生錯誤：{str(e)}")
    
    def _on_schedule_trigger(self, schedule):
        """播放排程觸發時的回調"""
        try:
            schedule_name = schedule.get('name', '未知排程')
            print(f"播放排程觸發: {schedule_name}")
            
            # 通知使用者
            self.notifier.notify_schedule_triggered(schedule_name)
            
            # 開始播放
            files = schedule.get('files', [])
            if files:
                valid_files = [f for f in files if os.path.exists(f)]
                if valid_files:
                    self._enqueue_schedule_playback(schedule, valid_files)
                else:
                    self.status_label.config(text=f"播放失敗：{schedule_name} - 檔案不存在")
            else:
                self.status_label.config(text=f"播放失敗：{schedule_name} - 沒有音訊檔案")
        except Exception as e:
            print(f"播放排程觸發錯誤: {e}")
            self.status_label.config(text=f"播放錯誤：{str(e)}")
    
    def _on_playback_start(self, file_path):
        """播放開始回調"""
        file_name = os.path.basename(file_path)
        self.status_label.config(text=f"播放中：{file_name}")
        
        # 更新播放控制區域
        if hasattr(self, 'playback_status_label'):
            self.playback_status_label.config(text=f"正在播放：{file_name}")
        if hasattr(self, 'stop_btn'):
            self.stop_btn.config(state='normal')
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = 0
        
        # 通知
        self.notifier.notify_playback_start(file_name)
        
        # 託盤圖示閃爍
        if self.tray:
            self.tray.start_blinking()
        
        # 開始更新進度條
        self._update_playback_progress()
    
    def _on_playback_end(self):
        """播放結束回調"""
        queue_size = self.player.get_queue_size()
        if queue_size == 0 and not self.player.is_playing:
            if self.pending_schedules:
                self._start_next_pending_schedule()
            else:
                self.current_schedule = None
                self.status_label.config(text="就緒")
                if hasattr(self, 'playback_status_label'):
                    self.playback_status_label.config(text="目前無播放")
                if hasattr(self, 'stop_btn'):
                    self.stop_btn.config(state='disabled')
                if hasattr(self, 'progress_bar'):
                    self.progress_bar['value'] = 0
                if hasattr(self, 'progress_time_label'):
                    self.progress_time_label.config(text="--:-- / --:--")
        else:
            self.status_label.config(text=f"佇列中：{queue_size} 個檔案")
            if hasattr(self, 'playback_status_label'):
                self.playback_status_label.config(text=f"佇列中：{queue_size} 個檔案")
        
        # 停止託盤圖示閃爍
        if self.tray:
            self.tray.stop_blinking()
    
    def load_schedules(self):
        """載入播放排程"""
        data = self.storage.load_schedules()
        self.schedules = data.get('schedules', [])
        for schedule in self.schedules:
            self._ensure_schedule_duration(schedule)
        
        # 更新下一個ID
        if self.schedules:
            max_id = max(s.get('id', 0) for s in self.schedules)
            self.next_schedule_id = max_id + 1
        else:
            self.next_schedule_id = 1
        
        # 更新排程器
        self.scheduler.set_schedules(self.schedules)
        
        # 更新顯示
        self.update_schedule_tree()
    
    def save_schedules(self):
        """保存播放排程"""
        for schedule in self.schedules:
            self._ensure_schedule_duration(schedule)
        data = {
            'schedules': self.schedules
        }
        self.storage.save_schedules(data)
    
    def stop_playback(self):
        """停止播放"""
        try:
            self.player.stop()
            self.status_label.config(text="已停止播放")
            if hasattr(self, 'playback_status_label'):
                self.playback_status_label.config(text="已停止播放")
            if hasattr(self, 'stop_btn'):
                self.stop_btn.config(state='disabled')
            if hasattr(self, 'progress_bar'):
                self.progress_bar['value'] = 0
            if hasattr(self, 'progress_time_label'):
                self.progress_time_label.config(text="--:-- / --:--")
            
            # 停止託盤圖示閃爍
            if self.tray:
                self.tray.stop_blinking()
            self.pending_schedules.clear()
            self.current_schedule = None
        except Exception as e:
            messagebox.showerror("錯誤", f"停止播放失敗：{str(e)}")
    
    def _calculate_schedule_duration(self, files):
        if not files:
            return None
        total = get_total_duration(files)
        if total and total > 0:
            return int(total)
        return None

    def _ensure_schedule_duration(self, schedule, recompute=False):
        if recompute or 'duration_seconds' not in schedule:
            duration_seconds = self._calculate_schedule_duration(schedule.get('files', []))
            schedule['duration_seconds'] = duration_seconds
            schedule['duration'] = duration_seconds
        return schedule.get('duration_seconds')

    def _format_duration_text(self, duration_seconds):
        if duration_seconds is None:
            return "未知"
        return format_duration(duration_seconds)

    def _compose_end_time_label(self, start_time, duration_seconds):
        if duration_seconds is None:
            return "未知"
        duration_text = self._format_duration_text(duration_seconds)
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
        except (TypeError, ValueError):
            return f"未知（{duration_text}）"
        finish_dt = datetime.combine(datetime.today().date(), start_dt.time()) + timedelta(seconds=duration_seconds)
        end_str = finish_dt.strftime("%H:%M")
        return f"{end_str}（{duration_text}）"

    def _enqueue_schedule_playback(self, schedule, files):
        duration_seconds = self._ensure_schedule_duration(schedule)
        if self.player.is_playing or self.player.get_queue_size() > 0:
            self.pending_schedules.append((schedule, files))
            wait_text = f"等待播放：{schedule.get('name', '播放排程')}（待播 {len(self.pending_schedules)}）"
            self.status_label.config(text=wait_text)
            if hasattr(self, 'playback_status_label'):
                self.playback_status_label.config(text=wait_text)
            return

        self.current_schedule = schedule
        self.player.enqueue_files(files)
        start_text = f"正在播放：{schedule.get('name', '播放排程')}"
        if duration_seconds:
            start_text += f"（約 {self._format_duration_text(duration_seconds)}）"
        self.status_label.config(text=start_text)
        if hasattr(self, 'playback_status_label'):
            self.playback_status_label.config(text=start_text)

    def _start_next_pending_schedule(self):
        if not self.pending_schedules:
            self.current_schedule = None
            return
        next_schedule, files = self.pending_schedules.popleft()
        self.current_schedule = next_schedule
        self.player.enqueue_files(files)
        duration_seconds = self._ensure_schedule_duration(next_schedule)
        start_text = f"正在播放：{next_schedule.get('name', '播放排程')}"
        if duration_seconds:
            start_text += f"（約 {self._format_duration_text(duration_seconds)}）"
        self.status_label.config(text=start_text)
        if hasattr(self, 'playback_status_label'):
            self.playback_status_label.config(text=start_text)
        if hasattr(self, 'progress_time_label'):
            self.progress_time_label.config(text="--:-- / --:--")

    def _update_playback_progress(self):
        """更新播放進度條（定期調用）"""
        if not hasattr(self, 'progress_bar'):
            return
        
        try:
            if self.player.is_playing:
                # 獲取播放進度
                progress = self.player.get_playback_progress()
                position = self.player.get_playback_position()
                duration = self.player.current_file_duration
                
                if progress is not None:
                    # 更新進度條
                    self.progress_bar['value'] = progress * 100
                
                # 更新時間顯示
                if position is not None and duration is not None:
                    current_time = format_duration(position)
                    total_time = format_duration(duration)
                    self.progress_time_label.config(text=f"{current_time} / {total_time}")
                elif position is not None:
                    current_time = format_duration(position)
                    self.progress_time_label.config(text=f"{current_time} / --:--")
                
                # 繼續更新（每100ms更新一次）
                self.root.after(100, self._update_playback_progress)
            else:
                # 播放已停止，重置進度條
                queue_size = self.player.get_queue_size()
                if queue_size > 0:
                    # 還有佇列，繼續更新
                    self.root.after(500, self._update_playback_progress)
                else:
                    # 完全停止，重置UI
                    self.progress_bar['value'] = 0
                    self.progress_time_label.config(text="--:-- / --:--")
        except Exception as e:
            print(f"更新播放進度錯誤: {e}")
            # 即使出錯也繼續嘗試更新
            self.root.after(500, self._update_playback_progress)
    
    def toggle_autostart(self):
        """切換開機自動啟動"""
        try:
            from core.autostart import add_to_startup, remove_from_startup
            
            if self.autostart_var.get():
                success, message = add_to_startup()
                if success:
                    messagebox.showinfo("成功", "已設置開機自動啟動")
                else:
                    messagebox.showerror("錯誤", message)
                    self.autostart_var.set(False)
            else:
                success, message = remove_from_startup()
                if success:
                    messagebox.showinfo("成功", "已取消開機自動啟動")
                else:
                    messagebox.showwarning("提示", message)
        except Exception as e:
            messagebox.showerror("錯誤", f"設置失敗: {str(e)}")
            self.autostart_var.set(False)
    
    def run(self):
        """執行主迴圈"""
        self.root.mainloop()
