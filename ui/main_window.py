"""
主視窗介面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import threading
from datetime import datetime
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

# 添加父目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.storage import Storage
from core.player import AudioPlayer
from core.scheduler import Scheduler
from core.dragdrop import validate_dropped_files
from core.notifier import Notifier
from core.tray import SystemTray

class MainWindow:
    """主視窗類別"""
    
    def __init__(self):
        """初始化主視窗"""
        self.root = TkinterDnD.Tk()
        self.root.title("自動廣播系統")
        self.root.geometry("1100x700")
        self.root.minsize(800, 600)  # 降低最小尺寸，讓縮小時也能使用
        
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
        """檢測可用的中文字體，提供回退機制"""
        # 優先順序：微軟雅黑 > 微軟正黑體 > 新細明體 > TkDefaultFont
        font_candidates = [
            'Microsoft YaHei UI',
            'Microsoft YaHei',
            'Microsoft JhengHei UI',
            'Microsoft JhengHei',
            'MingLiU',
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
                return font_name
            except:
                continue
        
        # 如果都不可用，使用系統預設字體
        test_label.destroy()
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
    
    def setup_ui(self):
        """設定UI介面"""
        # 頂部區域 - 標題和時間顯示（移除Big Logo，優化空間）
        top_frame = tk.Frame(self.root, bg=self.colors['bg_main'], height=60)
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.pack_propagate(False)
        
        # 標題和時間
        title_row = tk.Frame(top_frame, bg=self.colors['bg_main'])
        title_row.pack(fill='x', pady=5)
        
        # 左側：標題
        title_label = tk.Label(
            title_row,
            text="自動廣播系統",
            font=(self.font_family, 18, 'bold'),
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary']
        )
        title_label.pack(side='left', padx=10)
        
        # 右側：時間
        self.time_label = tk.Label(
            title_row,
            text="",
            font=(self.font_family, 13),
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary']
        )
        self.time_label.pack(side='right', padx=10)
        
        # 版權資訊（增大字體，更易讀取）
        copyright_top = tk.Label(
            top_frame,
            text="本程式由僑務委員會外交替代役 李孟一老師所開發，如有問題可用line聯繫：dreamone09",
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            font=(self.font_family, 11),
            anchor='w'
        )
        copyright_top.pack(fill='x', padx=10, pady=(0, 5))
        
        # 中間區域 - 使用PanedWindow讓左右可調整大小
        main_paned = tk.PanedWindow(self.root, orient='horizontal', bg=self.colors['bg_main'], sashwidth=5)
        main_paned.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左側：拖放區域（現代化卡片設計）
        left_container = tk.Frame(main_paned, bg=self.colors['bg_main'])
        
        left_card = tk.Frame(
            left_container,
            bg=self.colors['bg_card'],
            relief='flat',
            borderwidth=1,
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        left_card.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 標題（優化間距）
        left_title = tk.Label(
            left_card,
            text="音訊檔案管理",
            font=(self.font_family, 15, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        left_title.pack(pady=(12, 8))
        
        # 拖放區域（優化視覺效果）
        self.drop_frame = tk.Frame(
            left_card,
            bg=self.colors['bg_accent'],
            relief='flat',
            borderwidth=2,
            highlightbackground=self.colors['primary'],
            highlightthickness=2,
            height=160
        )
        self.drop_frame.pack(fill='x', padx=20, pady=12)
        
        drop_label = tk.Label(
            self.drop_frame,
            text="📁 將音訊檔案拖放到這裡\n或點擊下方按鈕選擇檔案",
            bg=self.colors['bg_accent'],
            font=(self.font_family, 12),
            fg=self.colors['text_primary'],
            justify='center',
            wraplength=250
        )
        drop_label.pack(expand=True, pady=15)
        
        # 註冊拖放事件（如果支援）
        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        # 選擇檔案按鈕（優化樣式）
        select_btn = tk.Button(
            left_card,
            text="📂 選擇音訊檔案",
            command=self.select_files,
            font=(self.font_family, 13, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            relief='raised',
            borderwidth=2,
            padx=20,
            pady=12,
            cursor='hand2',
            activebackground=self.colors['primary_hover'],
            activeforeground='white'
        )
        select_btn.pack(pady=8, padx=20, fill='x')
        
        # 目前選擇的檔案列表
        list_label = tk.Label(
            left_card,
            text="已選擇檔案：",
            font=(self.font_family, 13, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        list_label.pack(anchor='w', padx=20, pady=(15, 5))
        
        # 檔案列表框（增大字體，確保可見）
        listbox_frame = tk.Frame(left_card, bg=self.colors['bg_card'])
        listbox_frame.pack(fill='both', expand=True, padx=20, pady=5)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.file_listbox = tk.Listbox(
            listbox_frame,
            height=8,
            font=(self.font_family, 12),
            bg='white',  # 使用白色背景確保可見
            fg='black',  # 使用黑色文字確保可見
            selectbackground=self.colors['primary'],
            selectforeground='white',
            borderwidth=2,
            relief='solid',
            highlightthickness=1,
            yscrollcommand=scrollbar.set
        )
        self.file_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 檔案列表操作按鈕（增大按鈕，更易點擊）
        file_btn_frame = tk.Frame(left_card, bg=self.colors['bg_card'])
        file_btn_frame.pack(fill='x', padx=20, pady=(10, 15))
        
        remove_file_btn = tk.Button(
            file_btn_frame,
            text="🗑️ 移除選中",
            command=self.remove_selected_file,
            font=(self.font_family, 13, 'bold'),
            bg=self.colors['danger'],
            fg='white',
            relief='raised',
            borderwidth=2,
            padx=20,
            pady=12,
            cursor='hand2',
            activebackground='#C62828',
            activeforeground='white'
        )
        remove_file_btn.pack(side='left', padx=(0, 5), fill='x', expand=True)
        
        clear_files_btn = tk.Button(
            file_btn_frame,
            text="🧹 清空列表",
            command=self.clear_files,
            font=(self.font_family, 13, 'bold'),
            bg=self.colors['text_secondary'],
            fg='white',
            relief='raised',
            borderwidth=2,
            padx=20,
            pady=12,
            cursor='hand2',
            activebackground='#5D6D7E',
            activeforeground='white'
        )
        clear_files_btn.pack(side='left', padx=(5, 0), fill='x', expand=True)
        
        # 將左側添加到PanedWindow
        main_paned.add(left_container, minsize=350, width=450)
        
        # 右側：播放計劃設定（現代化卡片設計）
        right_container = tk.Frame(main_paned, bg=self.colors['bg_main'])
        
        right_card = tk.Frame(
            right_container,
            bg=self.colors['bg_card'],
            relief='flat',
            borderwidth=1,
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        right_card.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 標題（優化間距）
        right_title = tk.Label(
            right_card,
            text="播放計劃設定",
            font=(self.font_family, 15, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        right_title.pack(pady=(12, 8))
        
        # 播放設定區域（縮小，節省空間）
        settings_frame = tk.Frame(right_card, bg=self.colors['bg_card'])
        settings_frame.pack(fill='x', padx=15, pady=8)
        
        # 日期和時間放在同一行（緊湊布局）
        datetime_row = tk.Frame(settings_frame, bg=self.colors['bg_card'])
        datetime_row.pack(fill='x', pady=5)
        
        # 左側：日期選擇（單行，增大框框）
        days_frame = tk.Frame(datetime_row, bg=self.colors['bg_accent'], relief='flat')
        days_frame.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        days_title = tk.Label(
            days_frame,
            text="日期",
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        )
        days_title.pack(pady=(5, 5))
        
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
        days_inner.pack(pady=(0, 5))
        
        for i, (label, value) in enumerate(weekdays):
            var = tk.BooleanVar()
            self.day_vars[value] = var
            cb = tk.Checkbutton(
                days_inner,
                text=label,
                variable=var,
                font=(self.font_family, 12, 'bold'),  # 增大字體
                bg=self.colors['bg_accent'],
                fg=self.colors['text_primary'],
                selectcolor=self.colors['bg_card'],
                activebackground=self.colors['bg_accent'],
                activeforeground=self.colors['text_primary'],
                indicatoron=True,  # 使用標準複選框樣式
                width=4,  # 增大點擊區域
                height=2  # 增大高度
            )
            # 單行排列，增加間距
            cb.grid(row=0, column=i, padx=8, pady=5, sticky='w')
        
        # 右側：時間選擇（優化樣式）
        time_frame = tk.Frame(datetime_row, bg=self.colors['bg_accent'], relief='flat')
        time_frame.pack(side='right', fill='x', expand=True, padx=(5, 0))
        
        time_title = tk.Label(
            time_frame,
            text="時間",
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        )
        time_title.pack(pady=(5, 5))
        
        time_inner = tk.Frame(time_frame, bg=self.colors['bg_accent'])
        time_inner.pack(pady=(0, 5))
        
        tk.Label(
            time_inner,
            text="時",
            font=(self.font_family, 11),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(side='left', padx=5)
        
        self.hour_var = tk.StringVar(value="15")
        hour_spin = tk.Spinbox(
            time_inner,
            from_=0,
            to=23,
            width=5,
            textvariable=self.hour_var,
            format="%02.0f",
            font=(self.font_family, 11, 'bold'),
            relief='solid',
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['primary']
        )
        hour_spin.pack(side='left', padx=8)
        
        tk.Label(
            time_inner,
            text="分",
            font=(self.font_family, 11),
            bg=self.colors['bg_accent'],
            fg=self.colors['text_primary']
        ).pack(side='left', padx=5)
        
        self.minute_var = tk.StringVar(value="40")
        minute_spin = tk.Spinbox(
            time_inner,
            from_=0,
            to=59,
            width=5,
            textvariable=self.minute_var,
            format="%02.0f",
            font=(self.font_family, 11, 'bold'),
            relief='solid',
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['primary']
        )
        minute_spin.pack(side='left', padx=8)
        
        # 計劃名稱和添加按鈕（緊湊布局）
        name_btn_row = tk.Frame(right_card, bg=self.colors['bg_card'])
        name_btn_row.pack(fill='x', padx=15, pady=5)
        
        name_label = tk.Label(
            name_btn_row,
            text="名稱：",
            font=(self.font_family, 11),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        name_label.pack(side='left', padx=(0, 5))
        
        self.schedule_name_var = tk.StringVar(value="上課提醒")
        name_entry = tk.Entry(
            name_btn_row,
            textvariable=self.schedule_name_var,
            width=15,
            font=(self.font_family, 12),
            relief='solid',
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.colors['border'],
            highlightcolor=self.colors['primary']
        )
        name_entry.pack(side='left', padx=(0, 8), fill='x', expand=True)
        
        # 添加計劃按鈕（縮小）
        add_btn = tk.Button(
            name_btn_row,
            text="➕ 添加",
            command=self.add_schedule,
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['success'],
            fg='white',
            relief='raised',
            borderwidth=2,
            padx=15,
            pady=8,
            cursor='hand2',
            activebackground=self.colors['success_hover'],
            activeforeground='white'
        )
        add_btn.pack(side='right')
        
        # 播放計劃列表（確保有滾輪，縮小時也能看到）
        schedule_card = tk.Frame(
            right_card,
            bg=self.colors['bg_card']
        )
        schedule_card.pack(fill='both', expand=True, padx=15, pady=5)
        
        schedule_title = tk.Label(
            schedule_card,
            text="播放計劃列表",
            font=(self.font_family, 12, 'bold'),
            bg=self.colors['bg_card'],
            fg=self.colors['text_primary']
        )
        schedule_title.pack(pady=(0, 5))
        
        # 創建Treeview顯示播放計劃（確保有滾輪）
        tree_frame = tk.Frame(schedule_card, bg=self.colors['bg_card'])
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('名稱', '週幾', '時間', '音訊檔案', '檔案數')
        self.schedule_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',  # 只顯示標題，不顯示tree列，避免重複
            height=6  # 減少高度，確保縮小時也能顯示
        )
        
        # 設定Treeview樣式（緊湊但可見）
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Treeview', 
                       font=(self.font_family, 10), 
                       rowheight=30,  # 減少行高
                       background='white',
                       foreground='black',
                       fieldbackground='white')
        style.configure('Treeview.Heading', 
                       font=(self.font_family, 10, 'bold'),
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
                self.schedule_tree.column(col, width=100, minwidth=80)
            elif col == '音訊檔案':
                self.schedule_tree.column(col, width=180, minwidth=120)
            elif col == '週幾':
                self.schedule_tree.column(col, width=100, minwidth=80)
            else:
                self.schedule_tree.column(col, width=60, minwidth=50)
        
        scrollbar_tree = ttk.Scrollbar(tree_frame, orient='vertical', command=self.schedule_tree.yview)
        self.schedule_tree.configure(yscrollcommand=scrollbar_tree.set)
        
        self.schedule_tree.pack(side='left', fill='both', expand=True)
        scrollbar_tree.pack(side='right', fill='y')
        
        # 綁定雙擊編輯
        self.schedule_tree.bind('<Double-1>', self.edit_schedule)
        
        # 計劃操作按鈕
        schedule_btn_frame = tk.Frame(schedule_card, bg=self.colors['bg_card'])
        schedule_btn_frame.pack(pady=10)
        
        test_btn = tk.Button(
            schedule_btn_frame,
            text="🎵 測試播放",
            command=self.test_selected_schedule,
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['primary'],
            fg='white',
            relief='raised',
            borderwidth=2,
            padx=15,
            pady=10,
            cursor='hand2',
            activebackground=self.colors['primary_hover'],
            activeforeground='white'
        )
        test_btn.pack(side='left', padx=5)
        
        edit_btn = tk.Button(
            schedule_btn_frame,
            text="✏️ 編輯",
            command=self.edit_selected_schedule,
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['text_secondary'],
            fg='white',
            relief='raised',
            borderwidth=2,
            padx=15,
            pady=10,
            cursor='hand2',
            activebackground='#5D6D7E',
            activeforeground='white'
        )
        edit_btn.pack(side='left', padx=5)
        
        delete_btn = tk.Button(
            schedule_btn_frame,
            text="🗑️ 刪除",
            command=self.delete_selected_schedule,
            font=(self.font_family, 11, 'bold'),
            bg=self.colors['danger'],
            fg='white',
            relief='raised',
            borderwidth=2,
            padx=15,
            pady=10,
            cursor='hand2',
            activebackground='#C62828',
            activeforeground='white'
        )
        delete_btn.pack(side='left', padx=5)
        
        # 將右側添加到PanedWindow
        main_paned.add(right_container, minsize=350, width=600)
        
        # 底部狀態列（只顯示狀態和自動啟動選項）
        status_frame = tk.Frame(
            self.root,
            bg=self.colors['bg_main'],
            height=60
        )
        status_frame.pack(fill='x', side='bottom', padx=15, pady=(0, 5))
        status_frame.pack_propagate(False)
        
        # 狀態列
        status_inner = tk.Frame(status_frame, bg=self.colors['bg_main'])
        status_inner.pack(fill='x', padx=15, pady=5)
        
        self.status_label = tk.Label(
            status_inner,
            text="就緒",
            bg=self.colors['bg_main'],
            fg=self.colors['text_primary'],
            font=(self.font_family, 12),
            anchor='w'
        )
        self.status_label.pack(side='left', fill='x', expand=True)
        
        self.next_time_label = tk.Label(
            status_inner,
            text="",
            bg=self.colors['bg_main'],
            fg=self.colors['text_secondary'],
            font=(self.font_family, 11)
        )
        self.next_time_label.pack(side='right', padx=10)
        
        # 開機自動啟動選項（放在狀態列右側）
        try:
            from core.autostart import is_in_startup, add_to_startup, remove_from_startup
            
            self.autostart_var = tk.BooleanVar(value=is_in_startup())
            autostart_check = tk.Checkbutton(
                status_inner,
                text="開機時自動啟動",
                variable=self.autostart_var,
                command=self.toggle_autostart,
                bg=self.colors['bg_main'],
                fg=self.colors['text_primary'],
                font=(self.font_family, 10),
                activebackground=self.colors['bg_main'],
                activeforeground=self.colors['text_primary'],
                selectcolor=self.colors['bg_card']
            )
            autostart_check.pack(side='right', padx=(10, 0))
        except Exception as e:
            print(f"無法載入自動啟動模組: {e}")
    
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
        """更新時間顯示（優化：避免遞迴深度問題）"""
        try:
            now = datetime.now()
            time_str = now.strftime("%Y-%m-%d %H:%M:%S")
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
            error_msg = "以下檔案無法添加：\n"
            for file_path, reason in invalid_files[:5]:  # 最多顯示5個錯誤
                error_msg += f"{os.path.basename(file_path)}: {reason}\n"
            if len(invalid_files) > 5:
                error_msg += f"...還有 {len(invalid_files) - 5} 個檔案無法添加\n"
            messagebox.showwarning("檔案驗證失敗", error_msg)
        
        # 檢查檔案列表大小限制
        remaining_slots = self.max_selected_files - len(self.selected_files)
        if remaining_slots <= 0:
            messagebox.showwarning("提示", f"已達到檔案列表上限（{self.max_selected_files}個），請先移除部分檔案")
            self.update_file_listbox()
            self.status_label.config(text="就緒")
            return
        
        # 只添加可容納的檔案數量
        files_to_add = valid_files[:remaining_slots]
        if len(valid_files) > remaining_slots:
            messagebox.showinfo("提示", 
                f"已添加 {remaining_slots} 個檔案（達到上限）。\n"
                f"還有 {len(valid_files) - remaining_slots} 個檔案未添加。")
        
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
        """移除選中的檔案"""
        selection = self.file_listbox.curselection()
        if selection:
            try:
                index = selection[0]
                if 0 <= index < len(self.selected_files):
                    del self.selected_files[index]
                    self.update_file_listbox()
                else:
                    messagebox.showwarning("提示", "選中的檔案索引無效")
            except Exception as e:
                messagebox.showerror("錯誤", f"移除檔案時發生錯誤：{str(e)}")
        else:
            messagebox.showinfo("提示", "請先選擇要移除的檔案")
    
    def clear_files(self):
        """清空檔案列表"""
        self.selected_files = []
        self.update_file_listbox()
    
    def add_schedule(self):
        """添加播放計劃"""
        if not self.selected_files:
            messagebox.showwarning("提示", "請先選擇音訊檔案")
            return
        
        # 獲取選擇的周幾
        selected_days = [day for day, var in self.day_vars.items() if var.get()]
        if not selected_days:
            messagebox.showwarning("提示", "請至少選擇一天")
            return
        
        # 獲取時間
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            time_str = f"{hour:02d}:{minute:02d}"
        except ValueError:
            messagebox.showerror("錯誤", "時間格式不正確")
            return
        
        # 獲取計劃名稱
        name = self.schedule_name_var.get().strip()
        if not name:
            name = f"播放計劃{self.next_schedule_id}"
        
        # 創建播放計劃
        schedule = {
            'id': self.next_schedule_id,
            'name': name,
            'days': selected_days,
            'time': time_str,
            'files': self.selected_files.copy(),  # 保存完整路徑
            'duration': 0  # 總時長（可選）
        }
        
        self.next_schedule_id += 1
        
        # 添加到列表（只添加一次，update_schedule_tree會同步到調度器）
        self.schedules.append(schedule)
        
        # 更新顯示和調度器
        self.update_schedule_tree()
        
        # 清空選擇
        self.selected_files = []
        self.update_file_listbox()
        
        # 自動保存
        self.save_schedules()
        
        messagebox.showinfo("成功", "播放計劃已添加")
    
    def update_schedule_tree(self):
        """更新播放計劃樹形顯示"""
        # 清空現有項
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # 添加所有計劃
        for schedule in self.schedules:
            # 格式化周幾顯示
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
            
            self.schedule_tree.insert('', 'end', values=(
                schedule['name'],
                days_display,
                schedule['time'],
                files_display,
                len(files)
            ), tags=(schedule['id'],))
        
        # 更新排程器
        self.scheduler.set_schedules(self.schedules)
    
    def edit_selected_schedule(self):
        """編輯選中的播放計劃"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇一個播放計劃")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = int(item['tags'][0])
        
        # 找到對應的計劃
        schedule = None
        for s in self.schedules:
            if s['id'] == schedule_id:
                schedule = s
                break
        
        if not schedule:
            return
        
        # 載入到輸入區域
        self.selected_files = schedule['files'].copy()
        self.update_file_listbox()
        
        # 設定周幾
        for day, var in self.day_vars.items():
            var.set(day in schedule['days'])
        
        # 設定時間
        hour, minute = schedule['time'].split(':')
        self.hour_var.set(hour)
        self.minute_var.set(minute)
        
        # 設定名稱
        self.schedule_name_var.set(schedule['name'])
        
        # 刪除舊計劃
        self.delete_schedule_by_id(schedule_id)
        
        messagebox.showinfo("提示", "計劃已載入到編輯區域，修改後點擊「添加播放計劃」保存")
    
    def edit_schedule(self, event):
        """雙擊編輯（綁定事件）"""
        self.edit_selected_schedule()
    
    def delete_selected_schedule(self):
        """刪除選中的播放計劃"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇一個播放計劃")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = int(item['tags'][0])
        
        if messagebox.askyesno("確認", "確定要刪除這個播放計劃嗎？"):
            self.delete_schedule_by_id(schedule_id)
    
    def delete_schedule_by_id(self, schedule_id):
        """根據ID刪除播放計劃"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        self.scheduler.remove_schedule(schedule_id)
        self.update_schedule_tree()
        self.save_schedules()
    
    def test_selected_schedule(self):
        """測試播放選中的計劃"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "請先選擇一個播放計劃")
            return
        
        try:
            item = self.schedule_tree.item(selection[0])
            if not item['tags']:
                messagebox.showerror("錯誤", "無法獲取計劃資訊")
                return
            schedule_id = int(item['tags'][0])
            
            # 找到對應的計劃
            schedule = None
            for s in self.schedules:
                if s['id'] == schedule_id:
                    schedule = s
                    break
            
            if not schedule:
                messagebox.showerror("錯誤", "找不到對應的播放計劃")
                return
            
            # 檢查檔案
            if not schedule.get('files'):
                messagebox.showwarning("錯誤", "計劃中沒有音訊檔案")
                return
            
            # 測試播放
            valid_files = [f for f in schedule['files'] if os.path.exists(f)]
            if not valid_files:
                messagebox.showwarning("錯誤", "計劃中的檔案不存在或無法存取")
                return
            
            self.player.play_files(valid_files)
            messagebox.showinfo("提示", "測試播放已開始")
        except (ValueError, IndexError, KeyError) as e:
            messagebox.showerror("錯誤", f"測試播放時發生錯誤：{str(e)}")
    
    def _on_schedule_trigger(self, schedule):
        """播放計劃觸發時的回調"""
        try:
            schedule_name = schedule.get('name', '未知計劃')
            print(f"播放計劃觸發: {schedule_name}")
            
            # 通知使用者
            self.notifier.notify_schedule_triggered(schedule_name)
            
            # 開始播放
            files = schedule.get('files', [])
            if files:
                valid_files = [f for f in files if os.path.exists(f)]
                if valid_files:
                    self.player.play_files(valid_files)
                    self.status_label.config(text=f"正在播放：{schedule_name}")
                else:
                    self.status_label.config(text=f"播放失敗：{schedule_name} - 檔案不存在")
            else:
                self.status_label.config(text=f"播放失敗：{schedule_name} - 沒有音訊檔案")
        except Exception as e:
            print(f"播放計劃觸發錯誤: {e}")
            self.status_label.config(text=f"播放錯誤：{str(e)}")
    
    def _on_playback_start(self, file_path):
        """播放開始回調"""
        file_name = os.path.basename(file_path)
        self.status_label.config(text=f"播放中：{file_name}")
        
        # 通知
        self.notifier.notify_playback_start(file_name)
        
        # 託盤圖示閃爍
        if self.tray:
            self.tray.start_blinking()
    
    def _on_playback_end(self):
        """播放結束回調"""
        queue_size = self.player.get_queue_size()
        if queue_size > 0:
            self.status_label.config(text=f"佇列中：{queue_size} 個檔案")
        else:
            self.status_label.config(text="就緒")
        
        # 停止託盤圖示閃爍
        if self.tray:
            self.tray.stop_blinking()
    
    def load_schedules(self):
        """載入播放計劃"""
        data = self.storage.load_schedules()
        self.schedules = data.get('schedules', [])
        
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
        """保存播放計劃"""
        data = {
            'schedules': self.schedules
        }
        self.storage.save_schedules(data)
    
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
