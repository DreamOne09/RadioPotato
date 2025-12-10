"""
單一執行實例工具。

提供跨平台（Windows / POSIX）檔案鎖定確保程式同時僅有一個實例啟動。
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional


class SingleInstanceError(RuntimeError):
    """Raised when another instance is already running."""


class SingleInstance:
    """
    確保程式同時僅執行一個實例的輕量鎖。

    使用方式：
        with SingleInstance("radioone"):
            run_app()
    """

    def __init__(self, name: str = "radioone", lock_dir: Optional[Path] = None) -> None:
        base_dir = lock_dir or Path(tempfile.gettempdir())
        base_dir.mkdir(parents=True, exist_ok=True)
        self.lock_path = base_dir / f"{name}.lock"
        self._fp = None  # type: ignore[assignment]

    # --------------------------------------------------------------------- #
    # Context manager API
    # --------------------------------------------------------------------- #
    def __enter__(self) -> "SingleInstance":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()

    # --------------------------------------------------------------------- #
    # Public methods
    # --------------------------------------------------------------------- #
    def acquire(self) -> None:
        if self._fp:
            return

        self._fp = open(self.lock_path, "w")

        try:
            if os.name == "nt":
                self._acquire_windows()
            else:
                self._acquire_posix()
        except Exception:
            self._fp.close()
            self._fp = None
            raise

    def release(self) -> None:
        if not self._fp:
            return

        try:
            if os.name == "nt":
                self._release_windows()
            else:
                self._release_posix()
        finally:
            try:
                self._fp.close()
            finally:
                self._fp = None
                try:
                    self.lock_path.unlink(missing_ok=True)  # type: ignore[arg-type]
                except Exception:
                    # 鎖檔刪除失敗不應阻止程式退出
                    pass

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _acquire_windows(self) -> None:
        try:
            import msvcrt  # type: ignore
        except ImportError as exc:  # pragma: no cover - Windows only
            raise SingleInstanceError("無法載入 msvcrt 以建立檔案鎖") from exc

        try:
            msvcrt.locking(self._fp.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[arg-type]
        except OSError as exc:
            raise SingleInstanceError("偵測到另一個程式實例正在執行") from exc

    def _release_windows(self) -> None:
        import msvcrt  # type: ignore

        try:
            msvcrt.locking(self._fp.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[arg-type]
        except OSError:
            pass

    def _acquire_posix(self) -> None:
        try:
            import fcntl  # type: ignore
        except ImportError as exc:  # pragma: no cover - POSIX only
            raise SingleInstanceError("無法載入 fcntl 以建立檔案鎖") from exc

        try:
            fcntl.flock(self._fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[arg-type]
        except OSError as exc:
            raise SingleInstanceError("偵測到另一個程式實例正在執行") from exc

    def _release_posix(self) -> None:
        import fcntl  # type: ignore

        try:
            fcntl.flock(self._fp.fileno(), fcntl.LOCK_UN)  # type: ignore[arg-type]
        except OSError:
            pass


def default_lock_directory() -> Path:
    """
    取得預設鎖目錄（優先使用專案資料夾，其次為系統暫存目錄）。
    """
    if getattr(sys, "frozen", False):
        root = Path(os.path.dirname(sys.executable))
    else:
        root = Path(__file__).resolve().parents[1]

    data_dir = root / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    except OSError:
        return Path(tempfile.gettempdir())

