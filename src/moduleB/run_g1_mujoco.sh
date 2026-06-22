#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SDK2_PREFIX="$ROOT_DIR/third_party/unitree_robotics"
MUJOCO_REPO_DIR="$ROOT_DIR/third_party/unitree_mujoco"
SIM_BUILD_DIR="$MUJOCO_REPO_DIR/simulate/build"
SIM_BIN="$SIM_BUILD_DIR/unitree_mujoco"

if [ ! -x "$SIM_BIN" ]; then
  echo "未找到 unitree_mujoco 可执行文件。请先运行：src/moduleB/setup_g1_mujoco_env.sh" >&2
  exit 1
fi

export LD_LIBRARY_PATH="$SDK2_PREFIX/lib:$MUJOCO_REPO_DIR/simulate/mujoco/lib:${LD_LIBRARY_PATH:-}"
export CMAKE_PREFIX_PATH="$SDK2_PREFIX:$SDK2_PREFIX/lib/cmake:${CMAKE_PREFIX_PATH:-}"

cd "$SIM_BUILD_DIR"

# 默认读取 ../config.yaml；也允许用参数覆盖，例如：
#   src/moduleB/run_g1_mujoco.sh -r g1 -s scene_23dof.xml -i 1 -n lo
if [ "$#" -eq 0 ]; then
  exec ./unitree_mujoco
else
  exec ./unitree_mujoco "$@"
fi
