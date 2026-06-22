"""最简 Unitree G1 ROS2 预置动作控制脚本。

这个脚本用于教学：使用 ROS2 话题直接向 Unitree 高层 API 发送请求，
不使用 unitree_sdk2_python 的 Client 类。

运行前请先完成：
1. G1 Edu 上电，并按赛场/官方流程进入可运动状态；
2. 控制电脑通过网线连接 G1；
3. 安装并 source Unitree ROS2 环境，使 Python 能导入 unitree_api；
4. 根据现场网络配置好 CycloneDDS / ROS_DOMAIN_ID。

示例：
    python3 src/moduleB/minimal_g1_ros2_action.py
    python3 src/moduleB/minimal_g1_ros2_action.py --action-id 20 --release
    python3 src/moduleB/minimal_g1_ros2_action.py --domain-id 0 --action-id 17

常见动作 ID：
    17 = clap / 鼓掌
    20 = heart / 双手比心
    25 = face wave / 胸前挥手
    26 = high wave / 头顶挥手
    27 = shake hand / 握手
    99 = release arm / 释放手臂姿态

关键 ROS2 话题：
    /api/sport/request   发送运动状态请求，例如 Start()
    /api/sport/response  接收运动状态响应
    /api/arm/request     发送手臂预置动作请求
    /api/arm/response    接收手臂预置动作响应
"""

from __future__ import annotations

import argparse
import json
import os
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from unitree_api.msg import Request
from unitree_api.msg import Response


# G1 LocoClient.Start() 的 ROS2 本质：
# 向 /api/sport/request 发送 api_id=7101，参数 {"data": 500}。
# 500 是 G1 高层运动系统的一个 FSM ID，常用于进入可执行高层动作的状态。
ROBOT_API_ID_LOCO_SET_FSM_ID = 7101
G1_FSM_ID_START = 500

# G1ArmActionClient.ExecuteAction(id) 的 ROS2 本质：
# 向 /api/arm/request 发送 api_id=7106，参数 {"data": 动作ID}。
ROBOT_API_ID_ARM_ACTION_EXECUTE_ACTION = 7106

# 官方动作表中，99 表示 release arm，用于释放手臂保持姿态。
ARM_ACTION_RELEASE = 99


def build_parser() -> argparse.ArgumentParser:
    """解析命令行参数。

    教学重点：
    - ROS2 版通常不在脚本里指定网卡名，而是依赖 CycloneDDS/ROS2 环境配置。
    - --domain-id 会写入 ROS_DOMAIN_ID，必须在 rclpy.init() 之前设置。
    - --action-id 默认 17，也就是鼓掌，便于快速测试。
    """
    parser = argparse.ArgumentParser(description="最简 Unitree G1 ROS2 预置动作控制")
    parser.add_argument("--domain-id", type=int, default=0, help="ROS_DOMAIN_ID，默认 0")
    parser.add_argument("--action-id", type=int, default=17, help="预置动作 ID，默认 17=clap")
    parser.add_argument("--release", action="store_true", help="动作后执行 99=release arm")
    parser.add_argument("--no-start", action="store_true", help="不先发送 FSM 500 Start 请求")
    parser.add_argument("--timeout", type=float, default=5.0, help="等待响应超时时间，默认 5 秒")
    parser.add_argument("--yes", action="store_true", help="跳过安全确认")
    return parser


def confirm_safety(skip_confirm: bool) -> None:
    """真实机器人运动前的安全确认。"""
    if skip_confirm:
        return

    print("安全确认：请清空 G1 周围障碍物，确认移动吊架/急停可用。")
    print("ROS2 版会直接向 G1 高层 API 发送动作请求。")
    answer = input("输入 YES 继续执行：")
    if answer != "YES":
        raise SystemExit("已取消执行。")


class UnitreeRos2ApiClient(Node):
    """一个极简版 Unitree ROS2 API 客户端。

    Unitree ROS2 高层控制不是标准 ROS service，而是 request/response 两组话题。
    官方 C++ 示例里的 BaseClient 也是做同样的事情：
    1. 发布 unitree_api/msg/Request；
    2. 给 Request 写入唯一 identity.id；
    3. 订阅 Response；
    4. 等待 identity.id 相同的响应返回。
    """

    def __init__(self) -> None:
        super().__init__("minimal_g1_ros2_action")

        # QoS depth=1 与官方 C++ 示例保持一致。
        qos = QoSProfile(depth=1)

        # sport 通道：对应 G1 的运动状态、FSM、移动等能力。
        self.sport_request_pub = self.create_publisher(Request, "/api/sport/request", qos)
        self.create_subscription(Response, "/api/sport/response", self._on_response, qos)

        # arm 通道：对应 G1 的手臂/上半身预置动作。
        self.arm_request_pub = self.create_publisher(Request, "/api/arm/request", qos)
        self.create_subscription(Response, "/api/arm/response", self._on_response, qos)

        # 用字典保存已经收到的响应，key 是 request.header.identity.id。
        self.responses: dict[int, Response] = {}

    def _on_response(self, response: Response) -> None:
        """收到响应后，按 identity.id 记录起来，等待 call_api() 取走。"""
        self.responses[response.header.identity.id] = response

    def call_api(
        self,
        publisher: rclpy.publisher.Publisher,
        api_id: int,
        data: int,
        timeout: float,
    ) -> int:
        """发送一个 Unitree API 请求，并等待对应响应。

        参数说明：
        - publisher：决定请求发到 sport 还是 arm 通道；
        - api_id：Unitree API 编号，例如 7101 或 7106；
        - data：请求参数，Unitree 高层 API 常用 {"data": 数值}；
        - timeout：最多等待多少秒。
        """
        request = Request()

        # identity.id 用来区分每一次请求。
        # 这里用 monotonic_ns 生成一个递增的纳秒时间戳，足够教学和单线程使用。
        request.header.identity.id = time.monotonic_ns()
        request.header.identity.api_id = api_id

        # parameter 是 JSON 字符串。官方 C++ 示例使用 nlohmann::json 生成同样内容。
        request.parameter = json.dumps({"data": data})

        publisher.publish(request)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
            response = self.responses.pop(request.header.identity.id, None)
            if response is None:
                continue

            # Unitree API 把返回码放在 response.header.status.code。
            # 0 通常表示成功，非 0 表示失败或状态不允许。
            return int(response.header.status.code)

        raise TimeoutError(f"等待 api_id={api_id} 的响应超时")

    def start(self, timeout: float) -> int:
        """发送 Loco Start 请求，让 G1 进入 FSM 500。"""
        return self.call_api(
            self.sport_request_pub,
            ROBOT_API_ID_LOCO_SET_FSM_ID,
            G1_FSM_ID_START,
            timeout,
        )

    def execute_arm_action(self, action_id: int, timeout: float) -> int:
        """发送手臂预置动作请求，例如 17=clap。"""
        return self.call_api(
            self.arm_request_pub,
            ROBOT_API_ID_ARM_ACTION_EXECUTE_ACTION,
            action_id,
            timeout,
        )


def main() -> None:
    args = build_parser().parse_args()

    # ROS_DOMAIN_ID 必须在 rclpy.init() 之前设置。
    # 如果赛场或官方环境已经设置好，也可以保持默认值一致。
    os.environ["ROS_DOMAIN_ID"] = str(args.domain_id)

    # 第一步：安全确认。
    confirm_safety(args.yes)

    # 第二步：初始化 ROS2。
    # 这里没有 --iface 参数；ROS2 使用哪块网卡通常由 CycloneDDS 配置决定。
    rclpy.init()
    node = UnitreeRos2ApiClient()

    try:
        if not args.no_start:
            # 第三步：先发送 Start 请求。
            # 这对应 SDK2 版里的 LocoClient.Start()。
            print(f"ROS2 /api/sport/request api_id={ROBOT_API_ID_LOCO_SET_FSM_ID}, data={G1_FSM_ID_START}")
            print("return code:", node.start(args.timeout))
            time.sleep(0.5)

        # 第四步：执行指定手臂预置动作。
        # 默认 action_id=17，也就是 clap / 鼓掌。
        print(f"ROS2 /api/arm/request api_id={ROBOT_API_ID_ARM_ACTION_EXECUTE_ACTION}, data={args.action_id}")
        print("return code:", node.execute_arm_action(args.action_id, args.timeout))

        if args.release:
            # 第五步：按需释放手臂。
            time.sleep(2.0)
            print(f"ROS2 /api/arm/request api_id={ROBOT_API_ID_ARM_ACTION_EXECUTE_ACTION}, data={ARM_ACTION_RELEASE}")
            print("return code:", node.execute_arm_action(ARM_ACTION_RELEASE, args.timeout))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
