# 模块 B：G1 C++ 高层动作最小实现

本目录提供 Unitree G1 高层预置动作的 C++ 最小示例，对齐官方 `unitree_sdk2` 的 `G1ArmActionClient` 和 `LocoClient` 用法。

它不解析 OCR 文本，也不做交互式安全确认，只保留最小控制链路：

```text
初始化 SDK2 DDS 网卡
    -> LocoClient.Start() 进入 FSM 500
    -> G1ArmActionClient.ExecuteAction(action_id)
    -> 可选 ExecuteAction(99) 释放手臂姿态
```

## 1. 前置条件

需要先准备官方 C++ SDK2。本项目已有脚本会克隆并构建 `third_party/unitree_sdk2`：

```bash
cd /home/a24/project/RobotLearning
src/moduleB/setup_g1_mujoco_env.sh
```

如果系统依赖已经安装好，或当前用户没有 `sudo` 权限，可按现有脚本约定跳过 apt：

```bash
SKIP_APT=1 src/moduleB/setup_g1_mujoco_env.sh
```

## 2. 构建

从仓库根目录执行：

```bash
cd /home/a24/project/RobotLearning
chmod +x src/moduleB/build_g1_cpp_action.sh
src/moduleB/build_g1_cpp_action.sh
```

构建脚本会优先链接 `third_party/unitree_sdk2` 源码树中的官方构建产物，尤其是：

```text
third_party/unitree_sdk2/lib/x86_64/libunitree_sdk2.a
third_party/unitree_sdk2/thirdparty/lib/x86_64/libddsc.so
third_party/unitree_sdk2/thirdparty/lib/x86_64/libddscxx.so
```

不要手动改成链接 `third_party/unitree_robotics/lib` 下的安装前缀库；当前环境中该路径下的 DDS 库可能在创建 SDK2 通道时触发 `free(): invalid pointer`。

如果当前终端已经设置了 `LD_LIBRARY_PATH`，它的优先级会高于程序构建时写入的运行时库路径。也就是说，即使本程序已按官方示例链接到 `third_party/unitree_sdk2/thirdparty/lib/x86_64`，终端里的 `LD_LIBRARY_PATH` 仍可能让程序优先加载 `third_party/unitree_robotics/lib` 下的 `libddsc.so.0` / `libddscxx.so.0`，从而再次触发 `free(): invalid pointer`。

运行前可检查实际加载的 DDS 库：

```bash
ldd src/moduleB/cpp/build/minimal_g1_action | grep ddsc
```

如果输出不是 `third_party/unitree_sdk2/thirdparty/lib/x86_64`，请用下面的方式临时把正确库路径放到最前面：

```bash
LD_LIBRARY_PATH=/home/a24/project/RobotLearning/third_party/unitree_sdk2/thirdparty/lib/x86_64:$LD_LIBRARY_PATH \
  src/moduleB/cpp/build/minimal_g1_action --network eth0 --action-id 17
```

这不是为了加载 ROS 或额外 source 环境，而是为了确保 Linux 动态链接器优先使用与官方示例一致的 CycloneDDS 库。

构建产物位于：

```text
src/moduleB/cpp/build/minimal_g1_action
```

## 3. 运行

先找到连接 G1 的有线网卡名：

```bash
ip link
```

执行默认动作 `17=clap`：

```bash
src/moduleB/cpp/build/minimal_g1_action --network eth0
```

执行指定动作，例如 `20=heart`：

```bash
src/moduleB/cpp/build/minimal_g1_action --network eth0 --action-id 20
```

动作结束后追加 `99=release arm`：

```bash
src/moduleB/cpp/build/minimal_g1_action --network eth0 --action-id 20 --release
```

如果现场流程已经让 G1 处于可执行动作的 FSM，可跳过 `LocoClient.Start()`：

```bash
src/moduleB/cpp/build/minimal_g1_action --network eth0 --action-id 17 --no-start
```

按 Sport Services Interface 检查当前 `fsm_id` / `fsm_mode`：

```bash
src/moduleB/cpp/build/minimal_g1_action --network eth0 --action-id 17 --check-fsm
```

从真机读取当前固件支持的动作列表：

```bash
src/moduleB/cpp/build/minimal_g1_action --network eth0 --list
```

## 4. 常用动作 ID

```text
11 = two-hand kiss / 双手飞吻
12 = left kiss / 左手飞吻
13 = right kiss / 右手飞吻
15 = hands up / 双手举起
17 = clap / 鼓掌
18 = high five / 击掌
19 = hug / 拥抱
20 = heart / 双手比心
21 = right heart / 右手比心
22 = reject / 拒绝/叉手
23 = right hand up / 右手举起
24 = x-ray / 射线/奥特曼手势
25 = face wave / 胸前挥手
26 = high wave / 头顶挥手
27 = shake hand / 握手
99 = release arm / 释放手臂姿态
```

实际可用动作以 `--list` 从真机读取的结果为准。

## 5. 与官方接口的对应

本示例使用官方 C++ 文档中的 `LocoClient.Start()` 和 `G1ArmActionClient.ExecuteAction(id)` 路径。

核心调用关系：

```cpp
unitree::robot::ChannelFactory::Instance()->Init(0, network);

unitree::robot::g1::LocoClient loco_client;
loco_client.Init();
loco_client.Start();  // FSM 500

unitree::robot::g1::G1ArmActionClient arm_client;
arm_client.Init();
arm_client.ExecuteAction(action_id);
```

对应官方语义：

```text
LocoClient.Start()                  -> 设置 G1 高层运动 FSM 500
G1ArmActionClient.ExecuteAction(id) -> 执行手臂/上半身预置动作 ID
G1ArmActionClient.GetActionList()   -> 获取当前固件支持的动作列表
```

如果返回 `INVALID_FSM_ID`，通常表示当前状态不允许执行该手臂动作。可以先调用 `Start()`，或订阅 `rt/sportmodestate` 检查当前 FSM。

结合官方 Sport Services Interface，排查顺序建议是：

```text
1. LocoClient.Start() 返回 0，表示已请求进入 FSM 500。
2. 使用 --check-fsm 读取 GetFsmId() / GetFsmMode()。
3. 手臂预置动作通常要求 fsm_id 属于 {500, 501, 801}。
4. 如果 fsm_id=801，还需要确认 fsm_mode 属于 {0, 3}。
5. 如果 FSM 不满足，先按现场流程让机器人进入可运动/高层控制状态，再执行手臂动作。
```

参考：Unitree Sport Services Interface 中文页：[https://support.unitree.com/home/zh/G1_developer/sport_services_interface](https://support.unitree.com/home/zh/G1_developer/sport_services_interface)，英文页：[https://support.unitree.com/home/en/G1_developer/sport_services_interface](https://support.unitree.com/home/en/G1_developer/sport_services_interface)。

## 6. 注意事项

该 C++ 示例面向 G1 真机高层动作服务。MuJoCo 仿真可用于验证模型、DDS 链路和低层控制，但不能完整复现 `ExecuteAction(17)` 这类真机固件内置预置动作。

程序不会等待人工输入确认。真机运行前请按现场流程自行确认 G1 Edu、移动吊架、急停和周围空间状态。

程序在完成 SDK2 调用后会直接退出进程，跳过 C++ 全局对象和 SDK Client 的析构清理路径。这是为了规避部分 `unitree_sdk2`/CycloneDDS 本地构建组合在退出阶段出现 `free(): invalid pointer` 的问题；动作请求和返回码会在退出前打印。
