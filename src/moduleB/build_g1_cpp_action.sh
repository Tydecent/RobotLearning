#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SDK2_SRC_DIR="$ROOT_DIR/third_party/unitree_sdk2"
CPP_DIR="$ROOT_DIR/src/moduleB/cpp"
BUILD_DIR="$CPP_DIR/build"

echo "检查 C++ 构建工具"
command -v cmake >/dev/null
command -v g++ >/dev/null

if [ ! -d "$SDK2_SRC_DIR" ]; then
  echo "未找到 unitree_sdk2 源码目录：$SDK2_SRC_DIR" >&2
  echo "请先运行：src/moduleB/setup_g1_mujoco_env.sh" >&2
  echo "该脚本会克隆并构建 third_party/unitree_sdk2。" >&2
  exit 1
fi

if [ ! -f "$SDK2_SRC_DIR/lib/$(uname -m)/libunitree_sdk2.a" ]; then
  echo "未找到 SDK2 官方静态库：$SDK2_SRC_DIR/lib/$(uname -m)/libunitree_sdk2.a" >&2
  echo "请重新运行：src/moduleB/setup_g1_mujoco_env.sh" >&2
  exit 1
fi

echo "使用 unitree_sdk2 源码树：$SDK2_SRC_DIR"
cmake -S "$CPP_DIR" -B "$BUILD_DIR" \
  -DCMAKE_BUILD_TYPE=Release \
  -DUNITREE_SDK2_SOURCE_DIR="$SDK2_SRC_DIR"

cmake --build "$BUILD_DIR" -j"$(nproc)"

echo
echo "C++ G1 动作程序构建完成：$BUILD_DIR/minimal_g1_action"
echo "示例：$BUILD_DIR/minimal_g1_action --network eth0 --action-id 17"
