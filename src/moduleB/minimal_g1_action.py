"""最简 Unitree G1 真机预置动作控制脚本。

这个脚本用于教学：只保留“连接 G1 -> 进入可执行状态 -> 执行动作”
这条主线，不做 OCR、不做中文动作解析，也不封装复杂动作表。

运行前请先完成：
1. G1 Edu 上电，并按赛场/官方流程进入可运动状态；
2. 控制电脑通过网线连接 G1；
3. 安装 Unitree Python SDK：src/moduleB/setup_g1_env.sh；
4. 用 `ip link` 找到连接 G1 的网卡名，例如 eth0 或 enp3s0。

示例：
    python3 src/moduleB/minimal_g1_action.py --iface eth0
    python3 src/moduleB/minimal_g1_action.py --iface eth0 --action-id 20 --release

常见动作 ID：
    17 = clap / 鼓掌
    20 = heart / 双手比心
    25 = face wave / 胸前挥手
    26 = high wave / 头顶挥手
    27 = shake hand / 握手
    99 = release arm / 释放手臂姿态
"""

from __future__ import annotations

import argparse
import time

# ChannelFactoryInitialize 用来初始化 Unitree SDK2 的 DDS 通信通道。
# 它需要知道使用哪块网卡和 G1 通信，所以运行时必须传入 --iface。
from unitree_sdk2py.core.channel import ChannelFactoryInitialize

# G1ArmActionClient 是“手臂/上半身预置动作”的客户端。
# ExecuteAction(17) 这类调用只是发请求，真正动作由 G1 真机内部服务执行。
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient

# LocoClient 是“运动/状态切换”的客户端。
# 这里主要用 Start() 让机器人进入更适合执行高层动作的状态。
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient


def build_parser() -> argparse.ArgumentParser:
    """解析命令行参数。

    教学重点：
    - --iface 是必填项，因为 SDK2 必须绑定到连接 G1 的有线网卡。
    - --action-id 默认 17，也就是鼓掌，便于一条命令快速测试。
    - --release 会在动作结束后执行 99，避免部分动作让手臂停在保持姿态。
    """
    parser = argparse.ArgumentParser(description="最简 Unitree G1 预置动作控制")
    parser.add_argument("--iface", required=True, help="连接 G1 的网卡名，如 eth0/enp3s0")
    parser.add_argument("--action-id", type=int, default=17, help="预置动作 ID，默认 17=clap")
    parser.add_argument("--release", action="store_true", help="动作后执行 99=release arm")
    parser.add_argument("--no-start", action="store_true", help="不先调用 LocoClient.Start()")
    parser.add_argument("--yes", action="store_true", help="跳过安全确认")
    return parser


def confirm_safety(skip_confirm: bool) -> None:
    """真实机器人运动前的安全确认。

    预置动作虽然由 G1 内部服务执行，但机器人仍会真实运动。
    教学或比赛训练时建议保留这个确认，避免误执行。
    """
    if skip_confirm:
        return

    print("安全确认：请清空 G1 周围障碍物，确认移动吊架/急停可用。")
    answer = input("输入 YES 继续执行：")
    if answer != "YES":
        raise SystemExit("已取消执行。")


def main() -> None:
    args = build_parser().parse_args()

    # 第一步：安全确认。
    # 如果没有传 --yes，脚本会等待手动输入 YES。
    confirm_safety(args.yes)

    # 第二步：初始化 SDK2 通信。
    # 第一个参数 0 是 DDS domain id；通常保持 0。
    # 第二个参数是连接 G1 的网卡名，例如 eth0/enp3s0。
    # 如果网卡名填错，后续 RPC 调用通常会超时或没有响应。
    ChannelFactoryInitialize(0, args.iface)

    # 第三步：创建并初始化 LocoClient。
    # LocoClient 负责运动模式、站立、移动、坐下等高层运动能力。
    # 这里用它调用 Start()，让机器人进入可执行动作的状态。
    loco_client = LocoClient()

    # SetTimeout 表示一次 RPC 调用最多等待多少秒。
    # 预置动作通常不会太长，教学脚本里设为 10 秒比较直观。
    loco_client.SetTimeout(10.0)

    # Init 会向 SDK2 注册该 client 支持的 API。
    # 未 Init 就调用 Start()，通常不会得到正确结果。
    loco_client.Init()

    # 第四步：创建并初始化 G1ArmActionClient。
    # 这个 client 专门负责 G1 手臂/上半身预置动作。
    arm_client = G1ArmActionClient()
    arm_client.SetTimeout(10.0)
    arm_client.Init()

    if not args.no_start:
        # 第五步：先调用 Start()。
        # 很多预置动作要求 G1 处于指定 FSM 状态。
        # 如果状态不对，可能返回 INVALID_FSM_ID 或动作不执行。
        print("LocoClient.Start()")
        print("return code:", loco_client.Start())

        # 给机器人内部状态切换一点时间，再发送手臂动作请求。
        time.sleep(0.5)

    # 第六步：执行指定预置动作。
    # 默认 action_id=17，也就是 clap / 鼓掌。
    # 这里传给 ExecuteAction 的只是动作编号，不是关节角度或轨迹。
    print(f"G1ArmActionClient.ExecuteAction({args.action_id})")
    print("return code:", arm_client.ExecuteAction(args.action_id))

    if args.release:
        # 第七步：按需释放手臂姿态。
        # 有些动作会在最后一帧保持姿态，例如比心、拥抱、举手。
        # 99 是官方动作表中的 release arm，用于让手臂退出保持动作。
        time.sleep(2.0)
        print("G1ArmActionClient.ExecuteAction(99)  # release arm")
        print("return code:", arm_client.ExecuteAction(99))


if __name__ == "__main__":
    main()
