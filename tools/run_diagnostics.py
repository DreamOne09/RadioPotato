#!/usr/bin/env python3
"""
RadioPotato 自動廣播系統診斷工具。

覆蓋範圍：
1. 核心排程與播放邏輯（core/scheduler.py、core/player.py、core/storage.py、core/notifier.py、core/dragdrop.py）
2. 介面與系統整合（ui/main_window.py、core/tray.py、core/autostart.py）
3. 測試腳本與打包設定（simple_test.py、test_functionality.py、build.spec）
4. 關鍵資源（data/ 資料夾、RadioOne Logo.png 等）
"""

from __future__ import annotations

import argparse
import compileall
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:  # Python 3.8+
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover
    import importlib_metadata  # type: ignore

try:  # Optional，比較版本號
    from packaging.version import InvalidVersion, Version
except Exception:  # pragma: no cover - 若環境缺少 packaging，退回字串比較
    Version = None  # type: ignore[misc]
    InvalidVersion = Exception  # type: ignore[misc]


ROOT = Path(__file__).resolve().parents[1]
PYTHON_MIN_VERSION = (3, 8)
REQUIREMENTS_FILE = ROOT / "requirements.txt"
RESOURCE_CHECKS = [
    ("RadioOne Logo.png", "主視覺 Logo"),
    ("Radio One Big Logo.png", "大型 Logo"),
    ("build.spec", "PyInstaller 設定檔"),
]
SCOPE_SUMMARY = {
    "核心模組": [
        "core/storage.py",
        "core/scheduler.py",
        "core/player.py",
        "core/notifier.py",
        "core/dragdrop.py",
        "core/audio_utils.py",
        "core/singleton.py",
    ],
    "界面與系統整合": [
        "ui/main_window.py",
        "core/tray.py",
        "core/autostart.py",
    ],
    "測試與工具": [
        "simple_test.py",
        "test_functionality.py",
        "build.spec",
    ],
    "關鍵資源": [
        "data/",
        "RadioOne Logo.png",
        "Radio One Big Logo.png",
        "dist/（打包輸出目錄）",
    ],
}


@dataclass
class CheckResult:
    name: str
    success: bool
    message: str = ""

    def render(self) -> str:
        status = "✓" if self.success else "✗"
        return f"{status} {self.name}: {self.message}".rstrip()


def colorize(text: str, success: bool) -> str:
    """在支援 ANSI 的終端顯示顏色。PowerShell 新版支援 ANSI。"""
    if not sys.stdout.isatty():
        return text
    color_code = "\x1b[32m" if success else "\x1b[31m"
    reset = "\x1b[0m"
    return f"{color_code}{text}{reset}"


def print_header() -> None:
    print("=" * 60)
    print("RadioPotato 自動廣播系統診斷".center(60))
    print("=" * 60)
    scope_lines = []
    for group, items in SCOPE_SUMMARY.items():
        scope_lines.append(f"- {group}: {', '.join(items)}")
    print("診斷涵蓋範圍：")
    print(textwrap.indent("\n".join(scope_lines), prefix="  "))
    print("-" * 60)


def check_python_version() -> CheckResult:
    current = sys.version_info
    min_str = ".".join(map(str, PYTHON_MIN_VERSION))
    curr_str = f"{current.major}.{current.minor}.{current.micro}"
    success = current >= PYTHON_MIN_VERSION
    message = f"目前為 Python {curr_str}（最低需求 {min_str}）"
    return CheckResult("Python 版本檢查", success, message)


def parse_requirements(requirements_path: Path) -> List[Tuple[str, Optional[str]]]:
    requirements: List[Tuple[str, Optional[str]]] = []
    if not requirements_path.exists():
        return requirements

    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ">" in line or "=" in line:
            for operator in (">=", "==", ">"):
                if operator in line:
                    name, version = line.split(operator, 1)
                    requirements.append((name.strip(), version.strip()))
                    break
            else:
                requirements.append((line, None))
        else:
            requirements.append((line, None))
    return requirements


def compare_versions(installed: str, required: str) -> bool:
    if Version is None:
        # 後備策略：最簡單的比較，僅供參考
        return installed >= required
    try:
        return Version(installed) >= Version(required)
    except InvalidVersion:
        return installed >= required


def check_requirements() -> CheckResult:
    if not REQUIREMENTS_FILE.exists():
        return CheckResult("依賴檢查", False, f"找不到 {REQUIREMENTS_FILE}")

    missing: List[str] = []
    outdated: List[str] = []

    for package, required_version in parse_requirements(REQUIREMENTS_FILE):
        pkg_name = package.replace("_", "-")
        try:
            installed_version = importlib_metadata.version(pkg_name)
        except importlib_metadata.PackageNotFoundError:
            missing.append(package)
            continue

        if required_version and not compare_versions(installed_version, required_version):
            outdated.append(f"{package}（已安裝 {installed_version}，需求 {required_version}）")

    success = not missing and not outdated
    details: List[str] = []
    if missing:
        details.append("缺少：" + ", ".join(sorted(missing)))
    if outdated:
        details.append("版本過舊：" + "; ".join(outdated))
    if not details:
        details.append("所有需求套件皆可用")

    return CheckResult("依賴檢查", success, "；".join(details))


def check_resources() -> List[CheckResult]:
    results: List[CheckResult] = []
    for relative, description in RESOURCE_CHECKS:
        target = ROOT / relative
        if target.exists():
            results.append(CheckResult(f"資源檢查 - {description}", True, f"{relative} 就緒"))
        else:
            results.append(CheckResult(f"資源檢查 - {description}", False, f"{relative} 缺失"))

    # 寫入測試（data/ 下）
    storage_dir = ROOT / "data"
    storage_dir.mkdir(exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(dir=storage_dir, delete=True) as tmp:
            tmp.write(b"diagnostic")
            tmp.flush()
        results.append(CheckResult("資料目錄寫入測試", True, "data/ 具有寫入權限"))
    except Exception as exc:  # pragma: no cover - 實際環境才會觸發
        results.append(CheckResult("資料目錄寫入測試", False, f"無法寫入 data/：{exc}"))

    return results


def run_compile_checks() -> CheckResult:
    targets = [ROOT / "core", ROOT / "ui"]
    failed: List[str] = []
    for target in targets:
        if not target.exists():
            continue
        compiled = compileall.compile_dir(
            str(target),
            quiet=1,
            force=False,
            legacy=True,
        )
        if not compiled:
            failed.append(str(target.relative_to(ROOT)))
    success = not failed
    message = "語法檢查通過" if success else f"compileall 失敗：{', '.join(failed)}"
    return CheckResult("語法快速檢查", success, message)


def run_test_scripts() -> List[CheckResult]:
    results: List[CheckResult] = []
    test_scripts = [
        ("simple_test.py", "核心模組快速載入"),
        ("test_functionality.py", "功能整合測試"),
    ]
    env = os.environ.copy()
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    for script, description in test_scripts:
        path = ROOT / script
        if not path.exists():
            results.append(CheckResult(f"測試 - {description}", False, f"找不到 {script}"))
            continue

        cmd = [sys.executable, str(path)]
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        success = proc.returncode == 0
        if success:
            message = "執行成功"
        else:
            log_path = ROOT / "build" / f"{path.stem}.log"
            log_path.parent.mkdir(exist_ok=True, parents=True)
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            log_path.write_text(stdout_text + "\n" + stderr_text, encoding="utf-8")
            message = f"失敗（詳見 {log_path.relative_to(ROOT)}）"
        results.append(CheckResult(f"測試 - {description}", success, message))

    return results


def check_pyinstaller_available() -> CheckResult:
    cmd = shutil.which("pyinstaller")
    if cmd:
        return CheckResult("PyInstaller 可用性", True, f"使用路徑：{cmd}")
    # 退回 python -m PyInstaller 測試
    test_cmd = [sys.executable, "-m", "PyInstaller", "--version"]
    try:
        proc = subprocess.run(
            test_cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:  # pragma: no cover
        return CheckResult("PyInstaller 可用性", False, f"呼叫失敗：{exc}")

    if proc.returncode == 0:
        version = proc.stdout.strip() or proc.stderr.strip()
        return CheckResult("PyInstaller 可用性", True, f"版本：{version}")
    return CheckResult(
        "PyInstaller 可用性",
        False,
        "無法偵測到 pyinstaller，請先執行 `pip install -r requirements.txt`",
    )


def summarize(results: Iterable[CheckResult]) -> Tuple[int, int]:
    passed = sum(1 for r in results if r.success)
    total = sum(1 for _ in results)
    return passed, total


def run_diagnostics(skip_tests: bool = False) -> int:
    print_header()

    all_results: List[CheckResult] = []

    checks: List[CheckResult] = [
        check_python_version(),
        check_requirements(),
        run_compile_checks(),
        check_pyinstaller_available(),
    ]
    all_results.extend(checks)
    all_results.extend(check_resources())

    if not skip_tests:
        all_results.extend(run_test_scripts())
    else:
        all_results.append(CheckResult("測試腳本", True, "已跳過（命令列參數）"))

    failures = [res for res in all_results if not res.success]
    for res in all_results:
        print(colorize(res.render(), res.success))

    print("-" * 60)
    print(
        f"總結：{len(all_results) - len(failures)}/{len(all_results)} 項通過"
    )
    if failures:
        print("需處理的項目：")
        for res in failures:
            print(f"  - {res.name}: {res.message}")
        return 1

    print("🎉 診斷全部通過，可以進行打包與推送。")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="RadioPotato 自動廣播系統診斷工具"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="略過 simple_test.py 與 test_functionality.py",
    )
    args = parser.parse_args(argv)
    return run_diagnostics(skip_tests=args.skip_tests)


if __name__ == "__main__":
    sys.exit(main())

