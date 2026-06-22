#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SDK2_PREFIX="$ROOT_DIR/third_party/unitree_robotics"
MUJOCO_REPO_DIR="$ROOT_DIR/third_party/unitree_mujoco"
SIM_BIN="$MUJOCO_REPO_DIR/simulate/build/unitree_mujoco"
CONFIG="$MUJOCO_REPO_DIR/simulate/config.yaml"

echo "检查 G1 MuJoCo 环境"

check_path() {
  local label="$1"
  local path="$2"
  if [ -e "$path" ]; then
    echo "[OK] $label: $path"
  else
    echo "[缺失] $label: $path"
  fi
}

check_path "unitree_sdk2 本地安装目录" "$SDK2_PREFIX"
check_path "unitree_mujoco 仓库" "$MUJOCO_REPO_DIR"
check_path "MuJoCo 软链接" "$MUJOCO_REPO_DIR/simulate/mujoco"
check_path "模拟器可执行文件" "$SIM_BIN"
check_path "模拟器配置文件" "$CONFIG"

if [ -f "$CONFIG" ]; then
  echo
  echo "当前 config.yaml 关键配置："
  sed -n '1,20p' "$CONFIG"
fi

echo
echo "期望配置：robot=g1, robot_scene=scene_29dof.xml, domain_id=1, interface=lo"
