# 自动广播系统 (RadioPotato)

本程式由僑務委員會外交替代役 李孟一老師所開發，如有問題可用line聯繫：dreamone09

一个便携式自动广播系统，支持定时播放、文件拖放、播放队列、系统托盘等功能，兼容Windows 8及老旧系统。

## 功能特点

- ✅ **拖放文件**：支持拖放多个音频文件到窗口
- ✅ **可视化播放清单**：清晰显示所有播放计划
- ✅ **定时播放**：支持按周几和时间自动播放
- ✅ **播放队列**：多个任务冲突时自动排队播放
- ✅ **系统托盘**：最小化后台运行，播放时图标闪烁
- ✅ **Windows通知**：播放时弹出系统通知提醒
- ✅ **自动保存**：播放计划自动保存，下次打开保留
- ✅ **便携式设计**：无需安装，复制到随身碟即可使用

## 快速开始

### 安装依赖（开发用）

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

## 使用说明

详细使用说明请参考 [USAGE.md](USAGE.md)

## 测试与打包

测试和打包指南请参考 [TEST_AND_BUILD.md](TEST_AND_BUILD.md)

## 技术栈

- **Python 3.7+**
- **Tkinter** - GUI界面
- **pygame** - 音频播放
- **pystray** - 系统托盘
- **win10toast** - Windows通知
- **PyInstaller** - 打包工具

## 系统要求

- Windows 8 或更高版本
- 无需安装Python（打包后）

## 许可证

本项目由李孟一老師開發，供教育使用。
