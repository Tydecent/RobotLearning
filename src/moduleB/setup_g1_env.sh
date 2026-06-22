#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODULE_DIR="$ROOT_DIR/src/moduleB"
THIRD_PARTY_DIR="$ROOT_DIR/third_party"
SDK_DIR="$THIRD_PARTY_DIR/unitree_sdk2_python"

echo "[1/4] 检查 Python 环境"
python3 --version
python3 -m pip --version >/dev/null

echo "[2/4] 安装模块 B Python 依赖"
python3 -m pip install --user -r "$MODULE_DIR/requirements.txt"

echo "[3/4] 准备 unitree_sdk2_python"
mkdir -p "$THIRD_PARTY_DIR"
if [ ! -d "$SDK_DIR/.git" ]; then
  git clone https://github.com/unitreerobotics/unitree_sdk2_python.git "$SDK_DIR"
else
  git -C "$SDK_DIR" pull --ff-only
fi

echo "[4/4] 安装 Unitree Python SDK"
python3 -m pip install --user "$SDK_DIR"

echo
echo "模块 B 环境准备完成。"
echo "本地演练：python3 src/moduleB/g1_action_interface.py --dry-run --actions \"站立,鼓掌,释放手臂\""
echo "连接 G1： python3 src/moduleB/g1_action_interface.py --iface <网卡名> --actions \"start,clap,release arm\""
