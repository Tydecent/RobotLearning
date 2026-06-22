# 模块 B：Unitree G1 高层预置动作机制教学文档

本文面向《人工智能训练师》模块 B 训练，解释 Unitree G1 高层预置动作、SDK2、`unitree_ros2` 与真机执行流程。

---

## 1. 一句话理解

G1 的高层预置动作不是 ROS action，也不是直接给每个电机发关节角度，而是通过 Unitree SDK2 调用机器人内部已经封装好的动作服务。

可以这样理解：

```text
高层动作接口 = 向机器人内部服务下达“执行某个动作”的命令
用户程序 = 解析动作名称，调用 SDK2 客户端发送请求
G1 真机 = 接收请求，由内部服务完成动作执行
```

---

## 2. 什么是高层预置动作

“高层预置动作”指机器人固件或运控服务里已经做好的标准动作。

例如：

```python
arm_client.ExecuteAction(17)
```

这行代码的意思不是“手动控制左右手每个关节完成鼓掌”，而是：

```text
告诉 G1 内部动作服务：请执行 ID=17 的动作
```

在官方动作映射里，`17` 对应 `clap`，也就是鼓掌。

常见动作示例：

| ID | 英文名 | 中文含义 |
| --- | --- | --- |
| 17 | `clap` | 鼓掌 |
| 20 | `heart` | 双手比心 |
| 25 | `face wave` | 胸前挥手 |
| 26 | `high wave` | 头顶挥手 |
| 27 | `shake hand` | 握手 |
| 99 | `release arm` | 释放手臂姿态 |

这些动作的轨迹、时序、状态判断和平衡处理由机器人内部服务完成。用户程序只负责下达动作编号或动作名称。

---

## 3. SDK2 在高层动作里负责什么

`unitree_sdk2` 是 Unitree 官方 C++ SDK，`unitree_sdk2_python` 是 Python 封装版本。

它们主要负责：

- 初始化通信通道。
- 找到对应的机器人服务。
- 发送 RPC 请求。
- 等待并返回执行结果。
- 把底层 DDS 通信细节封装起来。

以 G1 手臂动作为例：

```python
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.arm.g1_arm_action_client import G1ArmActionClient

ChannelFactoryInitialize(0, "eth0")

client = G1ArmActionClient()
client.SetTimeout(10.0)
client.Init()
client.ExecuteAction(17)
```

背后的流程可以理解为：

```text
你的 Python/C++ 程序
    ↓
G1ArmActionClient
    ↓
Unitree SDK2 RPC / Channel
    ↓
DDS 网络通信
    ↓
G1 机器人内部手臂动作服务
    ↓
机器人执行鼓掌
```

所以 `G1ArmActionClient` 是客户端，真正执行动作的是机器人内部的服务端。

---

## 4. G1ArmActionClient 和 LocoClient 的区别

G1 高层能力里常见两类 Client。

### 4.1 G1ArmActionClient

`G1ArmActionClient` 主要负责上半身和手臂类预置动作。

典型接口：

```python
arm_client.ExecuteAction(17)  # 鼓掌
arm_client.ExecuteAction(20)  # 双手比心
arm_client.ExecuteAction(99)  # 释放手臂
```

它更像是在调用“表演动作”或“手势动作”。

### 4.2 LocoClient

`LocoClient` 主要负责运动模式、站立、移动、坐下等身体运动能力。

典型接口：

```python
loco.Start()
loco.Sit()
loco.Move(0.3, 0.0, 0.0)
loco.WaveHand()
loco.ShakeHand()
```

可以这样区分：

```text
G1ArmActionClient：更偏手臂手势，例如鼓掌、比心、飞吻、释放手臂
LocoClient：更偏身体运动，例如启动、坐下、移动、挥手、握手
```

---

## 5. 高层接口不是 ROS action

很多 ROS 用户容易误解，以为“动作接口”就是 ROS 里的 action。

但 G1 高层预置动作不是这种形式：

```text
ros2 action send_goal /xxx ...
```

它也不是简单发布一个 topic：

```text
ros2 topic pub /action_name clap
```

G1 高层动作本质上是 Unitree SDK2 的 RPC 服务调用。

例如：

| 高层能力 | SDK2 接口 | API 语义 |
| --- | --- | --- |
| 执行手臂预置动作 | `ExecuteAction(id)` | 请求机器人执行指定动作 ID |
| 获取动作列表 | `GetActionList()` | 从机器人读取当前支持动作 |
| 移动 | `Move(vx, vy, vyaw)` | 请求运控服务按速度移动 |
| 坐下 | `Sit()` | 请求运控服务执行坐下 |

其中手臂动作常见 API ID：

| API ID | 含义 |
| --- | --- |
| 7106 | 执行预置手臂动作 |
| 7107 | 获取动作列表 |
| 7108 | 执行自定义示教动作 |

---

## 6. unitree_ros2 和 SDK2 的关系

`unitree_ros2` 可以理解为 Unitree 官方能力在 ROS2 生态里的接入层。

它不是另一个完全独立的机器人控制体系。

更通俗地说：

```text
unitree_sdk2
    ↓
Unitree 官方核心通信和控制接口

unitree_ros2
    ↓
把 Unitree 通信能力接入 ROS2 节点、话题和示例工程
```

如果你使用 ROS2 做导航、感知、Rviz 可视化或多节点协作，`unitree_ros2` 会比较方便。

但 G1 高层动作的核心语义仍然来自 SDK2：

```text
执行哪个动作 ID
调用哪个运控方法
返回什么错误码
当前 FSM 是否允许执行
```

也就是说，`unitree_ros2` 是集成层，SDK2 是核心能力来源。

---

## 7. FSM 状态为什么重要

G1 不是任何状态下都允许执行高层动作。

例如手臂预置动作通常要求机器人处于特定 FSM 状态，如：

```text
500, 501, 801
```

如果状态不对，执行动作可能返回类似 `INVALID_FSM_ID` 的错误。

通俗理解：

```text
机器人还没进入“可以执行动作”的模式，你就让它鼓掌，它会拒绝。
```

所以常见流程是：

```python
loco.Start()
arm.ExecuteAction(17)
```

也就是先让机器人进入可执行动作状态，再调用手臂动作。

---

## 8. 真机执行前准备

真实执行 G1 预置动作前，先确认硬件、网络和软件环境都处于可控状态。模块 B 的重点不是自己编写关节轨迹，而是把操作说明中的动作名称正确映射到 SDK2 高层接口，再让 G1 真机内部服务执行动作。

### 8.1 安全检查

执行任何动作前都要先做安全确认：

- G1 Edu 已正确上电，电量充足。
- 机器人周围没有人员、桌椅、线缆、工具箱等障碍物。
- 移动吊架、保护绳或赛场要求的保护装置已经就位。
- 急停按钮可触达，现场有人负责观察机器人状态。
- 不要在机器人手臂附近放置易被碰撞、夹伤或拉扯的物品。
- 第一次执行新动作时，先选择幅度较小、风险较低的动作，例如 `clap` 或 `face wave`。

### 8.2 软件环境

在控制电脑上进入项目目录：

```bash
cd /home/a24/project/RobotLearning
```

安装模块 B 依赖和 Unitree Python SDK：

```bash
chmod +x src/moduleB/setup_g1_env.sh
src/moduleB/setup_g1_env.sh
```

安装完成后检查 Python 是否能导入 SDK：

```bash
python3 -c "import unitree_sdk2py; print('unitree sdk2 python ok')"
```

如果无法导入，通常是 `unitree_sdk2_python` 没有安装成功。可以重新执行：

```bash
python3 -m pip install --user third_party/unitree_sdk2_python
```

### 8.3 网线连接

常见连接方式如下：

```text
控制电脑网口
    ↓
网线 / 交换机
    ↓
G1 真机网络接口
```

连接后在控制电脑查看网卡名称：

```bash
ip link
```

常见网卡名可能是：

```text
eth0
enp3s0
enx...
```

后续执行脚本时，`--iface` 参数必须填写这块连接 G1 的网卡名。例如网卡名是 `eth0`，就使用：

```bash
--iface eth0
```

如果电脑同时连接了无线网和有线网，不要把无线网卡名填给 `--iface`。SDK2 需要使用和 G1 通信的有线网卡。

### 8.4 网络状态检查

先确认网卡已经启用：

```bash
ip addr show eth0
```

如果你的网卡名不是 `eth0`，把命令里的 `eth0` 替换成实际名称。

如果赛场或官方文档要求配置静态 IP，请把控制电脑配置到和 G1 同一网段。不同赛场可能会提前配置好网络，比赛时以现场说明为准。

可以用下面命令确认脚本能正常运行，并查看本地内置动作映射：

```bash
python3 src/moduleB/g1_action_interface.py --list
```

注意：`--list` 不会连接机器人，也不会让机器人运动。真正连接 G1 时，需要在执行动作命令里指定 `--iface`。

---

## 9. 让 G1 进入可执行动作状态

G1 高层动作依赖真机内部运动服务和 FSM 状态。手臂预置动作通常要求机器人处于可执行动作的状态，例如 `500`、`501` 或 `801`。

常见准备流程：

1. 打开 G1 电源，等待系统启动完成。
2. 按赛场或官方流程使用遥控器让机器人站立或进入可执行动作状态。
3. 确认机器人没有处于急停、保护、倒地、阻尼或禁止高层控制的状态。
4. 控制电脑连接 G1 后，先执行 `start`，再执行具体动作。

在脚本里，默认会在动作序列前自动调用：

```python
LocoClient.Start()
```

如果机器人状态不允许执行动作，可能会返回 `INVALID_FSM_ID` 或动作没有响应。此时应先检查机器人状态、遥控器状态、急停状态和连接网卡是否正确。

---

## 10. 执行一个预置动作

下面以“鼓掌”为例说明完整流程。

### 10.1 查看支持动作

进入项目目录：

```bash
cd /home/a24/project/RobotLearning
```

查看脚本支持的动作名称、中文别名和接口映射：

```bash
python3 src/moduleB/g1_action_interface.py --list
```

你会看到类似动作：

```text
clap            arm id=17  鼓掌
heart           arm id=20  双手比心
face_wave       arm id=25  胸前挥手
high_wave       arm id=26  头顶挥手
shake_hand      arm id=27  握手
release_arm     arm id=99  释放手臂姿态
```

### 10.2 执行鼓掌

确认 G1 周围安全后执行：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "start,clap,release arm"
```

如果你的网卡名不是 `eth0`，替换为实际网卡名。例如：

```bash
python3 src/moduleB/g1_action_interface.py --iface enp3s0 --actions "start,clap,release arm"
```

命令含义：

```text
start       让 G1 进入可执行动作状态
clap        调用 G1ArmActionClient.ExecuteAction(17)
release arm 调用 G1ArmActionClient.ExecuteAction(99)，释放手臂姿态
```

也可以直接使用中文动作名：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "站立,鼓掌,释放手臂"
```

### 10.3 跳过重复确认

脚本真实执行前会提示安全确认，需要输入 `YES` 才继续。熟悉流程后，如果赛场允许，也可以使用：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "start,clap,release arm" --yes
```

建议训练初期不要跳过确认，避免误触发动作。

### 10.4 自动释放手臂

部分手臂动作会在最后一帧保持姿态，例如比心、拥抱、举手等。可以让脚本自动追加 `release arm`：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "start,heart" --auto-release
```

等价于：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "start,heart,release arm"
```

### 10.5 最简 SDK2 教学脚本

如果只想教学“连接真机并执行一个动作 ID”，可以使用：

```bash
python3 src/moduleB/minimal_g1_action.py --iface eth0
```

这个命令默认执行：

```text
LocoClient.Start()
G1ArmActionClient.ExecuteAction(17)
```

其中 `17` 是 `clap`，也就是鼓掌。

执行比心并自动释放手臂：

```bash
python3 src/moduleB/minimal_g1_action.py --iface eth0 --action-id 20 --release
```

脚本用途：

- 适合课堂上逐行讲解 SDK2 初始化流程。
- 不做 OCR。
- 不做中文动作解析。
- 不封装复杂动作序列。
- 重点展示 `ChannelFactoryInitialize`、`LocoClient`、`G1ArmActionClient` 三个核心对象。

### 10.6 最简 ROS2 教学脚本

如果训练环境已经安装并 source 了 Unitree ROS2，可以用 ROS2 话题直接发送高层 API 请求：

```bash
python3 src/moduleB/minimal_g1_ros2_action.py --action-id 17
```

执行比心并释放手臂：

```bash
python3 src/moduleB/minimal_g1_ros2_action.py --action-id 20 --release
```

指定 ROS domain：

```bash
python3 src/moduleB/minimal_g1_ros2_action.py --domain-id 0 --action-id 17
```

ROS2 版脚本本质上做了两件事：

```text
/api/sport/request
    api_id = 7101
    data = 500
    含义：请求 G1 进入 Start / FSM 500 状态

/api/arm/request
    api_id = 7106
    data = 动作 ID
    含义：请求 G1 执行某个手臂预置动作
```

它会订阅对应响应话题：

```text
/api/sport/response
/api/arm/response
```

并按 `identity.id` 等待本次请求对应的返回结果。

### 10.7 备注：ROS2 / CycloneDDS 也需要选对网卡

ROS2 版脚本虽然没有 `--iface` 参数，但底层仍然依赖 DDS 网络通信。Unitree ROS2 通常使用 `rmw_cyclonedds_cpp`，也就是 CycloneDDS。CycloneDDS 同样需要知道应该从哪一块网卡和 G1 通信。

如果电脑上有多块网卡，例如：

```text
lo        本机回环
wlp...    无线网卡
enp...    有线网卡
docker0   Docker 虚拟网卡
virbr0    虚拟机网卡
```

CycloneDDS 自动选择时可能选到错误网卡，导致脚本发出了 `/api/sport/request` 或 `/api/arm/request`，但一直收不到 `/api/sport/response` 或 `/api/arm/response`。这时常见现象是：

```text
TimeoutError: 等待 api_id=7101 的响应超时
```

所以运行 ROS2 版脚本前，建议显式指定连接 G1 的有线网卡。先查看网卡：

```bash
ip link
```

假设连接 G1 的网卡名是 `enp3s0`，则在同一个终端中执行：

```bash
source /opt/ros/humble/setup.bash
source /home/a24/project/RobotLearning/third_party/unitree_ros2/cyclonedds_ws/install/setup.bash

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI='<CycloneDDS><Domain><General><Interfaces>
<NetworkInterface name="enp3s0" priority="default" multicast="default" />
</Interfaces></General></Domain></CycloneDDS>'
```

把 `enp3s0` 替换成实际连接 G1 的网卡名。

然后先检查 ROS2 是否能看到 Unitree 话题：

```bash
ros2 topic list
```

重点查看是否出现：

```text
/api/sport/request
/api/sport/response
/api/arm/request
/api/arm/response
```

确认后再运行：

```bash
python3 src/moduleB/minimal_g1_ros2_action.py --action-id 17
```

如果只是想测试手臂动作通道，也可以先跳过 Start 请求：

```bash
python3 src/moduleB/minimal_g1_ros2_action.py --action-id 99 --no-start
```

如果这条命令也超时，说明 `/api/arm/request` / `/api/arm/response` 也没有通信成功，应继续检查 CycloneDDS 网卡、机器人连接、ROS_DOMAIN_ID 和 Unitree ROS2 环境是否正确 source。

---

## 11. 从操作说明到动作执行

模块 B 常见流程是先从图片或文字中提取“操作说明”，再把说明里的动作词转换成动作序列。

如果已经有一份文本文件，例如 `/tmp/g1_instruction.txt`，内容类似：

```text
请让机器人先站立，然后鼓掌，最后释放手臂。
```

可以直接执行：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --instruction-file /tmp/g1_instruction.txt --auto-release
```

如果需要先从图片提取文字，可以执行：

```bash
python3 src/moduleB/OCR.py operation_instruction.jpg --paragraph > /tmp/g1_instruction.txt
python3 src/moduleB/g1_action_interface.py --iface eth0 --instruction-file /tmp/g1_instruction.txt --auto-release
```

实际比赛时，图片路径、文本路径和提交方式以赛题要求为准。

---

## 12. 真机动作实时镜像到 MuJoCo 用于截图

有时训练或验收需要一个可截图的可视化窗口。可以让 G1 真机执行预置动作，同时把真机实时关节角同步显示到 MuJoCo G1 模型中。

注意这里的含义：

```text
不是 MuJoCo 执行预置动作
而是真机执行动作，MuJoCo 跟随显示真机关节姿态
```

数据流如下：

```text
G1 真机执行预置动作
    ↓
SDK2 订阅 rt/lowstate
    ↓
读取 motor_state[0..28].q
    ↓
写入 MuJoCo G1 模型 qpos
    ↓
MuJoCo 窗口显示并截图
```

### 12.1 准备 MuJoCo 模型

脚本默认使用下面路径：

```text
/home/a24/project/RobotLearning/third_party/unitree_mujoco/unitree_robots/g1/scene_29dof.xml
```

如果这个文件不存在，需要先安装或克隆官方 `unitree_mujoco`，或者运行时用 `--mjcf` 指定实际路径。

Python 侧还需要安装 `mujoco`：

```bash
python3 -m pip install --user mujoco
```

### 12.2 启动实时镜像窗口

终端 1 启动 MuJoCo 镜像窗口：

```bash
cd /home/a24/project/RobotLearning
python3 src/moduleB/realtime_g1_to_mujoco.py --iface eth0
```

如果模型路径不同：

```bash
python3 src/moduleB/realtime_g1_to_mujoco.py \
  --iface eth0 \
  --mjcf /path/to/unitree_mujoco/unitree_robots/g1/scene_29dof.xml
```

如果 G1 的有线网卡不是 `eth0`，替换成实际网卡名。

### 12.3 让真机执行动作

终端 2 执行动作：

```bash
cd /home/a24/project/RobotLearning
python3 src/moduleB/minimal_g1_action.py --iface eth0 --action-id 17 --release
```

这时真机会执行鼓掌，MuJoCo 窗口会尽量跟随显示真机当前关节姿态。

也可以换成比心：

```bash
python3 src/moduleB/minimal_g1_action.py --iface eth0 --action-id 20 --release
```

### 12.4 查看关节映射

如果 MuJoCo 窗口姿态不对，先打印当前模型的关节名：

```bash
python3 src/moduleB/realtime_g1_to_mujoco.py --iface eth0 --print-joints
```

脚本内置的是 G1 29DOF 的官方关节顺序：

```text
LowState.motor_state[0..28]
    ↓
left_hip_pitch_joint ... right_wrist_yaw_joint
```

如果模型关节名和脚本内置名字不同，需要修改 `realtime_g1_to_mujoco.py` 里的 `G1_29DOF_JOINT_NAME_ALIASES`。

### 12.5 截图建议

实时镜像适合教学和截图，但要注意：

- MuJoCo 只是显示真机姿态，不负责平衡控制。
- 画面可能受网络延迟和状态发布频率影响。
- 如果只需要漂亮截图，可以先让真机动作执行到关键姿态，再在 MuJoCo 窗口截图。
- 比赛或评分是否接受这种截图，要以赛题和裁判要求为准。

---

## 13. 常见问题排查

### 13.1 找不到 SDK

现象：

```text
未安装 unitree_sdk2_python
```

处理：

```bash
cd /home/a24/project/RobotLearning
src/moduleB/setup_g1_env.sh
python3 -m pip install --user third_party/unitree_sdk2_python
```

### 13.2 网卡名填错

现象：

```text
连接超时
机器人没有响应
```

处理：

```bash
ip link
ip addr
```

确认哪一块有线网卡连接 G1，然后重新指定：

```bash
python3 src/moduleB/g1_action_interface.py --iface 正确网卡名 --actions "start,clap,release arm"
```

### 13.3 FSM 状态不允许执行

现象：

```text
INVALID_FSM_ID
动作没有执行
```

处理：

- 确认机器人已经站稳。
- 确认没有急停。
- 按赛场或官方流程让 G1 进入可执行动作状态。
- 先执行 `start`，再执行具体动作。
- 如果机器人处于调试、保护或不可运动状态，先退出该状态。

### 13.4 动作执行后手臂保持姿态

这是部分预置动作的正常现象。执行：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "release arm"
```

或在动作命令后追加：

```bash
--auto-release
```

### 13.5 动作名称无法识别

现象：

```text
未识别动作
```

处理：

```bash
python3 src/moduleB/g1_action_interface.py --list
```

按列表中的动作 key、英文别名或中文别名填写。例如：

```bash
python3 src/moduleB/g1_action_interface.py --iface eth0 --actions "鼓掌,比心,释放手臂"
```

### 13.6 MuJoCo 镜像窗口找不到模型

现象：

```text
找不到 MuJoCo 模型文件
```

处理：

```bash
python3 src/moduleB/realtime_g1_to_mujoco.py \
  --iface eth0 \
  --mjcf /path/to/unitree_mujoco/unitree_robots/g1/scene_29dof.xml
```

如果还没有 `unitree_mujoco`，需要先克隆官方仓库并确认 `unitree_robots/g1/scene_29dof.xml` 存在。

### 13.7 MuJoCo 镜像姿态不对

可能原因：

- 使用了 23DOF 或其他版本模型。
- 模型关节名和脚本内置关节名不一致。
- 真机 `LowState` 的关节顺序与模型版本不匹配。

先查看模型关节：

```bash
python3 src/moduleB/realtime_g1_to_mujoco.py --iface eth0 --print-joints
```

再根据输出修改：

```text
src/moduleB/realtime_g1_to_mujoco.py
G1_29DOF_JOINT_NAME_ALIASES
```

---

## 14. 总结

最重要的关系可以记成下面这张图：

```text
比赛操作说明
    ↓
OCR / 文本解析
    ↓
动作名称映射
    ↓
G1ArmActionClient / LocoClient
    ↓
Unitree SDK2 RPC / DDS
    ↓
G1 真机内部高层动作服务
    ↓
执行预置动作
```

一句话总结：

```text
SDK2 是核心通信和控制接口；
unitree_ros2 是 ROS2 集成层；
G1ArmActionClient 和 LocoClient 是客户端；
真正执行预置动作的是 G1 真机内部高层动作服务。
```
