#!/usr/bin/env bash
# RadioPotato Git pre-push helper for Unix-like environments.
#
# Usage: ./tools/prepush.sh [--skip-tests] [--skip-build]
# 可於 .git/hooks/pre-push 內引用：
#   #!/usr/bin/env bash
#   exec ./tools/prepush.sh "$@"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

SKIP_TESTS=0
SKIP_BUILD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-tests)
      SKIP_TESTS=1
      shift
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

python_cmd="${PYTHON:-python3}"
if ! command -v "${python_cmd}" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    python_cmd=python
  else
    echo "找不到 Python，請設定 PYTHON 環境變數或安裝 Python。" >&2
    exit 1
  fi
fi

diag_args=(tools/run_diagnostics.py)
if [[ ${SKIP_TESTS} -eq 1 ]]; then
  diag_args+=("--skip-tests")
fi

echo "==> Running diagnostics using ${python_cmd}"
if ! "${python_cmd}" "${diag_args[@]}"; then
  echo "診斷失敗，停止 pre-push 流程。" >&2
  exit 1
fi

if [[ ${SKIP_BUILD} -eq 1 ]]; then
  echo "==> 跳過 PyInstaller 打包"
  exit 0
fi

echo "==> Running PyInstaller build"
if command -v pyinstaller >/dev/null 2>&1; then
  pyinstaller build.spec
else
  "${python_cmd}" -m PyInstaller build.spec
fi

echo "==> Pre-push checks passed."

