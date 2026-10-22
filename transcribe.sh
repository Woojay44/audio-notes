#!/usr/bin/env bash
# 在 WSL 里运行转写；从 Windows 调用：wsl -e bash /mnt/<盘符>/<项目路径>/transcribe.sh <音频或目录>
set -e
VENV="$HOME/.venvs/audio-notes"
SITE=$("$VENV/bin/python" -c 'import site; print(site.getsitepackages()[0])')
# 让 ctranslate2 找到 pip 装的 cuBLAS / cuDNN
export LD_LIBRARY_PATH="$SITE/nvidia/cublas/lib:$SITE/nvidia/cudnn/lib:$LD_LIBRARY_PATH"
exec "$VENV/bin/python" "$(dirname "$0")/transcribe.py" "$@"
