# 自動廣播系統 (radioone)

本程式由僑務委員會外交替代役 李孟一老師所開發，如有問題可用line聯繫：dreamone09

一個便攜式自動廣播系統，支援定時播放、檔案拖放、播放佇列、系統託盤等功能，相容Windows 8及老舊系統。

## 功能特點

- ✅ **拖放檔案**：支援拖放多個音訊檔案到視窗
- ✅ **可視化播放清單**：清晰顯示所有播放計劃
- ✅ **定時播放**：支援按周幾和時間自動播放
- ✅ **播放佇列**：多個任務衝突時自動排隊播放
- ✅ **系統託盤**：最小化後台運行，播放時圖示閃爍
- ✅ **Windows通知**：播放時彈出系統通知提醒
- ✅ **自動保存**：播放計劃自動保存，下次打開保留
- ✅ **便攜式設計**：無需安裝，複製到隨身碟即可使用

## 快速開始

### 安裝依賴（開發用）

```bash
pip install -r requirements.txt
```

### 運行程式

```bash
python main.py
```

### 打包為exe

```bash
pyinstaller build.spec
```

打包後的exe位於 `dist/radioone.exe`

## 使用說明

詳細使用說明請參考 [USAGE.md](USAGE.md)

## 測試與打包

測試和打包指南請參考 [TEST_AND_BUILD.md](TEST_AND_BUILD.md)

## 技術棧

- **Python 3.7+**
- **Tkinter** - GUI介面
- **pygame** - 音訊播放
- **pystray** - 系統託盤
- **win10toast** - Windows通知
- **PyInstaller** - 打包工具

## 系統要求

- Windows 8 或更高版本
- 無需安裝Python（打包後）

## 授權

本專案由李孟一老師開發，供教育使用。
