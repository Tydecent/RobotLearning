# ROS 2 多工作空间管理指南

**说明**：配套文档：[项目环境与电脑配置要求](./项目环境与电脑配置要求.md) 第 3.7 节（单工作空间创建）。适用环境：**ROS 2 Humble** · **Ubuntu 22.04** · **colcon**

---

## 目录


| 章节                              | 内容               |
| ------------------------------- | ---------------- |
| [一、为什么需要多个工作空间](#一为什么需要多个工作空间)  | 典型场景与原则          |
| [二、目录结构](#二目录结构)                | 一个项目 = 一个工作空间    |
| [三、切换工作空间](#三切换工作空间)            | source 与 overlay |
| [四、~/.bashrc 怎么配](#四bashrc-怎么配) | 只保留底层，项目按需加载     |
| [五、快捷切换脚本](#五快捷切换脚本)            | alias / 函数示例     |
| [六、项目之间有依赖时](#六项目之间有依赖时)        | overlay 链        |
| [七、验证与排错](#七验证与排错)              | 常用检查命令           |
| [八、备赛建议](#八备赛建议)                | 习惯与注意事项          |


---

## 一、为什么需要多个工作空间

在 [项目环境与电脑配置要求](./项目环境与电脑配置要求.md) 中，默认创建了 `~/ros2_ws` 作为练习空间。实际备赛或开发时，往往同时存在多个 ROS 2 项目，例如：

- 通用入门练习（`~/ros2_ws`）
- 赛题/院校提供的竞赛包（`~/competition_ws`）
- URDF / Gazebo 实验（`~/urdf_lab`）
- Nav2 / TurtleBot3 导航练习（`~/turtlebot3_nav`）

**核心原则**：

1. **一个项目 = 一个独立工作空间**（各自有 `src/`、`build/`、`install/`、`log/`）
2. **用时只加载当前项目**，不要把所有工作空间都写进 `~/.bashrc`
3. 各空间独立 `colcon build`，互不覆盖源码目录

---

## 二、目录结构

推荐按项目命名，避免全部叫 `ros2_ws`：

```text
~/
├── ros2_ws/                 # 通用练习（文档默认）
│   ├── src/
│   ├── build/
│   ├── install/
│   └── log/
├── competition_ws/          # 赛题相关包
│   ├── src/
│   └── ...
├── urdf_lab/                # 模块 A：URDF + Gazebo
│   └── ...
└── turtlebot3_nav/          # 模块 C：Nav2 导航
    └── ...
```

### 创建新工作空间

```bash
mkdir -p ~/competition_ws/src
cd ~/competition_ws

# 安装依赖（src 里已有包时执行）
rosdep install --from-paths src --ignore-src -r -y

colcon build
```

将克隆或新建的包放入对应空间的 `src/` 目录，在该空间根目录执行 `colcon build`。

---

## 三、切换工作空间

ROS 2 支持 **overlay（叠加）**：后 `source` 的工作空间会覆盖先 `source` 中同名的包。

### 推荐用法（每次只加载一个项目）

```bash
# 1. 加载系统 ROS 2（若 ~/.bashrc 已配置可跳过）
source /opt/ros/humble/setup.bash

# 2. 加载当前项目工作空间
source ~/competition_ws/install/setup.bash
```

切换到另一个项目时，**建议新开终端**，再 source 另一个空间：

```bash
source /opt/ros/humble/setup.bash
source ~/turtlebot3_nav/install/setup.bash
```

### 不要这样做

```bash
# ❌ 不要把多个工作空间都写进 ~/.bashrc
source ~/ros2_ws/install/setup.bash
source ~/competition_ws/install/setup.bash   # 易冲突、难排查
```

同一终端里反复 source 不同空间，环境变量会叠在一起，容易出现「找不到包」「用了旧版本包」等问题。

---

## 四、~/.bashrc 怎么配

### 建议配置

```bash
# 始终加载：系统 ROS 2 Humble
source /opt/ros/humble/setup.bash

# 可选：仅当你有一个「默认主项目」时再写
# source ~/ros2_ws/install/setup.bash
```

其他项目通过 **手动 source** 或 **第五节快捷函数** 切换，不要全部写死。

### 与文档 3.7 节的关系

文档 3.7 中的：

```bash
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
```

适合「只有一个主工作空间」的情况。若已有多个项目，可：

- 保留该行（`ros2_ws` 作为默认练习空间），或
- 注释/删除该行，改用快捷函数按需加载

---

## 五、快捷切换脚本（可选）

在 `~/.bashrc` 末尾添加函数，便于切换项目：

```bash
# 通用练习空间
ws_ros2() {
  source /opt/ros/humble/setup.bash
  source ~/ros2_ws/install/setup.bash
  cd ~/ros2_ws
}

# 赛题工作空间
ws_competition() {
  source /opt/ros/humble/setup.bash
  source ~/competition_ws/install/setup.bash
  cd ~/competition_ws
}

# Nav2 / TurtleBot3 练习
ws_nav() {
  source /opt/ros/humble/setup.bash
  source ~/turtlebot3_nav/install/setup.bash
  cd ~/turtlebot3_nav
}
```

保存后执行 `source ~/.bashrc`，使用时：

```bash
ws_competition   # 当前终端切换到赛题空间
ws_nav           # 切换到导航练习（建议新开终端更清晰）
```

---

## 六、项目之间有依赖时

若 **项目 B 依赖项目 A**（B 的包需要使用 A 中编译好的包），按顺序叠加 overlay：

```bash
source /opt/ros/humble/setup.bash              # 底层 underlay：系统 ROS
source ~/common_libs/install/setup.bash      # 中间层：公共库
source ~/my_robot/install/setup.bash         # 最上层 overlay：当前项目
```

顺序固定：**系统 → 公共库 → 当前项目**。

仅当存在真实依赖关系时才叠多层；无关项目不要叠在一起 source。

---

## 七、验证与排错

### 检查当前环境

```bash
echo $ROS_DISTRO              # 应输出 humble
echo $COLCON_PREFIX_PATH      # 应含当前工作空间的 install 路径
ros2 pkg list | grep 你的包名  # 确认包是否可见
```

### 常见问题


| 现象                | 可能原因            | 处理                                                   |
| ----------------- | --------------- | ---------------------------------------------------- |
| `ros2 run` 找不到包   | 未 source 对应工作空间 | `source ~/项目名/install/setup.bash`                    |
| 改了代码不生效           | 未重新编译           | `colcon build` 或 `colcon build --packages-select 包名` |
| `colcon build` 失败 | 缺少依赖            | `rosdep install --from-paths src --ignore-src -r -y` |
| 行为异常 / 版本不对       | 多个空间叠在一起 source | 新开终端，只 source 一个项目                                   |
| Python 改动需重启才生效   | 未用 symlink 安装   | `colcon build --symlink-install`                     |


### 修改代码后的标准流程

```bash
cd ~/competition_ws
colcon build --packages-select 你的包名   # 或 colcon build
source install/setup.bash               # 若已在 ws_xxx 函数里可省略
ros2 launch 你的包 你的launch文件
```

---

## 八、建议


| 做法             | 说明                                                                 |
| -------------- | ------------------------------------------------------------------ |
| 目录按项目命名        | 如 `competition_ws`、`urdf_lab`，便于识别                                 |
| 一个终端一个项目       | 跑 Gazebo / Nav2 时尤其重要，避免混环境                                        |
| Git 只管理 `src/` | `build/`、`install/`、`log/` 一般不提交                                   |
| 进项目先 build     | 拉代码或改 URDF 后记得 `colcon build`                                      |
| 依赖用 rosdep     | 每个工作空间根目录各自执行 rosdep install                                       |
| 与赛场对齐          | 训练环境 Ubuntu 22.04 + ROS 2 Humble + Gazebo 11，与 [项目环境与电脑配置要求](./项目环境与电脑配置要求.md) 保持一致 |


---

## 附录：单工作空间命令速查（文档 3.7）

```bash
sudo apt install -y python3-rosdep python3-colcon-common-extensions
sudo rosdep init          # 若已初始化，忽略报错
rosdep update

mkdir -p ~/ros2_ws/src && cd ~/ros2_ws
colcon build
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc   # 多项目时见第四节
source ~/.bashrc
```


| 命令                              | 作用                           |
| ------------------------------- | ---------------------------- |
| `mkdir -p ~/ros2_ws/src`        | 创建工作空间与源码目录                  |
| `colcon build`                  | 编译 `src/` 下所有包，生成 `install/` |
| `source .../install/setup.bash` | 加载工作空间，使 `ros2` 能找到你的包       |
| 写入 `~/.bashrc`                  | 新开终端自动加载（多项目时建议改为按需加载）       |


---

*文档版本：与 Ubuntu 22.04 + ROS 2 Humble 训练环境配套。*