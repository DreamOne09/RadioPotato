"""
主窗口界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from datetime import datetime

# 尝试导入tkinterdnd2，如果失败则使用普通Tk
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    TkinterDnD = tk.Tk
    DND_FILES = None
    HAS_DND = False
    print("警告: tkinterdnd2未安装，拖放功能不可用，请使用'选择音频文件'按钮")

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.storage import Storage
from core.player import AudioPlayer
from core.scheduler import Scheduler
from core.dragdrop import validate_dropped_files
from core.notifier import Notifier
from core.tray import SystemTray

class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        self.root = TkinterDnD.Tk()
        self.root.title("自动广播系统")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 初始化核心组件
        self.storage = Storage()
        self.player = AudioPlayer(
            on_playback_start=self._on_playback_start,
            on_playback_end=self._on_playback_end
        )
        self.scheduler = Scheduler(on_schedule_trigger=self._on_schedule_trigger)
        self.notifier = Notifier()
        self.tray = None
        
        # 数据
        self.schedules = []
        self.selected_files = []  # 当前选择的文件列表
        self.next_schedule_id = 1
        
        # UI组件
        self.setup_ui()
        
        # 加载保存的数据
        self.load_schedules()
        
        # 启动调度器
        self.scheduler.start()
        
        # 启动系统托盘
        self.setup_tray()
        
        # 启动时间更新
        self.update_time_display()
        
        # 处理窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        """设置UI界面"""
        # 顶部区域 - 标题和时间显示
        top_frame = tk.Frame(self.root, bg='#f0f0f0', height=60)
        top_frame.pack(fill='x', padx=10, pady=5)
        top_frame.pack_propagate(False)
        
        title_label = tk.Label(top_frame, text="自动广播系统", font=('Arial', 16, 'bold'), bg='#f0f0f0')
        title_label.pack(side='left', padx=10)
        
        self.time_label = tk.Label(top_frame, text="", font=('Arial', 12), bg='#f0f0f0', fg='#666')
        self.time_label.pack(side='right', padx=10)
        
        # 中间区域
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左侧：拖放区域
        left_frame = tk.LabelFrame(main_frame, text="拖放音频文件", width=300)
        left_frame.pack(side='left', fill='both', padx=(0, 5))
        
        # 拖放区域
        self.drop_frame = tk.Frame(left_frame, bg='#e8e8e8', relief='dashed', borderwidth=2, height=200)
        self.drop_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        drop_label = tk.Label(self.drop_frame, text="拖放音频文件到这里\n或点击按钮选择文件", 
                              bg='#e8e8e8', font=('Arial', 10), justify='center')
        drop_label.pack(expand=True)
        
        # 注册拖放事件（如果支持）
        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        # 选择文件按钮
        select_btn = tk.Button(left_frame, text="选择音频文件", command=self.select_files)
        select_btn.pack(pady=5)
        
        # 当前选择的文件列表
        list_label = tk.Label(left_frame, text="已选择文件:")
        list_label.pack(anchor='w', padx=10, pady=(10, 0))
        
        self.file_listbox = tk.Listbox(left_frame, height=8)
        self.file_listbox.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 文件列表操作按钮
        file_btn_frame = tk.Frame(left_frame)
        file_btn_frame.pack(pady=5)
        
        remove_file_btn = tk.Button(file_btn_frame, text="移除选中", command=self.remove_selected_file)
        remove_file_btn.pack(side='left', padx=5)
        
        clear_files_btn = tk.Button(file_btn_frame, text="清空列表", command=self.clear_files)
        clear_files_btn.pack(side='left', padx=5)
        
        # 右侧：播放计划和设置
        right_frame = tk.LabelFrame(main_frame, text="播放计划设置")
        right_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
        
        # 周几选择
        days_frame = tk.LabelFrame(right_frame, text="选择周几")
        days_frame.pack(fill='x', padx=10, pady=5)
        
        self.day_vars = {}
        weekdays = [
            ('周一', 'monday'),
            ('周二', 'tuesday'),
            ('周三', 'wednesday'),
            ('周四', 'thursday'),
            ('周五', 'friday'),
            ('周六', 'saturday'),
            ('周日', 'sunday')
        ]
        
        for i, (label, value) in enumerate(weekdays):
            var = tk.BooleanVar()
            self.day_vars[value] = var
            cb = tk.Checkbutton(days_frame, text=label, variable=var)
            cb.grid(row=i//4, column=i%4, padx=5, pady=2, sticky='w')
        
        # 时间设置
        time_frame = tk.LabelFrame(right_frame, text="播放时间")
        time_frame.pack(fill='x', padx=10, pady=5)
        
        time_inner = tk.Frame(time_frame)
        time_inner.pack(pady=5)
        
        tk.Label(time_inner, text="时:").pack(side='left', padx=5)
        self.hour_var = tk.StringVar(value="15")
        hour_spin = tk.Spinbox(time_inner, from_=0, to=23, width=5, textvariable=self.hour_var, format="%02.0f")
        hour_spin.pack(side='left', padx=5)
        
        tk.Label(time_inner, text="分:").pack(side='left', padx=5)
        self.minute_var = tk.StringVar(value="40")
        minute_spin = tk.Spinbox(time_inner, from_=0, to=59, width=5, textvariable=self.minute_var, format="%02.0f")
        minute_spin.pack(side='left', padx=5)
        
        # 计划名称
        name_frame = tk.Frame(right_frame)
        name_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(name_frame, text="计划名称:").pack(side='left')
        self.schedule_name_var = tk.StringVar(value="上课提醒")
        name_entry = tk.Entry(name_frame, textvariable=self.schedule_name_var, width=20)
        name_entry.pack(side='left', padx=5)
        
        # 添加计划按钮
        add_btn = tk.Button(right_frame, text="添加播放计划", command=self.add_schedule, 
                           bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        add_btn.pack(pady=10)
        
        # 播放计划列表
        schedule_frame = tk.LabelFrame(right_frame, text="播放计划列表")
        schedule_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 创建Treeview显示播放计划
        columns = ('名称', '周几', '时间', '文件数')
        self.schedule_tree = ttk.Treeview(schedule_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.schedule_tree.heading(col, text=col)
            self.schedule_tree.column(col, width=100)
        
        self.schedule_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 绑定双击编辑
        self.schedule_tree.bind('<Double-1>', self.edit_schedule)
        
        # 计划操作按钮
        schedule_btn_frame = tk.Frame(schedule_frame)
        schedule_btn_frame.pack(pady=5)
        
        test_btn = tk.Button(schedule_btn_frame, text="测试播放", command=self.test_selected_schedule)
        test_btn.pack(side='left', padx=5)
        
        edit_btn = tk.Button(schedule_btn_frame, text="编辑", command=self.edit_selected_schedule)
        edit_btn.pack(side='left', padx=5)
        
        delete_btn = tk.Button(schedule_btn_frame, text="删除", command=self.delete_selected_schedule)
        delete_btn.pack(side='left', padx=5)
        
        # 底部状态栏
        status_frame = tk.Frame(self.root, bg='#f0f0f0', height=30)
        status_frame.pack(fill='x', side='bottom', padx=10, pady=5)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="就绪", bg='#f0f0f0', anchor='w')
        self.status_label.pack(side='left', padx=10, fill='x', expand=True)
        
        self.next_time_label = tk.Label(status_frame, text="", bg='#f0f0f0')
        self.next_time_label.pack(side='right', padx=10)
        
        # 版权信息
        copyright_label = tk.Label(status_frame, 
                                   text="本程式由僑務委員會外交替代役 李孟一老師所開發，如有問題可用line聯繫：dreamone09",
                                   bg='#f0f0f0', fg='#666', font=('Arial', 8))
        copyright_label.pack(side='bottom', pady=2)
    
    def setup_tray(self):
        """设置系统托盘"""
        try:
            self.tray = SystemTray(
                on_show=self.show_window,
                on_quit=self.quit_app
            )
            self.tray.start()
        except Exception as e:
            print(f"系统托盘初始化失败: {e}")
    
    def show_window(self):
        """显示窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def on_closing(self):
        """窗口关闭事件"""
        # 最小化到托盘而不是关闭
        self.root.withdraw()
    
    def quit_app(self):
        """退出应用"""
        # 保存数据
        self.save_schedules()
        # 清理资源
        self.player.cleanup()
        self.scheduler.stop()
        if self.tray:
            self.tray.stop()
        self.root.quit()
        self.root.destroy()
    
    def update_time_display(self):
        """更新时间显示"""
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"当前时间: {time_str}")
        
        # 更新下一个播放时间
        next_info = self.scheduler.get_next_play_time()
        if next_info:
            if 'days' in next_info:
                self.next_time_label.config(text=f"下次播放: {next_info['days']}天后 {next_info['time']}")
            else:
                self.next_time_label.config(text=f"下次播放: 今天 {next_info['time']}")
        else:
            self.next_time_label.config(text="")
        
        # 每秒更新一次
        self.root.after(1000, self.update_time_display)
    
    def on_drop(self, event):
        """处理文件拖放"""
        files = self.root.tk.splitlist(event.data)
        valid_files, invalid_files = validate_dropped_files(files)
        
        if invalid_files:
            error_msg = "以下文件无法添加:\n"
            for file_path, reason in invalid_files[:5]:  # 最多显示5个错误
                error_msg += f"{os.path.basename(file_path)}: {reason}\n"
            messagebox.showwarning("文件验证失败", error_msg)
        
        self.selected_files.extend(valid_files)
        self.update_file_listbox()
    
    def select_files(self):
        """选择文件"""
        files = filedialog.askopenfilenames(
            title="选择音频文件",
            filetypes=[
                ("音频文件", "*.mp3 *.wav *.wma *.ogg *.flac *.m4a *.aac"),
                ("所有文件", "*.*")
            ]
        )
        
        if files:
            valid_files, invalid_files = validate_dropped_files(files)
            if invalid_files:
                error_msg = "以下文件无法添加:\n"
                for file_path, reason in invalid_files[:5]:
                    error_msg += f"{os.path.basename(file_path)}: {reason}\n"
                messagebox.showwarning("文件验证失败", error_msg)
            
            self.selected_files.extend(valid_files)
            self.update_file_listbox()
    
    def update_file_listbox(self):
        """更新文件列表显示"""
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
    
    def remove_selected_file(self):
        """移除选中的文件"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            del self.selected_files[index]
            self.update_file_listbox()
    
    def clear_files(self):
        """清空文件列表"""
        self.selected_files = []
        self.update_file_listbox()
    
    def add_schedule(self):
        """添加播放计划"""
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择音频文件")
            return
        
        # 获取选择的周几
        selected_days = [day for day, var in self.day_vars.items() if var.get()]
        if not selected_days:
            messagebox.showwarning("提示", "请至少选择一天")
            return
        
        # 获取时间
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            time_str = f"{hour:02d}:{minute:02d}"
        except ValueError:
            messagebox.showerror("错误", "时间格式不正确")
            return
        
        # 获取计划名称
        name = self.schedule_name_var.get().strip()
        if not name:
            name = f"播放计划 {self.next_schedule_id}"
        
        # 创建播放计划
        schedule = {
            'id': self.next_schedule_id,
            'name': name,
            'days': selected_days,
            'time': time_str,
            'files': self.selected_files.copy(),  # 保存完整路径
            'duration': 0  # 总时长（可选）
        }
        
        self.next_schedule_id += 1
        
        # 添加到列表
        self.schedules.append(schedule)
        self.scheduler.add_schedule(schedule)
        
        # 更新显示
        self.update_schedule_tree()
        
        # 清空选择
        self.selected_files = []
        self.update_file_listbox()
        
        # 自动保存
        self.save_schedules()
        
        messagebox.showinfo("成功", "播放计划已添加")
    
    def update_schedule_tree(self):
        """更新播放计划树形显示"""
        # 清空现有项
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        
        # 添加所有计划
        for schedule in self.schedules:
            # 格式化周几显示
            day_names = {
                'monday': '周一',
                'tuesday': '周二',
                'wednesday': '周三',
                'thursday': '周四',
                'friday': '周五',
                'saturday': '周六',
                'sunday': '周日'
            }
            days_display = ','.join([day_names.get(day, day) for day in schedule['days']])
            
            self.schedule_tree.insert('', 'end', values=(
                schedule['name'],
                days_display,
                schedule['time'],
                len(schedule['files'])
            ), tags=(schedule['id'],))
        
        # 更新调度器
        self.scheduler.set_schedules(self.schedules)
    
    def edit_selected_schedule(self):
        """编辑选中的播放计划"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个播放计划")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = int(item['tags'][0])
        
        # 找到对应的计划
        schedule = None
        for s in self.schedules:
            if s['id'] == schedule_id:
                schedule = s
                break
        
        if not schedule:
            return
        
        # 这里可以实现一个编辑对话框
        # 为了简化，我们直接允许用户修改并重新添加
        # 加载到输入区域
        self.selected_files = schedule['files'].copy()
        self.update_file_listbox()
        
        # 设置周几
        for day, var in self.day_vars.items():
            var.set(day in schedule['days'])
        
        # 设置时间
        hour, minute = schedule['time'].split(':')
        self.hour_var.set(hour)
        self.minute_var.set(minute)
        
        # 设置名称
        self.schedule_name_var.set(schedule['name'])
        
        # 删除旧计划
        self.delete_schedule_by_id(schedule_id)
        
        messagebox.showinfo("提示", "计划已加载到编辑区域，修改后点击'添加播放计划'保存")
    
    def edit_schedule(self, event):
        """双击编辑（绑定事件）"""
        self.edit_selected_schedule()
    
    def delete_selected_schedule(self):
        """删除选中的播放计划"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个播放计划")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = int(item['tags'][0])
        
        if messagebox.askyesno("确认", "确定要删除这个播放计划吗？"):
            self.delete_schedule_by_id(schedule_id)
    
    def delete_schedule_by_id(self, schedule_id):
        """根据ID删除播放计划"""
        self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
        self.scheduler.remove_schedule(schedule_id)
        self.update_schedule_tree()
        self.save_schedules()
    
    def test_selected_schedule(self):
        """测试播放选中的计划"""
        selection = self.schedule_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个播放计划")
            return
        
        item = self.schedule_tree.item(selection[0])
        schedule_id = int(item['tags'][0])
        
        # 找到对应的计划
        schedule = None
        for s in self.schedules:
            if s['id'] == schedule_id:
                schedule = s
                break
        
        if not schedule:
            return
        
        # 测试播放
        valid_files = [f for f in schedule['files'] if os.path.exists(f)]
        if not valid_files:
            messagebox.showwarning("错误", "计划中的文件不存在")
            return
        
        self.player.play_files(valid_files)
        messagebox.showinfo("提示", "测试播放已开始")
    
    def _on_schedule_trigger(self, schedule):
        """播放计划触发时的回调"""
        print(f"播放计划触发: {schedule['name']}")
        
        # 通知用户
        self.notifier.notify_schedule_triggered(schedule['name'])
        
        # 开始播放
        valid_files = [f for f in schedule['files'] if os.path.exists(f)]
        if valid_files:
            self.player.play_files(valid_files)
            self.status_label.config(text=f"正在播放: {schedule['name']}")
        else:
            self.status_label.config(text=f"播放失败: {schedule['name']} - 文件不存在")
    
    def _on_playback_start(self, file_path):
        """播放开始回调"""
        file_name = os.path.basename(file_path)
        self.status_label.config(text=f"播放中: {file_name}")
        
        # 通知
        self.notifier.notify_playback_start(file_name)
        
        # 托盘图标闪烁
        if self.tray:
            self.tray.start_blinking()
    
    def _on_playback_end(self):
        """播放结束回调"""
        queue_size = self.player.get_queue_size()
        if queue_size > 0:
            self.status_label.config(text=f"队列中: {queue_size} 个文件")
        else:
            self.status_label.config(text="空闲")
        
        # 停止托盘图标闪烁
        if self.tray:
            self.tray.stop_blinking()
    
    def load_schedules(self):
        """加载播放计划"""
        data = self.storage.load_schedules()
        self.schedules = data.get('schedules', [])
        
        # 更新下一个ID
        if self.schedules:
            max_id = max(s.get('id', 0) for s in self.schedules)
            self.next_schedule_id = max_id + 1
        else:
            self.next_schedule_id = 1
        
        # 更新调度器
        self.scheduler.set_schedules(self.schedules)
        
        # 更新显示
        self.update_schedule_tree()
    
    def save_schedules(self):
        """保存播放计划"""
        data = {
            'schedules': self.schedules
        }
        self.storage.save_schedules(data)
    
    def run(self):
        """运行主循环"""
        self.root.mainloop()

