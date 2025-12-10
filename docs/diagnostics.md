# RadioPotato 診斷與打包流程

本文件說明推送前如何驗證自動廣播系統的核心功能並打包成 Windows 可執行檔。

## 1. 診斷腳本

執行下列指令會完成環境檢查、語法檢查、核心測試與資源檢查：

```bash
python tools/run_diagnostics.py
```

若暫時不需執行測試（例如 CI 中缺少音效裝置），可以加上 `--skip-tests`：

```bash
python tools/run_diagnostics.py --skip-tests
```

診斷涵蓋範圍：

- 核心模組：`core/` 下的播放、排程、通知、單一執行實例、儲存等邏輯。
- 介面整合：`ui/main_window.py`、`core/tray.py`、`core/autostart.py`。
- 測試腳本與打包設定：`simple_test.py`、`test_functionality.py`、`build.spec`。
- 關鍵資源檔案與 `data/` 目錄寫入權限。

若診斷失敗，輸出會列出需要處理的項目與詳細 log 檔案。

## 2. Pre-push 自動化腳本

### Windows（PowerShell）

```powershell
powershell -ExecutionPolicy Bypass -File tools\prepush.ps1
```

參數：

- `-SkipTests`：略過 `simple_test.py` 與 `test_functionality.py`。
- `-SkipBuild`：在診斷成功後跳過 PyInstaller 打包。

### macOS / Linux（Bash）

```bash
./tools/prepush.sh
```

參數：

- `--skip-tests`
- `--skip-build`

## 3. Git pre-push Hook 範例

若想在每次 `git push` 前自動執行診斷與打包，可在 `.git/hooks/pre-push` 新增：

```bash
#!/usr/bin/env bash
exec "$(git rev-parse --show-toplevel)/tools/prepush.sh" "$@"
```

或在 Windows 上建立 `.git/hooks/pre-push.ps1`：

```powershell
powershell -ExecutionPolicy Bypass -File (Join-Path (git rev-parse --show-toplevel) "tools\prepush.ps1")
```

記得賦予執行權限：

```bash
chmod +x tools/prepush.sh .git/hooks/pre-push
```

## 4. PyInstaller 打包快捷方式

pre-push 腳本會自動執行 `pyinstaller build.spec`。如需手動打包：

```bash
pyinstaller build.spec
# 或
python -m PyInstaller build.spec
```

打包結果會輸出至 `dist/radioone.exe`。

