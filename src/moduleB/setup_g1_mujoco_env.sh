#!/usr/bin/env bash
set -euo pipefail

MUJOCO_VERSION="${MUJOCO_VERSION:-3.3.6}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
THIRD_PARTY_DIR="$ROOT_DIR/third_party"
SDK2_SRC_DIR="$THIRD_PARTY_DIR/unitree_sdk2"
SDK2_PREFIX="$THIRD_PARTY_DIR/unitree_robotics"
MUJOCO_REPO_DIR="$THIRD_PARTY_DIR/unitree_mujoco"
MUJOCO_HOME="${MUJOCO_HOME:-$HOME/.mujoco}"
MUJOCO_DIR="$MUJOCO_HOME/mujoco-$MUJOCO_VERSION"
MUJOCO_ARCHIVE="mujoco-${MUJOCO_VERSION}-linux-x86_64.tar.gz"
MUJOCO_URL="https://github.com/google-deepmind/mujoco/releases/download/${MUJOCO_VERSION}/${MUJOCO_ARCHIVE}"

echo "[1/7] 检查基础工具"
command -v git >/dev/null
command -v cmake >/dev/null
command -v g++ >/dev/null

if [ "${SKIP_APT:-0}" != "1" ]; then
  echo "[2/7] 安装系统依赖"
  sudo apt update
  sudo apt install -y \
    build-essential cmake git curl tar \
    libyaml-cpp-dev libspdlog-dev libboost-all-dev libglfw3-dev
else
  echo "[2/7] 跳过 apt 依赖安装（SKIP_APT=1）"
fi

mkdir -p "$THIRD_PARTY_DIR" "$MUJOCO_HOME"

echo "[3/7] 准备 unitree_sdk2"
if [ ! -d "$SDK2_SRC_DIR/.git" ]; then
  git clone https://github.com/unitreerobotics/unitree_sdk2.git "$SDK2_SRC_DIR"
else
  git -C "$SDK2_SRC_DIR" pull --ff-only
fi

echo "[4/7] 本地安装 unitree_sdk2 -> $SDK2_PREFIX"
cmake -S "$SDK2_SRC_DIR" -B "$SDK2_SRC_DIR/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$SDK2_PREFIX"
cmake --build "$SDK2_SRC_DIR/build" -j"$(nproc)"
cmake --install "$SDK2_SRC_DIR/build"

echo "[5/7] 准备 MuJoCo $MUJOCO_VERSION"
if [ ! -d "$MUJOCO_DIR" ]; then
  TMP_ARCHIVE="/tmp/$MUJOCO_ARCHIVE"
  curl -L "$MUJOCO_URL" -o "$TMP_ARCHIVE"
  tar -xzf "$TMP_ARCHIVE" -C "$MUJOCO_HOME"
fi

echo "[6/7] 准备 unitree_mujoco"
if [ ! -d "$MUJOCO_REPO_DIR/.git" ]; then
  git clone https://github.com/unitreerobotics/unitree_mujoco.git "$MUJOCO_REPO_DIR"
else
  git -C "$MUJOCO_REPO_DIR" pull --ff-only
fi

ln -sfn "$MUJOCO_DIR" "$MUJOCO_REPO_DIR/simulate/mujoco"

cat > "$MUJOCO_REPO_DIR/simulate/config.yaml" <<'YAML'
robot: "g1"
robot_scene: "scene_29dof.xml"

domain_id: 1
interface: "lo"

use_joystick: 0
joystick_type: "xbox"
joystick_device: "/dev/input/js0"
joystick_bits: 16

print_scene_information: 1

enable_elastic_band: 1
YAML

echo "[7/7] 编译 unitree_mujoco C++ 模拟器"
cmake -S "$MUJOCO_REPO_DIR/simulate" -B "$MUJOCO_REPO_DIR/simulate/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH="$SDK2_PREFIX;$SDK2_PREFIX/lib/cmake"
cmake --build "$MUJOCO_REPO_DIR/simulate/build" -j"$(nproc)"

echo
echo "G1 MuJoCo 环境准备完成。"
echo "启动仿真：src/moduleB/run_g1_mujoco.sh"
echo "配置文件：$MUJOCO_REPO_DIR/simulate/config.yaml"
