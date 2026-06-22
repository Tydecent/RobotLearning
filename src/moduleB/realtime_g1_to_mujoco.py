"""实时把 Unitree G1 真机关节姿态同步显示到 MuJoCo。

这个脚本用于教学和截图：真机执行预置动作时，脚本只读取真机
`rt/lowstate` 里的关节角度，并把这些角度写入 MuJoCo G1 模型。

重要说明：
1. 这个脚本不控制真机，不发送 LowCmd，也不调用预置动作；
2. 真机动作仍然由 `minimal_g1_action.py` 或其他 SDK2/ROS2 脚本触发；
3. MuJoCo 只作为“可视化镜像窗口”，不是独立执行 G1 内部预置动作；
4. 如果关节名或模型版本不同，请使用 `--print-joints` 查看 MuJoCo 模型关节名。

典型使用流程：
    # 终端 1：启动镜像窗口
    python3 src/moduleB/realtime_g1_to_mujoco.py --iface eth0

    # 终端 2：让真机执行动作
    python3 src/moduleB/minimal_g1_action.py --iface eth0 --action-id 17 --release

依赖：
    pip install mujoco
    src/moduleB/setup_g1_env.sh
"""

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np

from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.core.channel import ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MJCF = ROOT_DIR / "third_party/unitree_mujoco/unitree_robots/g1/scene_29dof.xml"

# Unitree G1 29DOF LowState.motor_state 的关节顺序。
# 这个顺序来自官方 unitree_mujoco/unitree_robots/g1/g1_joint_index_dds.md。
#
# 左侧列表下标 = motor_state 下标。
# 每个下标给出一个或多个可能的 MuJoCo joint name：
# - 官方 unitree_mujoco 29DOF 通常使用 left_elbow_joint / right_elbow_joint；
# - 有些 G1 模型可能使用 left_elbow_pitch_joint 这类名字，所以这里放入别名。
G1_29DOF_JOINT_NAME_ALIASES: tuple[tuple[str, ...], ...] = (
    ("left_hip_pitch_joint",),
    ("left_hip_roll_joint",),
    ("left_hip_yaw_joint",),
    ("left_knee_joint",),
    ("left_ankle_pitch_joint",),
    ("left_ankle_roll_joint",),
    ("right_hip_pitch_joint",),
    ("right_hip_roll_joint",),
    ("right_hip_yaw_joint",),
    ("right_knee_joint",),
    ("right_ankle_pitch_joint",),
    ("right_ankle_roll_joint",),
    ("waist_yaw_joint", "torso_joint"),
    ("waist_roll_joint",),
    ("waist_pitch_joint",),
    ("left_shoulder_pitch_joint",),
    ("left_shoulder_roll_joint",),
    ("left_shoulder_yaw_joint",),
    ("left_elbow_joint", "left_elbow_pitch_joint"),
    ("left_wrist_roll_joint",),
    ("left_wrist_pitch_joint",),
    ("left_wrist_yaw_joint",),
    ("right_shoulder_pitch_joint",),
    ("right_shoulder_roll_joint",),
    ("right_shoulder_yaw_joint",),
    ("right_elbow_joint", "right_elbow_pitch_joint"),
    ("right_wrist_roll_joint",),
    ("right_wrist_pitch_joint",),
    ("right_wrist_yaw_joint",),
)


def build_parser() -> argparse.ArgumentParser:
    """解析命令行参数。

    教学重点：
    - --iface 是连接 G1 的网卡名，用于 SDK2 订阅真机 DDS 数据；
    - --mjcf 是 MuJoCo G1 场景文件；
    - --print-joints 用于排查模型关节名和脚本内置映射是否一致。
    """
    parser = argparse.ArgumentParser(description="实时把 G1 真机动作同步显示到 MuJoCo")
    parser.add_argument("--iface", required=True, help="连接 G1 的网卡名，如 eth0/enp3s0")
    parser.add_argument("--mjcf", default=str(DEFAULT_MJCF), help="MuJoCo G1 MJCF/scene XML 路径")
    parser.add_argument("--domain-id", type=int, default=0, help="Unitree DDS domain id，默认 0")
    parser.add_argument("--topic", default="rt/lowstate", help="G1 低层状态话题，默认 rt/lowstate")
    parser.add_argument("--fps", type=float, default=60.0, help="MuJoCo 窗口刷新频率，默认 60")
    parser.add_argument("--print-joints", action="store_true", help="打印 MuJoCo 模型里的关节名后退出")
    parser.add_argument("--zero-root", action="store_true", help="每帧把 floating base 根位姿重置为初始值")
    return parser


def print_mujoco_joints(model: mujoco.MjModel) -> None:
    """打印 MuJoCo 模型中所有 joint 名称，用于调试映射。"""
    print("MuJoCo 模型关节列表：")
    for joint_id in range(model.njnt):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
        joint_type = int(model.jnt_type[joint_id])
        qpos_addr = int(model.jnt_qposadr[joint_id])
        print(f"- id={joint_id:02d}, qpos={qpos_addr:02d}, type={joint_type}, name={name}")


def build_joint_qpos_mapping(model: mujoco.MjModel) -> list[tuple[int, int, str]]:
    """建立 Unitree motor_state 下标到 MuJoCo qpos 下标的映射。

    返回列表中每项含义：
    (unitree_motor_index, mujoco_qpos_index, matched_joint_name)

    MuJoCo 的 qpos 可能前面有 free joint 的 7 个根位姿自由度，因此不能假设
    qpos 下标等于关节顺序，必须通过 model.jnt_qposadr 查询。
    """
    mapping: list[tuple[int, int, str]] = []
    missing: list[tuple[int, tuple[str, ...]]] = []

    for motor_index, aliases in enumerate(G1_29DOF_JOINT_NAME_ALIASES):
        matched_name = None
        matched_joint_id = -1

        for name in aliases:
            joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
            if joint_id >= 0:
                matched_name = name
                matched_joint_id = joint_id
                break

        if matched_name is None:
            missing.append((motor_index, aliases))
            continue

        qpos_index = int(model.jnt_qposadr[matched_joint_id])
        mapping.append((motor_index, qpos_index, matched_name))

    if missing:
        print("警告：以下 Unitree 关节没有在 MuJoCo 模型中找到同名 joint，将跳过：")
        for motor_index, aliases in missing:
            print(f"- motor_state[{motor_index}] aliases={aliases}")
        print("可运行 --print-joints 查看当前 MJCF 模型的关节名。")

    print(f"已建立 {len(mapping)}/{len(G1_29DOF_JOINT_NAME_ALIASES)} 个关节映射。")
    return mapping


class G1LowStateMirror:
    """订阅 G1 LowState，并保存最新一帧 29DOF 关节角。

    Unitree SDK2 的 ChannelSubscriber 在后台收到 DDS 消息后会调用回调函数。
    MuJoCo 主循环只需要不断读取 latest_q，并写入 data.qpos。
    """

    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.lock = threading.Lock()
        self.latest_q: np.ndarray | None = None
        self.frame_count = 0

        self.subscriber = ChannelSubscriber(topic, LowState_)
        self.subscriber.Init(self._on_low_state, 10)

    def _on_low_state(self, msg: LowState_) -> None:
        """收到真机低层状态后，提取前 29 个电机的 q。"""
        q = np.array([msg.motor_state[i].q for i in range(29)], dtype=np.float64)
        with self.lock:
            self.latest_q = q
            self.frame_count += 1

    def get_latest_q(self) -> tuple[np.ndarray | None, int]:
        """返回最新关节角和帧计数。"""
        with self.lock:
            if self.latest_q is None:
                return None, self.frame_count
            return self.latest_q.copy(), self.frame_count


def main() -> None:
    args = build_parser().parse_args()
    mjcf_path = Path(args.mjcf).expanduser().resolve()

    if not mjcf_path.exists():
        raise SystemExit(
            "找不到 MuJoCo 模型文件："
            f"{mjcf_path}\n"
            "请先安装 unitree_mujoco，或用 --mjcf 指定 scene_29dof.xml。"
        )

    # 第一步：加载 MuJoCo 模型。
    # scene_29dof.xml 会引用 g1_29dof.xml 和 meshes，因此必须保持官方目录结构完整。
    model = mujoco.MjModel.from_xml_path(str(mjcf_path))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    if args.print_joints:
        print_mujoco_joints(model)
        return

    # 第二步：建立 Unitree 关节索引 -> MuJoCo qpos 的映射。
    joint_mapping = build_joint_qpos_mapping(model)
    if not joint_mapping:
        raise SystemExit("没有建立任何关节映射，无法同步。请检查 MJCF 是否为 G1 29DOF 模型。")

    # 保存初始 qpos。对于 floating base 模型，根位姿通常在 qpos[0:7]。
    initial_qpos = data.qpos.copy()

    # 第三步：初始化 Unitree SDK2 DDS 通道。
    # 这里和控制脚本一样需要指定连接真机的有线网卡。
    ChannelFactoryInitialize(args.domain_id, args.iface)

    # 第四步：订阅真机 LowState。
    # 本脚本只读状态，不会向真机发送任何控制命令。
    mirror = G1LowStateMirror(args.topic)

    print("等待 G1 LowState 数据...")
    print("提示：另开一个终端执行 minimal_g1_action.py，可以看到 MuJoCo 窗口跟随真机姿态。")

    # 第五步：启动 MuJoCo 被动 viewer。
    # launch_passive 允许 Python 主循环自己更新 data.qpos，再同步到窗口。
    frame_dt = 1.0 / max(args.fps, 1.0)
    last_print_time = 0.0
    last_frame_count = -1

    with mujoco.viewer.launch_passive(model, data) as viewer:
        while viewer.is_running():
            loop_start = time.monotonic()

            latest_q, frame_count = mirror.get_latest_q()
            if latest_q is not None:
                if args.zero_root:
                    # 可选：把根位姿固定在初始位置，避免 floating base 因模型差异显示漂移。
                    data.qpos[:] = initial_qpos

                # 把真机 29 个关节角逐个写入 MuJoCo qpos。
                # 这一步只是姿态显示，不做动力学控制。
                for motor_index, qpos_index, _joint_name in joint_mapping:
                    data.qpos[qpos_index] = latest_q[motor_index]

                mujoco.mj_forward(model, data)
                viewer.sync()

            now = time.monotonic()
            if now - last_print_time > 2.0:
                status = "已收到" if latest_q is not None else "未收到"
                changed = frame_count != last_frame_count
                print(f"LowState: {status}, frames={frame_count}, updating={changed}")
                last_print_time = now
                last_frame_count = frame_count

            sleep_time = frame_dt - (time.monotonic() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)


if __name__ == "__main__":
    main()
