"""Unitree G1 模块 B 预置动作接口。

本脚本面向《人工智能训练师》模块 B 训练：
1. 从中文/英文操作说明中解析动作名称；
2. 本地 dry-run 演练动作序列；
3. 安装 unitree_sdk2_python 并连接 G1 后调用高层预置动作接口。

示例：
    python3 src/moduleB/g1_action_interface.py --list
    python3 src/moduleB/g1_action_interface.py --dry-run --actions "站立,鼓掌,释放手臂"
    python3 src/moduleB/g1_action_interface.py --dry-run --instruction-file src/moduleB/samples/operation_instruction.txt
    python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "start,clap,release arm"
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class ActionSpec:
    key: str
    kind: str
    description: str
    aliases: tuple[str, ...]
    arm_id: int | None = None
    auto_release: bool = False
    duration: float = 1.0
    vx: float = 0.0
    vy: float = 0.0
    vyaw: float = 0.0


ARM_ACTIONS: tuple[ActionSpec, ...] = (
    ActionSpec("release_arm", "arm", "释放手臂姿态", ("release arm", "释放手臂", "释放", "松开手臂"), 99),
    ActionSpec("two_hand_kiss", "arm", "双手飞吻", ("two-hand kiss", "双手飞吻", "飞吻"), 11),
    ActionSpec("left_kiss", "arm", "左手飞吻", ("left kiss", "左手飞吻"), 12),
    ActionSpec("right_kiss", "arm", "右手飞吻", ("right kiss", "右手飞吻"), 13),
    ActionSpec("hands_up", "arm", "双手举起", ("hands up", "举手", "双手举起", "双手举高"), 15, True),
    ActionSpec("clap", "arm", "鼓掌", ("clap", "鼓掌", "拍手"), 17),
    ActionSpec("high_five", "arm", "击掌", ("high five", "击掌", "举手击掌"), 18, True),
    ActionSpec("hug", "arm", "拥抱", ("hug", "拥抱", "抱抱"), 19, True),
    ActionSpec("heart", "arm", "双手比心", ("heart", "比心", "双手比心", "爱心"), 20, True),
    ActionSpec("right_heart", "arm", "右手比心", ("right heart", "右手比心"), 21, True),
    ActionSpec("reject", "arm", "拒绝/叉手", ("reject", "拒绝", "叉手", "不可以"), 22, True),
    ActionSpec("right_hand_up", "arm", "右手举起", ("right hand up", "右手举起", "右手举高"), 23, True),
    ActionSpec("x_ray", "arm", "射线/奥特曼手势", ("x-ray", "xray", "射线", "奥特曼"), 24, True),
    ActionSpec("face_wave", "arm", "胸前挥手", ("face wave", "胸前挥手", "挥手"), 25),
    ActionSpec("high_wave", "arm", "头顶挥手", ("high wave", "头顶挥手", "高位挥手"), 26),
    ActionSpec("shake_hand", "arm", "握手", ("shake hand", "握手"), 27, True),
)

LOCO_ACTIONS: tuple[ActionSpec, ...] = (
    ActionSpec("start", "loco", "启动高层运动 FSM 500", ("start", "启动", "开始", "站立", "站立准备", "进入运动模式", "可执行动作状态")),
    ActionSpec("sit", "loco", "坐下", ("sit", "坐下")),
    ActionSpec("damp", "loco", "阻尼模式", ("damp", "阻尼")),
    ActionSpec("zero_torque", "loco", "零力矩", ("zero torque", "零力矩")),
    ActionSpec("squat_to_stand", "loco", "蹲姿站起", ("Squat2StandUp", "蹲姿站起", "蹲下站起")),
    ActionSpec("lie_to_stand", "loco", "躺姿站起", ("Lie2StandUp", "躺姿站起")),
    ActionSpec("high_stand", "loco", "高站姿", ("high stand", "高站姿", "高站")),
    ActionSpec("low_stand", "loco", "低站姿", ("low stand", "低站姿", "低站")),
    ActionSpec("wave_hand_loco", "loco", "Loco 挥手", ("loco wave", "运动挥手", "转身前挥手")),
    ActionSpec("wave_hand_turn", "loco", "Loco 转身挥手", ("turn wave", "转身挥手")),
    ActionSpec("shake_hand_loco", "loco", "Loco 分阶段握手", ("loco shake hand", "运动握手")),
    ActionSpec("move_forward", "move", "前进 1 秒", ("move forward", "前进", "向前"), vx=0.3),
    ActionSpec("move_backward", "move", "后退 1 秒", ("move backward", "后退", "向后"), vx=-0.3),
    ActionSpec("move_left", "move", "左移 1 秒", ("move left", "左移", "向左"), vy=0.3),
    ActionSpec("move_right", "move", "右移 1 秒", ("move right", "右移", "向右"), vy=-0.3),
    ActionSpec("turn_left", "move", "左转 1 秒", ("turn left", "左转"), vyaw=0.3),
    ActionSpec("turn_right", "move", "右转 1 秒", ("turn right", "右转"), vyaw=-0.3),
    ActionSpec("stop_move", "loco", "停止移动", ("stop", "stop move", "停止", "停止移动")),
)

ACTION_SPECS: tuple[ActionSpec, ...] = ARM_ACTIONS + LOCO_ACTIONS
ACTION_BY_KEY = {action.key: action for action in ACTION_SPECS}
RELEASE_ARM = ACTION_BY_KEY["release_arm"]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def split_actions(raw_actions: str) -> list[str]:
    parts = re.split(r"[,，;；、\n]+", raw_actions)
    return [part.strip() for part in parts if part.strip()]


def parse_instruction_text(text: str) -> list[ActionSpec]:
    """按动作别名在说明文本中出现的先后顺序生成动作序列。"""
    normalized = normalize_text(text)
    matches: list[tuple[int, int, ActionSpec]] = []

    for index, action in enumerate(ACTION_SPECS):
        for alias in action.aliases:
            position = normalized.find(normalize_text(alias))
            if position >= 0:
                matches.append((position, index, action))
                break

    matches.sort(key=lambda item: (item[0], item[1]))
    return [action for _, _, action in matches]


def resolve_action(name: str) -> ActionSpec:
    normalized_name = normalize_text(name)

    if normalized_name in ACTION_BY_KEY:
        return ACTION_BY_KEY[normalized_name]

    for action in ACTION_SPECS:
        if normalized_name in {normalize_text(alias) for alias in action.aliases}:
            return action

    raise ValueError(f"未识别动作：{name}")


class DryRunG1Client:
    def start(self) -> None:
        print("[dry-run] Loco.Start() -> FSM 500")

    def run(self, action: ActionSpec) -> None:
        if action.kind == "arm":
            print(f"[dry-run] G1ArmActionClient.ExecuteAction({action.arm_id})  # {action.description}")
        elif action.kind == "move":
            print(
                "[dry-run] LocoClient.Move("
                f"vx={action.vx}, vy={action.vy}, vyaw={action.vyaw}, duration={action.duration})"
            )
        else:
            print(f"[dry-run] LocoClient.{to_loco_method_name(action.key)}()  # {action.description}")


class UnitreeG1Client:
    def __init__(self, iface: str, timeout: float = 10.0) -> None:
        try:
            from unitree_sdk2py.core.channel import ChannelFactoryInitialize
            from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient
            from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient
        except ImportError as exc:
            raise SystemExit(
                "未安装 unitree_sdk2_python。请先执行 src/moduleB/setup_g1_env.sh，"
                "或使用 --dry-run 进行本地演练。"
            ) from exc

        ChannelFactoryInitialize(0, iface)

        self.arm_client = G1ArmActionClient()
        self.arm_client.SetTimeout(timeout)
        self.arm_client.Init()

        self.loco_client = LocoClient()
        self.loco_client.SetTimeout(timeout)
        self.loco_client.Init()

    def start(self) -> None:
        print("Loco.Start() -> FSM 500")
        self.loco_client.Start()

    def run(self, action: ActionSpec) -> None:
        if action.kind == "arm":
            code = self.arm_client.ExecuteAction(action.arm_id)
            print(f"G1ArmActionClient.ExecuteAction({action.arm_id}) -> code={code}")
        elif action.kind == "move":
            code = self.loco_client.Move(action.vx, action.vy, action.vyaw)
            print(f"LocoClient.Move({action.vx}, {action.vy}, {action.vyaw}) -> code={code}")
        else:
            call_loco_action(self.loco_client, action.key)
            print(f"LocoClient.{to_loco_method_name(action.key)}()")


def to_loco_method_name(action_key: str) -> str:
    names = {
        "start": "Start",
        "sit": "Sit",
        "damp": "Damp",
        "zero_torque": "ZeroTorque",
        "squat_to_stand": "Squat2StandUp",
        "lie_to_stand": "Lie2StandUp",
        "high_stand": "HighStand",
        "low_stand": "LowStand",
        "wave_hand_loco": "WaveHand",
        "wave_hand_turn": "WaveHand(True)",
        "shake_hand_loco": "ShakeHand",
        "stop_move": "StopMove",
    }
    return names[action_key]


def call_loco_action(loco_client: object, action_key: str) -> None:
    calls: dict[str, Callable[[], object]] = {
        "start": loco_client.Start,
        "sit": loco_client.Sit,
        "damp": loco_client.Damp,
        "zero_torque": loco_client.ZeroTorque,
        "squat_to_stand": loco_client.Squat2StandUp,
        "lie_to_stand": loco_client.Lie2StandUp,
        "high_stand": loco_client.HighStand,
        "low_stand": loco_client.LowStand,
        "wave_hand_loco": loco_client.WaveHand,
        "wave_hand_turn": lambda: loco_client.WaveHand(True),
        "shake_hand_loco": loco_client.ShakeHand,
        "stop_move": loco_client.StopMove,
    }
    calls[action_key]()


def load_actions(args: argparse.Namespace) -> list[ActionSpec]:
    if args.instruction_file:
        text = Path(args.instruction_file).read_text(encoding="utf-8")
        actions = parse_instruction_text(text)
    elif args.actions:
        actions = [resolve_action(name) for name in split_actions(args.actions)]
    else:
        actions = []

    if not actions:
        raise SystemExit("未解析到动作。请使用 --actions 或 --instruction-file，或用 --list 查看动作名。")

    if args.auto_release:
        expanded: list[ActionSpec] = []
        for index, action in enumerate(actions):
            expanded.append(action)
            next_action = actions[index + 1] if index + 1 < len(actions) else None
            if action.auto_release and action.key != RELEASE_ARM.key and next_action != RELEASE_ARM:
                expanded.append(RELEASE_ARM)
        return expanded

    return actions


def print_action_table(actions: Iterable[ActionSpec] = ACTION_SPECS) -> None:
    print("可用动作：")
    for action in actions:
        if action.kind == "arm":
            call = f"arm id={action.arm_id}"
        elif action.kind == "move":
            call = f"move vx={action.vx}, vy={action.vy}, vyaw={action.vyaw}"
        else:
            call = f"loco {to_loco_method_name(action.key)}"
        aliases = " / ".join(action.aliases)
        print(f"- {action.key:16s} [{call:28s}] {action.description}；别名：{aliases}")


def confirm_safety(skip_confirm: bool) -> None:
    if skip_confirm:
        return
    print("安全确认：执行前请清空机器人周围障碍物，确认 G1 Edu 已挂载移动吊架并可急停。")
    answer = input("输入 YES 继续执行：")
    if answer != "YES":
        raise SystemExit("已取消执行。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unitree G1 模块 B 预置动作执行接口")
    parser.add_argument("--list", action="store_true", help="列出支持的动作映射")
    parser.add_argument("--actions", help="动作序列，使用逗号/顿号/分号分隔，如：站立,鼓掌,释放手臂")
    parser.add_argument("--instruction-file", help="操作说明文本文件；脚本会按出现顺序解析动作")
    parser.add_argument("--dry-run", action="store_true", help="本地仿真演练，不连接机器人")
    parser.add_argument("--iface", help="连接 G1 的网卡名，如 eth0/enp3s0；非 dry-run 模式必填")
    parser.add_argument("--timeout", type=float, default=10.0, help="Unitree RPC 超时时间，默认 10 秒")
    parser.add_argument("--no-start", action="store_true", help="不自动调用 LocoClient.Start()")
    parser.add_argument("--auto-release", action="store_true", help="对需释放的手臂动作自动追加 release arm")
    parser.add_argument("--yes", action="store_true", help="跳过安全确认输入")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.list:
        print_action_table()
        return

    actions = load_actions(args)

    if args.dry_run:
        client: DryRunG1Client | UnitreeG1Client = DryRunG1Client()
    else:
        if not args.iface:
            raise SystemExit("真实执行需要指定 --iface，例如：--iface eth0。仅演练请加 --dry-run。")
        confirm_safety(args.yes)
        client = UnitreeG1Client(args.iface, timeout=args.timeout)

    if not args.no_start and actions[0].key != "start":
        client.start()
        time.sleep(0.5)

    for action in actions:
        client.run(action)
        time.sleep(action.duration)


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)
