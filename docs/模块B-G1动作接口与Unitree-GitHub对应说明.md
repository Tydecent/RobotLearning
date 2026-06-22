# 模块 B：G1 动作接口与 Unitree GitHub 对应说明

> 基于 [unitreerobotics](https://github.com/unitreerobotics) 组织仓库研究，对照《人工智能训练师-技术文件.pdf》样题中模块 B「机器人操作与控制」任务。  
> 赛场硬件：**G1 Edu 标准版**；本文说明 GitHub 上哪些部分对应「操作说明 → 调用封装动作接口」。

---

## 一、技术文件里模块 B 在说什么

样题（PDF 第 20 页）要求：

1. **任务一**：从图片中提取机器人「操作说明」关键信息并打印。
2. **任务二**：根据任务一得到的「操作说明」，**调用封装好的机器人动作接口**，使机器人完成指定动作。

技术文件还写明：

- 赛场硬件：**G1 Edu 标准版**（含移动吊架）。
- 赛场软件：**中慧云启具身智能机器人竞赛平台 1.0**（赛方定制，**不在** unitreerobotics GitHub 上）。

**注意**：PDF 本身不包含「操作说明」正文；正式赛时通常是一张图片或文档，列出动作名称、顺序、参数等。GitHub 上对应的是 **G1 固件/SDK 提供的预置动作清单与调用方式**，不是赛方那张图片本身。

模块 B 概述（PDF 第 6 页）：

> 选手需基于封装好的标准化机器人独立动作，依托机器人控制架构，根据任务需求自主调用相关动作，使机器人实现指定动作。

---

## 二、核心对应关系

赛题所说的「封装好的标准化机器人独立动作」，在官方 GitHub 上主要体现在 **两套高层 Client**：

| 能力类型 | 封装接口 | 典型动作 |
|---------|---------|---------|
| **上半身预置手势** | `G1ArmActionClient` | 鼓掌、挥手、握手、比心、举手、飞吻等 |
| **全身运动/姿态** | `LocoClient` | 启动、站立、坐下、移动、挥手、握手（另一套入口） |

整体流程：

```
操作说明（赛场图片，含中文动作名/顺序）
        ↓ OCR 提取（不在 unitreerobotics，可用 PaddleOCR / EasyOCR 等）
        ↓ 映射到动作 ID / Loco 命令
        ↓ 调用封装接口
┌─────────────────────────────────────────────────────────┐
│ unitree_sdk2_python  或  unitree_sdk2  或  unitree_ros2   │
│   G1ArmActionClient.ExecuteAction(id)                   │
│   LocoClient.Start() / Move() / Sit() / WaveHand()      │
└─────────────────────────────────────────────────────────┘
        ↓
   G1 Edu 真机执行
```

---

## 三、unitreerobotics 各仓库与模块 B 的对应

### 1. 首选：`unitree_sdk2`（C++ SDK，动作定义最完整）

**仓库**：[https://github.com/unitreerobotics/unitree_sdk2](https://github.com/unitreerobotics/unitree_sdk2)

#### （1）上半身预置动作 —— 与「操作说明」手势类内容最直接对应

| GitHub 路径 | 内容 |
|------------|------|
| [`include/unitree/robot/g1/arm/g1_arm_action_client.hpp`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/arm/g1_arm_action_client.hpp) | 核心封装类 `G1ArmActionClient`；内含 `action_map`（动作名 → ID） |
| [`include/unitree/robot/g1/arm/g1_arm_action_api.hpp`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/arm/g1_arm_action_api.hpp) | API 定义：`7106` 执行动作、`7107` 获取动作列表 |
| [`example/g1/high_level/g1_arm_action_example.cpp`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/example/g1/high_level/g1_arm_action_example.cpp) | 官方示例：列出 / 按 ID 执行预置动作 |

**关键方法：**

- `ExecuteAction(int32_t action_id)` — 按 ID 执行预置动作
- `ExecuteAction(const std::string &action_name)` — 按名称执行自定义示教动作
- `GetActionList(std::string &data)` — 从机器人读取当前固件支持的动作列表

**`action_map` 中的预置动作（操作说明里常见中文名可对应）：**

| ID | 英文名 | 常见中文含义 |
|----|--------|-------------|
| 11 | two-hand kiss | 双手飞吻 |
| 12 | left kiss | 左手飞吻 |
| 13 | right kiss | 右手飞吻 |
| 15 | hands up | 双手举起 |
| 17 | clap | 鼓掌 |
| 18 | high five | 击掌 |
| 19 | hug | 拥抱 |
| 20 | heart | 双手比心 |
| 21 | right heart | 右手比心 |
| 22 | reject | 拒绝 / 叉手 |
| 23 | right hand up | 右手举起 |
| 24 | x-ray | 奥特曼 / 射线手势 |
| 25 | face wave | 胸前挥手 |
| 26 | high wave | 头顶挥手 |
| 27 | shake hand | 握手 |
| 99 | release arm | 释放手臂姿态 |

#### （2）全身运动/姿态 —— 与「站立、移动、坐下」类操作说明对应

| GitHub 路径 | 内容 |
|------------|------|
| [`include/unitree/robot/g1/loco/g1_loco_client.hpp`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/loco/g1_loco_client.hpp) | `LocoClient`：`Start()`、`Sit()`、`Move()`、`WaveHand()`、`ShakeHand()` 等 |
| [`example/g1/high_level/g1_loco_client_example.cpp`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/example/g1/high_level/g1_loco_client_example.cpp) | 官方示例：命令行调用各类运动动作 |

**LocoClient 常见封装动作：**

| 方法 | 含义 |
|------|------|
| `Start()` | FSM 500，进入可执行动作状态（许多手臂动作的前置条件） |
| `Sit()` / `StandUp()` / `Squat()` | 坐下 / 站起 / 蹲 |
| `Damp()` / `ZeroTorque()` | 阻尼 / 零力矩 |
| `Move(vx, vy, vyaw)` | 行走 / 转向 |
| `StopMove()` | 停止移动 |
| `HighStand()` / `LowStand()` | 高站 / 低站 |
| `WaveHand()` / `WaveHand(true)` | 挥手 / 转身挥手 |
| `ShakeHand(stage)` | 握手（分阶段） |

#### （3）G1 示例总目录

[`example/g1/high_level/`](https://github.com/unitreerobotics/unitree_sdk2/tree/main/example/g1/high_level)

模块 B 应重点阅读此目录，而不是 `low_level/`（低层关节控制，不属于「封装好的独立动作」）。

同目录下其他文件（供扩展参考）：

- `g1_arm5_sdk_dds_example.cpp` / `g1_arm7_sdk_dds_example.cpp` — 手臂 SDK 低层 DDS 控制
- `g1_hand_sdk_example.cpp` — 灵巧手控制

---

### 2. Python 脚本场景：`unitree_sdk2_python`

**仓库**：[https://github.com/unitreerobotics/unitree_sdk2_python](https://github.com/unitreerobotics/unitree_sdk2_python)

与样题「编写脚本」形式最接近。

| GitHub 路径 | 内容 |
|------------|------|
| [`unitree_sdk2py/g1/arm/g1_arm_action_client.py`](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/unitree_sdk2py/g1/arm/g1_arm_action_client.py) | Python 版 `G1ArmActionClient` + `action_map` |
| [`unitree_sdk2py/g1/arm/g1_arm_action_api.py`](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/unitree_sdk2py/g1/arm/g1_arm_action_api.py) | API ID 常量 |
| [`unitree_sdk2py/g1/loco/g1_loco_client.py`](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/unitree_sdk2py/g1/loco/g1_loco_client.py) | Python 版 `LocoClient` |
| [`example/g1/high_level/g1_arm_action_example.py`](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/example/g1/high_level/g1_arm_action_example.py) | Python 手臂动作示例 |
| [`example/g1/high_level/g1_loco_client_example.py`](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/example/g1/high_level/g1_loco_client_example.py) | Python 运动控制示例 |

典型用法思路：**OCR 解析中文动作名 → 查 `action_map` → `ExecuteAction(id)`**。

---

### 3. ROS2 场景：`unitree_ros2`

**仓库**：[https://github.com/unitreerobotics/unitree_ros2](https://github.com/unitreerobotics/unitree_ros2)

| GitHub 路径 | 内容 |
|------------|------|
| [`example/src/src/g1/high_level/g1_arm_action_example.cpp`](https://github.com/unitreerobotics/unitree_ros2/blob/master/example/src/src/g1/high_level/g1_arm_action_example.cpp) | ROS2 下调用 G1 手臂预置动作 |
| [`example/src/src/g1/high_level/loco_client_example.cpp`](https://github.com/unitreerobotics/unitree_ros2/blob/master/example/src/src/g1/high_level/loco_client_example.cpp) | ROS2 下 Loco 运动/姿态控制 |
| [`example/src/src/g1/high_level/`](https://github.com/unitreerobotics/unitree_ros2/tree/master/example/src/src/g1/high_level) | G1 高层控制示例目录 |

底层仍对应 SDK2 的 API（如 `7106` / `7107`），通过 ROS2 + DDS 封装。技术文件列了 Rviz2 等工具，但 G1 真机高层动作仍以 **SDK2 接口语义** 为准。

---

## 四、与模块 B 不太相关的 unitreerobotics 仓库

| 仓库 | 原因 |
|------|------|
| [`unitree_ros`](https://github.com/unitreerobotics/unitree_ros) 的 [`robots/g1_description`](https://github.com/unitreerobotics/unitree_ros/tree/master/robots/g1_description) | 模块 **A**（URDF / 仿真模型），不是动作接口 |
| [`unitree_rl_gym`](https://github.com/unitreerobotics/unitree_rl_gym) | 强化学习仿真 |
| [`unitree_rl_lab`](https://github.com/unitreerobotics/unitree_rl_lab) | IsaacLab 强化学习 |
| [`xr_teleoperate`](https://github.com/unitreerobotics/xr_teleoperate) | XR 遥操作 |
| [`unitree_lerobot`](https://github.com/unitreerobotics/unitree_lerobot) | 策略训练与部署 |
| [`unitree_sim_isaaclab`](https://github.com/unitreerobotics/unitree_sim_isaaclab) | Isaac 仿真 |

---

## 五、执行「操作说明」时的重要注意事项

以下内容在 SDK 示例与头文件注释中有说明，与赛场实际操作强相关。

### 1. FSM 状态限制

手臂预置动作通常只在 FSM ID **`{500, 501, 801}`** 下可用（见 `g1_arm_action_example.cpp` 错误提示）。执行前往往需先调用 `LocoClient.Start()`（FSM 500）。

可通过话题 `rt/sportmodestate` 查看当前 FSM 状态。

### 2. 动作列表以真机为准

应调用 `GetActionList()`（API **7107**）获取机器人当前支持的动作。固件版本不同，可用 ID 可能多于 `action_map` 中列出的 16 个。

### 3. 释放姿态

部分动作结束后会保持姿态；需发送 **`release arm`（ID 99）** 或再次发送相同 ID 以释放。

### 4. 两套「挥手 / 握手」入口

| 场景 | 调用方式 |
|------|---------|
| 手臂预置 API | `G1ArmActionClient.ExecuteAction(25/26/27)` |
| 运动控制 API | `LocoClient.WaveHand()` / `ShakeHand()` |

操作说明若只写「挥手」，需结合上下文判断使用哪套接口。

### 5. 安全提示

SDK 示例中注明：部分动作在 APP 上不显示，但程序可执行；某些动作可能导致机器人失衡，需谨慎执行。

---

## 六、API ID 速查

| API ID | 名称 | 用途 |
|--------|------|------|
| 7106 | `ROBOT_API_ID_ARM_ACTION_EXECUTE_ACTION` | 执行预置手臂动作 |
| 7107 | `ROBOT_API_ID_ARM_ACTION_GET_ACTION_LIST` | 获取可用动作列表 |
| 7108 | `ROBOT_API_ID_ARM_ACTION_EXECUTE_CUSTOM_ACTION` | 执行自定义示教动作（按名称） |

---

## 七、推荐阅读顺序

1. [unitree_sdk2 — `g1_arm_action_client.hpp`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/arm/g1_arm_action_client.hpp)  
   预置手势名称与 ID 映射。

2. [unitree_sdk2 — `g1_loco_client.hpp`](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/g1/loco/g1_loco_client.hpp)  
   站立、移动、姿态类动作。

3. [unitree_sdk2_python — `g1_arm_action_client.py`](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/unitree_sdk2py/g1/arm/g1_arm_action_client.py)  
   Python 封装，与样题脚本形式一致。

4. 对应 `example/g1/high_level/` 下的官方示例（C++ 或 Python，按赛场环境选择）。

---

## 八、赛场与 GitHub 的关系

| 层级 | 说明 |
|------|------|
| **GitHub（unitreerobotics）** | G1 Edu 底层官方 SDK 能力：动作语义、ID、FSM 要求 |
| **中慧云启竞赛平台 1.0** | 赛方定制封装，函数名/参数可能与 SDK 不完全相同 |
| **正式比赛** | 以赛场平台与当日试题提供的「操作说明」为准 |

GitHub 用于赛前理解 G1 预置动作体系；正式比赛接口以赛方平台文档为准。

---

## 九、相关链接

- Unitree 组织主页：[https://github.com/unitreerobotics](https://github.com/unitreerobotics)
- SDK2 开发者文档（官网）：[https://support.unitree.com/home/zh/developer](https://support.unitree.com/home/zh/developer)
- G1 开发者概览（官网）：[https://support.unitree.com/home/zh/G1_developer/overview](https://support.unitree.com/home/zh/G1_developer/overview)
- 本项目开源学习索引：[`开源学习项目.md`](./开源学习项目.md)

---

*文档生成依据：技术工作文件样题、unitreerobotics 公开仓库（截至 2026 年 6 月）。*
