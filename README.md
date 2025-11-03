# 自动广播系统 (RadioPotato)

本程式由僑務委員會外交替代役 李孟一老師所開發，如有問題可用line聯繫：dreamone09

## 功能特点

- 拖放音频文件到窗口即可添加
- 可视化播放清单
- 支持按周几和时间自动播放
- 播放队列系统（冲突任务自动排队）
- 系统托盘支持（最小化后台运行）
- Windows通知提醒
- 自动保存播放计划
- 便携式设计（无需安装）

## 使用说明

1. 将 `RadioPotato.exe` 复制到任意位置或随身碟
2. 双击运行程序
3. 拖放音频文件到窗口
4. 选择播放的周几和时间
5. 点击"添加播放计划"
6. 最小化窗口到托盘，程序会在设定时间自动播放

## 开发说明

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

### 打包为exe

```bash
pyinstaller build.spec
```

打包后的exe位于 `dist/RadioPotato.exe`

