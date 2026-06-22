# 题目 A：基于 urdf_tutorial 的机器人仿真模型修复与验证教程

> 依据《新疆维吾尔自治区第三届职业技能大赛——人工智能训练师（具身智能机器人）技术工作文件》（2026 年 6 月）中 **模块 A：机器人仿真模型修复与验证** 整理。  
> 本文档以 `/home/js/robot/HumanoidTeaching/src/urdf_tutorial` 为教学项目，默认环境为 **Ubuntu 22.04 + ROS 2 Humble**。内容尽量按课堂讲解的口吻来写，方便教师直接照着讲、学生跟着做。正式比赛内容及评分标准以正式赛题为准。

---

## 目录

| 章节 | 内容 |
| --- | --- |
| [一、课程定位](#一课程定位) | 题目 A 要求、教学目标、学生能力产出 |
| [二、项目整体认识](#二项目整体认识) | 项目目录、包结构、运行链路 |
| [三、环境准备与运行验证](#三环境准备与运行验证) | ROS 2 环境、构建、launch、RViz 验证 |
| [四、URDF 基础知识精讲](#四urdf-基础知识精讲) | robot、link、joint、origin、geometry、material |
| [五、项目文件逐个讲解](#五项目文件逐个讲解) | 8 个 URDF/xacro 文件的递进教学 |
| [六、题目 A 模型修复训练法](#六题目-a-模型修复训练法) | 阅读参考文件、定位错误、修复模型、验证结果 |
| [七、2 小时课堂实施方案](#七2-小时课堂实施方案) | 与竞赛模块 A 对齐的授课流程 |
| [八、典型故障与排查](#八典型故障与排查) | 语法、TF、尺寸、姿态、关节、mesh、xacro |
| [九、实操任务设计](#九实操任务设计) | 基础、进阶、综合三类训练任务 |
| [十、评分建议与提交规范](#十评分建议与提交规范) | 20 分评分表、提交物、报告模板 |
| [十一、教师授课提示](#十一教师授课提示) | 讲解重点、提问点、常见误区 |
| [附录 A：常用命令速查](#附录-a常用命令速查) | 构建、检查、显示、xacro、TF |
| [附录 B：URDF 标签速查](#附录-burdf-标签速查) | 高频标签与用途 |

---

## 一、课程定位

### 1.1 对应竞赛模块

技术工作文件中，模块 A 为：

| 模块 | 考核内容 | 时长 | 权重 |
| --- | --- | --- | --- |
| A | 机器人仿真模型修复与验证 | 2 小时 | 20% |

模块 A 的描述要点是：

> 选手需要根据给定的机器人仿真模型与参考文件，提取归纳关键信息，编写模型文件和脚本，运行仿真工具，验证模型是否修复成功。

这句话可以拆成 4 个训练能力：

1. **会读资料**：从参考文件中提取尺寸、结构、关节、坐标、传感器或执行器位置。
2. **会改模型**：能修改 URDF/xacro 中的 link、joint、origin、geometry、mesh、collision、inertial。
3. **会运行工具**：能使用 ROS 2 launch、RViz、TF、xacro、check_urdf 等工具验证模型。
4. **会写结论**：能说明发现了什么问题、改了哪里、如何证明修复成功。

### 1.2 为什么选择 urdf_tutorial

`urdf_tutorial` 是 ROS 官方风格的 URDF 入门项目，特点是文件少、递进清楚、错误点典型：

| 项目特点 | 教学价值 |
| --- | --- |
| 从单一 link 开始 | 适合零基础学生理解 URDF 最小结构 |
| 每个文件只增加少量概念 | 便于教师逐步讲解，不会一开始就被完整机器人模型淹没 |
| 包含视觉、关节、物理、xacro | 覆盖题目 A 中常见模型修复点 |
| 能直接用 RViz 可视化 | 学生可以马上看到修改效果 |
| 包含 mesh 文件 | 可以训练 package URI、资源路径、左右镜像等常见问题 |

### 1.3 学完后学生应具备的能力

学完这份教程后，我们希望学生不只是“看过 URDF”，而是真的能自己动手完成下面这些事：

1. 解释一个 ROS 2 包中 `package.xml`、`CMakeLists.txt`、`launch`、`rviz`、`urdf`、`meshes` 的作用。
2. 读懂 URDF 中 `robot`、`link`、`joint`、`origin`、`visual`、`collision`、`inertial` 的含义。
3. 画出机器人模型的 link-joint 树，也就是 TF 父子关系。
4. 修复常见模型错误，例如 link 重名、joint 断链、尺寸错误、坐标错位、关节类型错误、mesh 路径错误。
5. 使用 RViz 检查机器人模型是否完整显示、坐标系是否连通、可动关节是否正常。
6. 使用 `xacro` 将宏文件展开为 URDF，并检查展开后的模型是否符合预期。
7. 按竞赛要求整理提交文件、截图、运行命令和修复报告，把“我修好了”说清楚、证明清楚。

---

## 二、项目整体认识

### 2.1 项目位置

本教程使用的项目目录为：

```bash
/home/js/robot/HumanoidTeaching/src/urdf_tutorial
```

上课时可以直接把 `/home/js/robot/HumanoidTeaching` 当成 ROS 2 工作空间根目录，把 `src/urdf_tutorial` 当成工作空间里的一个功能包。

### 2.2 项目目录结构

核心结构如下：

```text
urdf_tutorial/
├── CMakeLists.txt
├── package.xml
├── README.md
├── launch/
│   └── display.launch.py
├── rviz/
│   └── urdf.rviz
├── meshes/
│   ├── l_finger.dae
│   └── l_finger_tip.dae
└── urdf/
    ├── 01-myfirst.urdf
    ├── 02-multipleshapes.urdf
    ├── 03-origins.urdf
    ├── 04-materials.urdf
    ├── 05-visual.urdf
    ├── 06-flexible.urdf
    ├── 07-physics.urdf
    └── 08-macroed.urdf.xacro
```

### 2.3 各目录作用

| 路径 | 作用 | 题目 A 训练点 |
| --- | --- | --- |
| `package.xml` | ROS 2 包描述文件，声明包名、版本、依赖、构建类型 | 判断包依赖是否完整 |
| `CMakeLists.txt` | 安装 launch、rviz、urdf、meshes 等资源 | 判断模型资源能否被 launch 找到 |
| `launch/display.launch.py` | 通用显示入口，加载指定模型并启动 RViz | 编写和使用启动脚本 |
| `rviz/urdf.rviz` | RViz 配置文件，显示 RobotModel 与 TF | 可视化验证模型 |
| `urdf/` | 存放机器人模型描述文件 | 模型阅读、修改和修复 |
| `meshes/` | 存放外部三维几何资源 | mesh 路径、左右镜像、资源加载排查 |

### 2.4 项目运行链路

这里先别急着打开 URDF 改参数，我们先把“一个模型文件是怎么跑起来的”讲清楚：

```text
ros2 launch urdf_tutorial display.launch.py model:=urdf/06-flexible.urdf
        │
        ▼
launch/display.launch.py
        │
        ▼
urdf_launch/display.launch.py
        │
        ├── 读取 urdf/06-flexible.urdf
        ├── 发布 /robot_description
        ├── 启动 robot_state_publisher
        ├── 启动 joint_state_publisher_gui
        └── 启动 RViz，加载 rviz/urdf.rviz
```

记住这几件事，后面排错会轻松很多：

1. URDF 文件不是单独“打开”就算验证完成了，它要通过 ROS 工具发布成 `/robot_description`。
2. RViz 的 RobotModel 插件从 `/robot_description` 读取模型。
3. TF 显示依赖 link-joint 关系和 joint state。
4. 可动关节需要 Joint State Publisher GUI 才能拖动查看效果。

---

## 三、环境准备与运行验证

### 3.1 进入工作空间

```bash
cd /home/js/robot/HumanoidTeaching
```

### 3.2 安装常用依赖

你的环境是 ROS 2 Humble。不同电脑可能已经装过一部分工具，训练前可以先确认下面这些包在不在：

```bash
sudo apt update
sudo apt install -y \
  python3-colcon-common-extensions \
  ros-${ROS_DISTRO}-xacro \
  ros-${ROS_DISTRO}-robot-state-publisher \
  ros-${ROS_DISTRO}-joint-state-publisher \
  ros-${ROS_DISTRO}-joint-state-publisher-gui \
  ros-${ROS_DISTRO}-rviz2 \
  ros-${ROS_DISTRO}-urdf-launch \
  liburdfdom-tools
```

如果使用的是 ROS 2 Humble，`ROS_DISTRO` 通常会输出 `humble`。可以用下面这个命令确认：

```bash
echo $ROS_DISTRO
```

如果输出为空，说明当前终端还没加载 ROS 环境，先执行：

```bash
source /opt/ros/humble/setup.bash
```

为了以后每次打开终端都自动加载 Humble，也可以把它写进 `~/.bashrc`：

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 3.3 构建项目

```bash
cd /home/js/robot/HumanoidTeaching
colcon build --packages-select urdf_tutorial
```

构建成功后加载工作空间：

```bash
source install/setup.bash
```

### 3.4 运行默认模型

```bash
ros2 launch urdf_tutorial display.launch.py
```

默认模型为：

```text
urdf/01-myfirst.urdf
```

正常现象：

1. 启动 RViz。
2. 显示 Grid。
3. 显示一个蓝灰色或默认颜色的圆柱体。
4. Fixed Frame 为 `base_link`。

### 3.5 运行指定模型

运行完整视觉模型：

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/05-visual.urdf
```

运行可动关节模型：

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/06-flexible.urdf
```

运行物理属性模型：

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/07-physics.urdf
```

运行 xacro 模型：

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/08-macroed.urdf.xacro
```

### 3.6 检查 URDF 语法

```bash
check_urdf src/urdf_tutorial/urdf/07-physics.urdf
```

正常时会输出机器人 link、joint 信息。若 XML 标签错误、父子 link 不存在、结构不合法，会报错。

### 3.7 展开 xacro

```bash
xacro src/urdf_tutorial/urdf/08-macroed.urdf.xacro > /tmp/macroed.urdf
check_urdf /tmp/macroed.urdf
```

这里要提醒学生一句：不能只说“xacro 文件没报错”。xacro 只是模板，真正拿去给机器人系统用的是展开后的 URDF，所以还要看展开后 link 和 joint 数量、名字、父子关系是否对。

---

## 四、URDF 基础知识精讲

### 4.1 URDF 是什么

URDF 全称为 Unified Robot Description Format，即统一机器人描述格式。它使用 XML 语法描述机器人结构，主要包含：

1. 机器人有哪些刚体部件，也就是 `link`。
2. 部件之间如何连接，也就是 `joint`。
3. 每个部件长什么样，也就是 `visual`。
4. 每个部件如何参与碰撞，也就是 `collision`。
5. 每个部件在物理仿真中的质量和惯量，也就是 `inertial`。

### 4.2 最小 URDF 结构

`01-myfirst.urdf` 的核心结构是：

```xml
<robot name="myfirst">
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="0.6" radius="0.2"/>
      </geometry>
    </visual>
  </link>
</robot>
```

讲解重点：

| 标签 | 含义 |
| --- | --- |
| `robot` | 整个机器人模型的根标签 |
| `name` | 名称，便于工具识别 |
| `link` | 一个刚体坐标系，可以理解为机器人某个零件 |
| `visual` | 视觉模型，决定 RViz 中看到的外观 |
| `geometry` | 几何形状 |
| `cylinder` | 圆柱体，使用 `length` 和 `radius` 描述尺寸 |

### 4.3 link 与 joint 的关系

URDF 里 `link` 只是一个个零件坐标系，光写出来还不会自动连在一起；要靠 `joint` 把它们接成一棵树。

```xml
<joint name="base_to_right_leg" type="fixed">
  <parent link="base_link"/>
  <child link="right_leg"/>
</joint>
```

讲解重点：

1. `parent` 是父 link。
2. `child` 是子 link。
3. `joint` 表示子 link 如何挂在父 link 上。
4. 整个机器人模型应该形成一棵树，不能断开，不能循环。

### 4.4 origin 的两种含义

这是教学中最重要、也最容易出错的地方。

#### visual origin

```xml
<link name="right_leg">
  <visual>
    <geometry>
      <box size="0.6 0.1 0.2"/>
    </geometry>
    <origin rpy="0 1.57075 0" xyz="0 0 -0.3"/>
  </visual>
</link>
```

`visual` 里面的 `origin` 表示：几何体相对于本 link 坐标系的位置和姿态。

#### joint origin

```xml
<joint name="base_to_right_leg" type="fixed">
  <parent link="base_link"/>
  <child link="right_leg"/>
  <origin xyz="0 -0.22 0.25"/>
</joint>
```

`joint` 里面的 `origin` 表示：child link 坐标系相对于 parent link 坐标系的位置和姿态。

课堂判断方法：

1. 如果整个子部件挂错位置，优先检查 joint origin。
2. 如果 link 坐标系位置对，但几何体在 link 周围偏了，检查 visual origin。
3. 如果碰撞体和视觉体不重合，检查 collision origin 是否和 visual origin 一致。

### 4.5 xyz 与 rpy

`xyz` 表示平移，单位通常是米：

```text
xyz="x y z"
```

`rpy` 表示旋转，单位是弧度：

```text
rpy="roll pitch yaw"
```

常见角度换算：

| 角度 | 弧度近似值 | 用途示例 |
| --- | --- | --- |
| 90° | `1.57075` 或 `1.5708` | 把圆柱或长方体转向 |
| 180° | `3.1415` 或 `3.14159` | 左右镜像、翻转夹爪 |
| 45° | `0.7854` | 倾斜安装 |

### 4.6 joint 类型

| joint 类型 | 含义 | 是否需要 axis | 是否需要 limit |
| --- | --- | --- | --- |
| `fixed` | 固定连接，不运动 | 否 | 否 |
| `continuous` | 连续旋转，无角度上下限 | 是 | 一般不需要上下限 |
| `revolute` | 有限角度旋转 | 是 | 是 |
| `prismatic` | 沿轴线平移 | 是或默认轴 | 是 |

项目中的典型例子：

| 文件 | 关节 | 类型 | 教学重点 |
| --- | --- | --- | --- |
| `06-flexible.urdf` | 轮子关节 | `continuous` | 轮子可连续转动 |
| `06-flexible.urdf` | 夹爪关节 | `revolute` | 有开合角度限制 |
| `06-flexible.urdf` | 夹爪伸缩杆 | `prismatic` | 有平移范围 |
| `06-flexible.urdf` | 头部 | `continuous` | 可绕 z 轴旋转 |

### 4.7 geometry：几何形状到底怎么读

`geometry` 是用来说明“这个 link 看起来是什么形状”的。它本身只是一个容器，真正的形状由里面的 `box`、`cylinder`、`sphere` 或 `mesh` 决定。

课堂上可以这样讲：

> `geometry` 就像是在说：这个零件用什么形状画出来？是盒子、圆柱、球，还是外部三维模型？

#### 4.7.1 box：长方体

项目中腿和底盘常用 `box`：

```xml
<box size="0.6 0.1 0.2"/>
```

`size` 后面有 3 个数：

| 属性 | 含义 | 在例子中的值 |
| --- | --- | --- |
| 第 1 个数 | x 方向长度 | `0.6` m |
| 第 2 个数 | y 方向宽度 | `0.1` m |
| 第 3 个数 | z 方向高度 | `0.2` m |

也就是说：

```text
size="0.6 0.1 0.2"
```

表示这个长方体在 x 方向长 `0.6` 米，在 y 方向宽 `0.1` 米，在 z 方向高 `0.2` 米。

注意：`box` 默认是以当前 link 坐标系原点为中心放置的。如果没有写 `origin`，长方体中心就在 link 坐标系原点。

常见错误：

1. 把单位当成厘米。例如把 `0.6` 理解成 0.6 厘米，这是错的，URDF 里通常按米理解。
2. 把 `size` 顺序写反。例如腿本来应该在 x 方向长，却把长写到了 z 方向。
3. 只改 `box size`，忘了同步修改 `collision` 里的尺寸，导致视觉模型和碰撞模型不一致。

#### 4.7.2 cylinder：圆柱体

项目中身体和轮子常用 `cylinder`：

```xml
<cylinder length="0.6" radius="0.2"/>
```

这里有两个核心属性：

| 属性 | 含义 | 在例子中的值 |
| --- | --- | --- |
| `length` | 圆柱高度，也就是圆柱轴线方向的长度 | `0.6` m |
| `radius` | 圆柱半径 | `0.2` m |

注意：URDF 里的 cylinder 默认沿 **z 轴** 方向放置。也就是说，如果不写旋转，圆柱是“竖着”的。

所以轮子经常会写：

```xml
<origin rpy="1.57075 0 0" xyz="0 0 0"/>
<geometry>
  <cylinder length="0.1" radius="0.035"/>
</geometry>
```

这里的意思是：

1. `cylinder length="0.1"`：轮子的厚度是 `0.1` 米。
2. `radius="0.035"`：轮子半径是 `0.035` 米，所以直径是 `0.07` 米。
3. `rpy="1.57075 0 0"`：把默认沿 z 轴的圆柱转一下，让它变成轮子的方向。

常见错误：

1. 忘记旋转圆柱，轮子会“竖着站起来”。
2. 把半径当直径填。例如参考文件说轮子直径 `0.07` m，URDF 里应该写 `radius="0.035"`。
3. `length` 和 `radius` 写反，轮子会变成很长的滚筒或很薄的片。

#### 4.7.3 sphere：球体

项目中头部用 `sphere`：

```xml
<sphere radius="0.2"/>
```

`radius` 表示球半径。这个很直观：`radius="0.2"` 表示球半径为 `0.2` 米，直径就是 `0.4` 米。

常见错误：

1. 参考文件给的是直径，学生直接填到 `radius`，模型会变大一倍。
2. 球体位置看起来不对时，问题通常不在 `sphere` 本身，而在连接它的 joint origin。

### 4.8 mesh：外部三维模型怎么读

`mesh` 用来引用外部三维模型文件。比如项目中的夹爪不是用简单的盒子或圆柱拼出来的，而是引用了 `.dae` 文件：

```xml
<mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
```

这句要拆开讲：

| 片段 | 含义 |
| --- | --- |
| `mesh` | 使用外部三维模型 |
| `filename` | 外部模型文件的位置 |
| `package://` | 从 ROS 包中查找资源，而不是从硬盘绝对路径查找 |
| `urdf_tutorial` | 包名 |
| `meshes/l_finger.dae` | 包里面的模型文件路径 |

所以：

```text
package://urdf_tutorial/meshes/l_finger.dae
```

可以读成：

> 去 `urdf_tutorial` 这个 ROS 包里，找到 `meshes` 文件夹下的 `l_finger.dae` 文件。

项目中还有：

```xml
<mesh filename="package://urdf_tutorial/meshes/l_finger_tip.dae"/>
```

它表示夹爪指尖的模型。

#### 为什么不要写绝对路径

不推荐这样写：

```xml
<mesh filename="/home/js/robot/HumanoidTeaching/src/urdf_tutorial/meshes/l_finger.dae"/>
```

原因很简单：这只在当前电脑当前目录下能用。换到裁判机、同学电脑或重新放置工作空间后，路径就可能失效。

推荐写法是：

```xml
<mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
```

这样只要 ROS 能找到 `urdf_tutorial` 这个包，就能找到 mesh 文件。

#### mesh 可以加 scale

本项目中的 mesh 没写 `scale`，表示按模型文件原始尺寸加载。但在其他题目里可能看到：

```xml
<mesh filename="package://my_robot/meshes/camera.stl" scale="0.001 0.001 0.001"/>
```

`scale` 表示缩放比例：

| 写法 | 含义 |
| --- | --- |
| `scale="1 1 1"` | 原始大小 |
| `scale="0.001 0.001 0.001"` | x、y、z 都缩小到原来的千分之一 |
| `scale="2 1 1"` | x 方向放大 2 倍，y 和 z 不变 |

常见错误：

1. mesh 文件路径写错，RViz 里夹爪不显示。
2. 包名写错，例如把 `urdf_tutorial` 写成 `urdf-tutorial`。
3. 文件名大小写写错，Linux 下路径大小写敏感。
4. mesh 原始单位不是米，忘记加 `scale`，模型会大得离谱或小到看不见。
5. 左右夹爪复用同一个 mesh 时，忘记通过 `rpy` 做翻转，导致两边方向一样。

### 4.9 visual、collision、inertial：看得见、碰得到、算得动

从 `07-physics.urdf` 开始，每个 link 不只是有 `visual`，还增加了 `collision` 和 `inertial`。这三个标签要分清：

| 标签 | 作用 | 可以怎么理解 |
| --- | --- | --- |
| `visual` | RViz/Gazebo 中看到的外观 | 看得见 |
| `collision` | 物理碰撞时使用的形状 | 碰得到 |
| `inertial` | 质量和惯量 | 算得动 |

课堂上可以这样比喻：

> `visual` 是外观皮肤，`collision` 是物理边界，`inertial` 是重量和转动特性。

#### 4.9.1 visual：视觉模型

例子：

```xml
<visual>
  <geometry>
    <cylinder length="0.6" radius="0.2"/>
  </geometry>
  <material name="blue"/>
</visual>
```

解释：

1. `visual` 只负责“看起来是什么样”。
2. `geometry` 说明形状。
3. `material` 说明颜色或材质。
4. RViz 中主要显示的就是 visual。

注意：只有 visual 的模型，在 RViz 中能显示，但进入物理仿真时可能不够用。

#### 4.9.2 collision：碰撞模型

例子：

```xml
<collision>
  <geometry>
    <cylinder length="0.6" radius="0.2"/>
  </geometry>
</collision>
```

解释：

1. `collision` 负责物理碰撞计算。
2. 它可以和 `visual` 一样，也可以比 `visual` 简化。
3. 对复杂 mesh 来说，collision 常常用简单 box/cylinder 代替，这样仿真更稳定、更快。

常见错误：

1. 只写 visual，不写 collision，Gazebo 中碰撞行为可能异常。
2. visual 改了尺寸，collision 忘了改，结果看起来对，但碰撞边界不对。
3. collision 的 origin 和 visual 的 origin 不一致，导致“看起来没碰到，实际已经碰到了”。

#### 4.9.3 inertial：惯性模型

例子：

```xml
<inertial>
  <mass value="0.05"/>
  <inertia ixx="1e-3" ixy="0.0" ixz="0.0" iyy="1e-3" iyz="0.0" izz="1e-3"/>
</inertial>
```

这一段很多学生会看不懂，要拆开讲。

### 4.10 mass：质量怎么读

`mass` 表示 link 的质量：

```xml
<mass value="0.05"/>
```

这里的：

```text
value="0.05"
```

表示这个 link 的质量是 `0.05` 千克，也就是 50 克。

再看项目里的几个例子：

| 位置 | 写法 | 含义 |
| --- | --- | --- |
| 身体 `base_link` | `<mass value="10"/>` | 身体质量 10 kg |
| 轮子 | `<mass value="1"/>` | 单个轮子质量 1 kg |
| 夹爪杆 | `<mass value="0.05"/>` | 夹爪杆质量 0.05 kg |
| 指尖 | `<mass value="0.05"/>` | 指尖质量 0.05 kg |

课堂口语解释：

> `mass value` 就是在告诉仿真器：这个零件有多重。不是颜色，不是尺寸，而是质量。

常见错误：

1. 把 `value="0.05"` 理解成 0.05 米，这是错的。`mass` 的单位是千克。
2. 质量写成 0，物理仿真可能不稳定。
3. 小零件质量写得比主体还大，仿真运动会很奇怪。
4. 复制粘贴时所有 link 都写成同一个质量，虽然能跑，但不符合真实机器人。

### 4.11 inertia：惯量矩阵怎么先入门理解

`inertia` 是惯量，也就是物体抵抗旋转变化的能力。它比质量更难理解，但竞赛训练阶段可以先掌握“会读、会检查、会避免明显错误”。

例子：

```xml
<inertia ixx="1e-3" ixy="0.0" ixz="0.0" iyy="1e-3" iyz="0.0" izz="1e-3"/>
```

这些属性组成一个 3×3 惯量矩阵：

```text
[ ixx  ixy  ixz ]
[ ixy  iyy  iyz ]
[ ixz  iyz  izz ]
```

每个属性可以这样理解：

| 属性 | 入门理解 |
| --- | --- |
| `ixx` | 绕 x 轴转动时的惯量 |
| `iyy` | 绕 y 轴转动时的惯量 |
| `izz` | 绕 z 轴转动时的惯量 |
| `ixy` | x 和 y 之间的耦合项 |
| `ixz` | x 和 z 之间的耦合项 |
| `iyz` | y 和 z 之间的耦合项 |

项目中统一用了：

```text
ixx="1e-3" iyy="1e-3" izz="1e-3"
ixy="0.0" ixz="0.0" iyz="0.0"
```

`1e-3` 是科学计数法，表示：

```text
1e-3 = 0.001
```

课堂上可以这样讲：

> 这份教程项目的惯量值是简化写法，目的不是精确模拟真实机器人，而是让模型具备基本物理属性。正式做复杂机器人时，惯量最好根据几何尺寸和质量计算，或者由 CAD/仿真工具导出。

常见错误：

1. 忘记写 `inertia`，仿真器可能警告或行为异常。
2. 惯量写成负数，这是不合理的。
3. 惯量全写 0，物理仿真容易出问题。
4. 质量和惯量严重不匹配，例如 10 kg 的主体惯量却写得非常小。

### 4.12 axis 和 limit：关节为什么会按某个方向动

在 `06-flexible.urdf` 里会看到：

```xml
<joint name="left_gripper_joint" type="revolute">
  <axis xyz="0 0 1"/>
  <limit effort="1000.0" lower="0.0" upper="0.548" velocity="0.5"/>
  <origin rpy="0 0 0" xyz="0.2 0.01 0"/>
  <parent link="gripper_pole"/>
  <child link="left_gripper"/>
</joint>
```

这段可以拆成 5 件事：

| 标签/属性 | 含义 |
| --- | --- |
| `type="revolute"` | 这是一个有限角度旋转关节 |
| `<axis xyz="0 0 1"/>` | 绕 z 轴旋转 |
| `lower="0.0"` | 最小角度是 0 rad |
| `upper="0.548"` | 最大角度是 0.548 rad，大约 31.4° |
| `velocity="0.5"` | 关节最大速度参考值 |
| `effort="1000.0"` | 关节最大力矩或力的参考值 |

#### axis xyz 怎么看

`axis xyz` 表示关节运动方向：

| 写法 | 含义 |
| --- | --- |
| `<axis xyz="1 0 0"/>` | 绕 x 轴转，或沿 x 轴平移 |
| `<axis xyz="0 1 0"/>` | 绕 y 轴转，或沿 y 轴平移 |
| `<axis xyz="0 0 1"/>` | 绕 z 轴转，或沿 z 轴平移 |
| `<axis xyz="0 0 -1"/>` | 绕 z 轴反方向转 |

对于 `revolute` 和 `continuous`，axis 表示“绕哪根轴转”。  
对于 `prismatic`，axis 表示“沿哪根轴平移”。

#### limit 怎么看

`limit` 里常见 4 个属性：

| 属性 | 含义 | 单位 |
| --- | --- | --- |
| `lower` | 最小位置 | 旋转关节为 rad，平移关节为 m |
| `upper` | 最大位置 | 旋转关节为 rad，平移关节为 m |
| `velocity` | 最大速度 | rad/s 或 m/s |
| `effort` | 最大力矩或力 | N·m 或 N，入门阶段先理解为“出力上限” |

项目里的伸缩杆：

```xml
<joint name="gripper_extension" type="prismatic">
  <parent link="base_link"/>
  <child link="gripper_pole"/>
  <limit effort="1000.0" lower="-0.38" upper="0" velocity="0.5"/>
  <origin rpy="0 0 0" xyz="0.19 0 0.2"/>
</joint>
```

这表示：

1. `type="prismatic"`：这是平移关节，不是旋转关节。
2. `lower="-0.38"`：最多可以往负方向移动 `0.38` 米。
3. `upper="0"`：最大位置是 0 米。
4. `velocity="0.5"`：最大速度参考值为 `0.5` m/s。

常见错误：

1. `axis` 写反，夹爪开合方向反了。
2. `revolute` 忘记写 `limit`，解析或控制时会出问题。
3. `lower` 比 `upper` 大，运动范围不合理。
4. 把角度值当成度数写进去。例如想写 90°，不能写 `90`，应该写约 `1.5708`。
5. `prismatic` 的上下限单位是米，不是厘米。

### 4.13 material：颜色和材质怎么读

项目里先定义材质：

```xml
<material name="blue">
  <color rgba="0 0 0.8 1"/>
</material>
```

再使用材质：

```xml
<material name="blue"/>
```

`rgba` 有 4 个数：

| 位置 | 含义 | 取值范围 |
| --- | --- | --- |
| 第 1 个 | Red，红色 | 0 到 1 |
| 第 2 个 | Green，绿色 | 0 到 1 |
| 第 3 个 | Blue，蓝色 | 0 到 1 |
| 第 4 个 | Alpha，透明度 | 0 到 1 |

例如：

```xml
<color rgba="0 0 0.8 1"/>
```

表示红色 0、绿色 0、蓝色 0.8、不透明度 1，所以显示为蓝色。

再比如：

```xml
<color rgba="1 1 1 1"/>
```

表示白色。

```xml
<color rgba="0 0 0 1"/>
```

表示黑色。

课堂提醒：

> 材质主要帮助我们看模型、分辨左右、检查部件有没有装反。它一般不是题目 A 里最优先修的内容，除非题目明确要求颜色或材质。

常见错误：

1. 只写 `<material name="blue"/>`，但前面没有定义 `blue`。
2. `rgba` 超出 0 到 1 的范围。
3. alpha 写成 0，模型可能变透明，看起来像没显示。

### 4.14 读一个完整 link 的方法

看到 `07-physics.urdf` 里这种较长的 link，不要慌：

```xml
<link name="right_tip">
  <visual>
    <origin rpy="-3.1415 0 0" xyz="0.09137 0.00495 0"/>
    <geometry>
      <mesh filename="package://urdf_tutorial/meshes/l_finger_tip.dae"/>
    </geometry>
  </visual>
  <collision>
    <geometry>
      <mesh filename="package://urdf_tutorial/meshes/l_finger_tip.dae"/>
    </geometry>
    <origin rpy="-3.1415 0 0" xyz="0.09137 0.00495 0"/>
  </collision>
  <inertial>
    <mass value="0.05"/>
    <inertia ixx="1e-3" ixy="0.0" ixz="0.0" iyy="1e-3" iyz="0.0" izz="1e-3"/>
  </inertial>
</link>
```

可以按下面顺序读：

1. 先看 `link name="right_tip"`：这是右夹爪指尖这个零件。
2. 再看 `visual`：它在 RViz 中显示为 `l_finger_tip.dae` 这个 mesh。
3. 看 `visual origin`：这个 mesh 相对 `right_tip` 坐标系有位置和姿态偏移。
4. 看 `collision`：碰撞模型也用了同一个 mesh。
5. 看 `collision origin`：碰撞模型的位置姿态和视觉模型保持一致。
6. 看 `mass value="0.05"`：这个零件质量是 0.05 kg。
7. 看 `inertia`：这个零件有一组简化惯量参数。

用一句话总结：

> 这个 link 叫 `right_tip`，外观和碰撞都用 `l_finger_tip.dae`，它被翻转并偏移到指定位置，质量是 50 克，带有简化惯量。

### 4.15 学生读 URDF 的固定口诀

读任何一个 URDF 文件时，可以按这个口诀：

```text
先看 robot 名，
再数 link 数量，
joint 连父子，
origin 定位置，
geometry 看形状，
material 看颜色，
axis 看方向，
limit 看范围，
collision 看碰撞，
mass/inertia 看物理，
mesh 路径最后别写错。
```

课堂上可以让学生每读一个文件都按这套顺序过一遍。刚开始会慢，但练几次以后，看到复杂模型也不会乱。

---

## 五、项目文件逐个讲解

### 5.1 README.md

`README.md` 提供 ROS 官方 URDF 教程入口。课堂中不用逐字讲，但要告诉学生：

1. 本项目不是业务系统，而是 URDF 学习包。
2. 训练顺序应按照文件编号从 `01` 到 `08`。
3. 后续如果需要扩展 Gazebo 仿真，可继续学习 `urdf_sim_tutorial`。

### 5.2 package.xml

核心内容：

```xml
<name>urdf_tutorial</name>
<buildtool_depend>ament_cmake</buildtool_depend>
<exec_depend>urdf_launch</exec_depend>
```

讲解重点：

| 字段 | 作用 |
| --- | --- |
| `<name>` | 包名，launch 时使用 `urdf_tutorial` |
| `<buildtool_depend>` | 构建工具依赖 |
| `<exec_depend>` | 运行时依赖，这里依赖 `urdf_launch` |
| `<export>` | 声明构建类型和 Gazebo 模型路径 |

题目 A 可能考查：

1. 包名写错导致 `ros2 launch` 找不到包。
2. 运行依赖缺失导致 launch 文件找不到。
3. mesh 或模型资源路径未正确安装。

### 5.3 CMakeLists.txt

核心内容：

```cmake
install(
  DIRECTORY images launch meshes rviz urdf
  DESTINATION share/${PROJECT_NAME}
)
```

讲解重点：

1. 这个包没有 C++/Python 节点，主要安装资源文件。
2. `launch`、`meshes`、`rviz`、`urdf` 这些资源要安装到包的 share 目录，launch 才能稳定找到它们。
3. 如果新建了目录或文件，但没有被安装，launch 后可能找不到资源。

题目 A 可能考查：

1. 新增模型文件后未重新构建。
2. 新增资源目录后未加入 install 规则。
3. 使用绝对路径而不是 `package://` 导致换机器无法运行。

### 5.4 launch/display.launch.py

核心逻辑：

```python
urdf_tutorial_path = FindPackageShare('urdf_tutorial')
default_model_path = PathJoinSubstitution(['urdf', '01-myfirst.urdf'])
default_rviz_config_path = PathJoinSubstitution([urdf_tutorial_path, 'rviz', 'urdf.rviz'])
```

继续向 `urdf_launch` 传参：

```python
launch_arguments={
    'urdf_package': 'urdf_tutorial',
    'urdf_package_path': LaunchConfiguration('model'),
    'rviz_config': LaunchConfiguration('rvizconfig'),
    'jsp_gui': LaunchConfiguration('gui')
}.items()
```

课堂讲解：

1. `model` 参数是相对于 `urdf_tutorial` 包的路径，例如 `urdf/06-flexible.urdf`。
2. `rvizconfig` 参数指定 RViz 配置文件。
3. `gui` 控制是否启动关节状态发布 GUI。
4. 本 launch 文件本身不解析 URDF，而是把任务交给 `urdf_launch` 包。

常用命令：

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/06-flexible.urdf
```

关闭关节 GUI：

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/06-flexible.urdf gui:=false
```

### 5.5 rviz/urdf.rviz

该配置启用了：

| RViz 插件 | 作用 |
| --- | --- |
| Grid | 显示地面网格，辅助观察尺寸与位置 |
| RobotModel | 从 `/robot_description` 显示机器人模型 |
| TF | 显示坐标系树 |

固定坐标系：

```yaml
Fixed Frame: base_link
```

教学要求：

1. 学生要会看 RobotModel 是否报错。
2. 学生要会打开和关闭 TF 显示。
3. 学生要会判断某个 link 是否没有接入 TF 树。

### 5.6 meshes/

该目录包含：

```text
meshes/l_finger.dae
meshes/l_finger_tip.dae
```

URDF 中引用方式：

```xml
<mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
```

讲解重点：

1. `package://urdf_tutorial/...` 表示从 ROS 包路径查找资源。
2. 提交作品时尽量不要使用本机绝对路径，例如 `/home/js/.../meshes/...`，否则换一台电脑就容易找不到文件。
3. 左右夹爪可以复用同一个 mesh，通过 `origin rpy` 实现镜像。

---

## 六、题目 A 模型修复训练法

### 6.1 竞赛式解题流程

做模型修复题时，可以让学生按下面这个顺序来。这个顺序很重要，因为先把结构修通，再去调外观，会少走很多弯路：

```text
第一步：读任务书和参考文件
第二步：列出应有部件、尺寸、关节、坐标
第三步：运行原始模型，记录现象
第四步：检查 URDF/xacro 语法
第五步：检查 link-joint 树
第六步：逐项修复模型
第七步：运行 RViz/TF/GUI 验证
第八步：整理提交文件和修复报告
```

### 6.2 参考文件信息提取表

遇到正式题目时，先别急着改文件。可以让学生先把任务书里的关键信息整理出来：

| 信息类别 | 需要提取什么 | 对应 URDF 位置 |
| --- | --- | --- |
| 机器人名称 | 模型名称、包名 | `<robot name="">`、`package.xml` |
| 主体尺寸 | 长、宽、高、半径 | `<box size="">`、`<cylinder radius="" length="">` |
| 部件列表 | 腿、轮子、头、夹爪、传感器等 | `<link name="">` |
| 连接关系 | 谁连接谁，父子关系 | `<joint>`、`<parent>`、`<child>` |
| 安装位置 | 相对坐标 | `<origin xyz="">` |
| 安装姿态 | 旋转角度 | `<origin rpy="">` |
| 关节类型 | 固定、旋转、平移、连续旋转 | `<joint type="">` |
| 运动范围 | 上限、下限、速度、力矩 | `<limit>` |
| 几何资源 | mesh 文件路径、缩放 | `<mesh filename="">` |
| 物理属性 | 质量、惯量、碰撞体 | `<collision>`、`<inertial>` |

### 6.3 模型修复优先级

修模型时可以按这个优先级来，别一上来就调颜色、材质这类外观细节：

1. **先修 XML 语法**：文件要能被解析，否则后面都跑不起来。
2. **再修 link/joint 树**：所有 link 要连成一棵树，不能断，也不能乱接。
3. **再修尺寸和位置**：确保主要部件在正确位置。
4. **再修姿态和镜像**：轮子朝向、夹爪左右、传感器方向。
5. **再修关节运动**：关节类型、轴向、运动范围。
6. **最后补物理属性**：collision、inertial、mass、inertia。
7. **最后整理 xacro**：用宏减少重复，保证展开结果正确。

### 6.4 验证要留下证据

题目 A 不是“看起来差不多”就结束。课堂上要训练学生留下证据：命令能跑通、RViz 能显示、TF 是连通的、关节能按预期动。

| 验证内容 | 工具 | 通过标准 |
| --- | --- | --- |
| URDF 语法 | `check_urdf` | 无 XML/URDF 解析错误 |
| xacro 展开 | `xacro` | 能生成合法 URDF |
| 模型显示 | RViz RobotModel | 部件完整显示，无资源加载错误 |
| TF 连通 | RViz TF 或 `view_frames` | 所有 link 接入同一棵树 |
| 关节运动 | joint_state_publisher_gui | 可动关节能按预期运动 |
| 尺寸位置 | RViz 网格、参考数值 | 与参考文件一致或误差在要求范围 |
| 提交复现 | 命令记录 | 裁判能按提交命令复现结果 |

---

## 七、2 小时课堂实施方案

本节按竞赛模块 A 的 2 小时时长设计，适合一次完整训练课。

### 7.1 时间安排

| 时间 | 环节 | 教师任务 | 学生产出 |
| --- | --- | --- | --- |
| 0-10 分钟 | 导入题目 A | 讲技术文件中模块 A 的要求 | 明确训练目标 |
| 10-25 分钟 | 项目结构导览 | 讲包结构、launch、rviz、urdf、meshes | 能说出各目录作用 |
| 25-45 分钟 | URDF 基础 | 讲 `01` 到 `04` | 能解释 link、joint、origin、material |
| 45-65 分钟 | 完整视觉模型 | 讲 `05-visual.urdf` | 画出 link-joint 树 |
| 65-85 分钟 | 可动关节 | 讲 `06-flexible.urdf` | 能拖动 GUI 验证关节 |
| 85-100 分钟 | 物理和 xacro | 讲 `07`、`08` | 理解 collision/inertial/xacro |
| 100-115 分钟 | 错误模型修复 | 发放或现场制造错误 | 完成至少 3 类错误修复 |
| 115-120 分钟 | 提交与点评 | 检查命令、截图、报告 | 完成提交包 |

### 7.2 教师课堂演示顺序

教师演示时可以依次运行：

```bash
cd /home/js/robot/HumanoidTeaching
source install/setup.bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/01-myfirst.urdf
```

然后依次替换模型：

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/02-multipleshapes.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/03-origins.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/04-materials.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/05-visual.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/06-flexible.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/07-physics.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/08-macroed.urdf.xacro
```

每换一个模型，只讲“新增了什么能力”，不要把全部 XML 逐行念完。

### 7.3 学生课堂记录模板

可以让学生边看边填这张表。表填得越清楚，后面做修复题越快：

| 模型文件 | 新增知识点 | 我观察到的 RViz 现象 | 可能出错点 |
| --- | --- | --- | --- |
| `01-myfirst.urdf` | 单 link | 一个圆柱 | geometry 尺寸 |
| `02-multipleshapes.urdf` | fixed joint | 多一个腿 | parent/child 写错 |
| `03-origins.urdf` | origin | 腿移动到一侧 | xyz/rpy 混淆 |
| `04-materials.urdf` | material | 有颜色和左右腿 | material 名称错误 |
| `05-visual.urdf` | mesh 和完整结构 | 显示完整机器人 | mesh 路径、TF 断裂 |
| `06-flexible.urdf` | 可动关节 | GUI 可拖动 | axis/limit 错误 |
| `07-physics.urdf` | collision/inertial | 外观变化不大 | 仿真属性缺失 |
| `08-macroed.urdf.xacro` | xacro 宏 | 展开后同样显示 | 宏参数错误 |

---

## 八、典型故障与排查

### 8.1 XML 语法错误

常见原因：

1. 标签没有闭合。
2. 属性引号缺失。
3. 标签嵌套顺序错误。
4. 多了非法字符。

示例错误：

```xml
<cylinder length="0.6" radius="0.2">
```

正确写法：

```xml
<cylinder length="0.6" radius="0.2"/>
```

排查命令：

```bash
check_urdf src/urdf_tutorial/urdf/01-myfirst.urdf
```

### 8.2 link 或 joint 命名错误

常见原因：

1. `parent` 引用了不存在的 link。
2. `child` 引用了不存在的 link。
3. 两个 link 使用同一个名称。
4. 两个 joint 使用同一个名称。

错误示例：

```xml
<parent link="base"/>
```

如果模型中实际 link 名称是 `base_link`，就会导致连接失败。

修复原则：

1. 所有 link 名称都要唯一。
2. 所有 joint 名称也要唯一。
3. `parent`/`child` 要引用真实存在的 link。
4. 最后整个模型要连通，不能有“孤零零”的部件。

### 8.3 坐标位置错误

现象：

1. 腿插到身体中间。
2. 左右腿距离不对。
3. 轮子漂浮或埋入底盘。
4. 头部、夹爪安装位置不合理。

排查方法：

1. 先看 joint origin。
2. 再看 visual origin。
3. 使用 RViz Grid 判断大致距离。
4. 对照参考尺寸表逐个核对。

示例：

```xml
<origin xyz="0 -0.22 0.25"/>
```

含义是：子 link 坐标系相对父 link，在 y 方向偏移 `-0.22` 米，在 z 方向偏移 `0.25` 米。

### 8.4 姿态方向错误

现象：

1. 轮子横竖方向不对。
2. 夹爪一边正常，一边翻转错误。
3. 长方体腿朝向不对。

典型写法：

```xml
<origin rpy="1.57075 0 0" xyz="0 0 0"/>
```

表示绕 x 轴旋转约 90°。

排查时可以这样做：

1. 只改一个角度，观察变化。
2. 不要同时改 `xyz` 和 `rpy`，否则不容易判断原因。
3. 对称结构要检查左右是否符号相反。

### 8.5 关节不可动或运动方向错误

现象：

1. GUI 中没有某个关节。
2. 拖动滑块模型不动。
3. 夹爪左右开合方向相反。
4. 平移关节超出合理范围。

检查项：

| 检查项 | 正确要求 |
| --- | --- |
| joint type | 可动关节不能写成 `fixed` |
| axis | 旋转或平移方向要符合参考模型 |
| limit lower/upper | `revolute` 和 `prismatic` 需要合理上下限 |
| parent/child | 父子关系不能反 |

### 8.6 mesh 路径错误

错误示例：

```xml
<mesh filename="/home/js/robot/HumanoidTeaching/src/urdf_tutorial/meshes/l_finger.dae"/>
```

不推荐这样写，因为换电脑后路径可能失效。

推荐写法：

```xml
<mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
```

排查方法：

1. 检查文件是否真的存在。
2. 检查包名是否正确。
3. 检查 `CMakeLists.txt` 是否安装了 `meshes` 目录。
4. 重新 `colcon build` 并 `source install/setup.bash`。

### 8.7 collision 和 inertial 缺失

在 RViz 中，只看 visual 可能不会发现问题。但进入 Gazebo 或物理仿真时，缺少 collision/inertial 会导致：

1. 碰撞不准确。
2. 模型穿透。
3. 物理仿真不稳定。
4. 质量和惯量不合理。

基本写法：

```xml
<collision>
  <geometry>
    <box size="0.4 0.1 0.1"/>
  </geometry>
</collision>
<inertial>
  <mass value="10"/>
  <inertia ixx="1e-3" ixy="0.0" ixz="0.0" iyy="1e-3" iyz="0.0" izz="1e-3"/>
</inertial>
```

教学要求：

1. visual 决定“看起来是什么”。
2. collision 决定“碰撞时按什么形状算”。
3. inertial 决定“物理仿真中质量和惯量如何”。

### 8.8 xacro 宏错误

常见原因：

1. 忘记写命名空间：`xmlns:xacro="http://ros.org/wiki/xacro"`。
2. property 名称写错。
3. macro 参数数量不对。
4. 表达式括号或符号错误。
5. 宏生成的 link 或 joint 重名。

排查命令：

```bash
xacro src/urdf_tutorial/urdf/08-macroed.urdf.xacro > /tmp/macroed.urdf
check_urdf /tmp/macroed.urdf
```

重要原则：

> xacro 不是最终模型，展开后的 URDF 才是最终模型。讲课时一定要让学生看展开结果，而不是只看模板文件。

---

## 九、实操任务设计

### 9.1 基础任务：从零理解 URDF

任务目标：让学生能解释并修改最小模型。

操作要求：

1. 打开 `urdf/01-myfirst.urdf`。
2. 将圆柱半径从 `0.2` 改为 `0.3`。
3. 将圆柱长度从 `0.6` 改为 `0.8`。
4. 运行 RViz 查看变化。
5. 写一句话说明 `radius` 和 `length` 的作用。

验收标准：

1. 模型能正常显示。
2. 学生能说明单位是米。
3. 学生能指出 geometry 只影响视觉形状，不自动产生物理质量。

### 9.2 基础任务：添加一个 link

任务目标：理解 link 和 fixed joint。

操作要求：

1. 以 `02-multipleshapes.urdf` 为基础。
2. 添加一个 `left_leg`。
3. 用 `base_to_left_leg` 将其连接到 `base_link`。
4. 让左右腿在 y 方向对称。

参考：

```xml
<origin xyz="0 0.22 0.25"/>
```

验收标准：

1. 左右腿都能显示。
2. link 和 joint 名称不重复。
3. TF 树连通。

### 9.3 进阶任务：修复错位模型

教师准备一个错误版 `05-visual.urdf`，故意设置：

1. `base_to_right_leg` 的 y 坐标符号错误。
2. `right_front_wheel_joint` 的 z 坐标错误。
3. `right_gripper` 的 `rpy` 错误。

学生任务：

1. 运行错误模型，截图记录问题。
2. 找出至少 3 个错误位置。
3. 修复后重新运行。
4. 提交修改说明。

验收标准：

1. 左右腿对称。
2. 轮子贴近底盘且方向正确。
3. 左右夹爪镜像合理。

### 9.4 进阶任务：修复可动关节

教师准备一个错误版 `06-flexible.urdf`，故意设置：

1. 轮子 joint type 改成 `fixed`。
2. 左夹爪 axis 改成错误方向。
3. 伸缩杆 limit 删除。
4. 头部关节缺少 axis。

学生任务：

1. 启动模型和 Joint State Publisher GUI。
2. 观察哪些关节没有出现或运动异常。
3. 修复 joint type、axis、limit。
4. 再次拖动 GUI 验证。

验收标准：

1. 轮子关节可以连续转动。
2. 夹爪开合方向正确。
3. 伸缩杆运动范围合理。
4. 头部绕 z 轴旋转。

### 9.5 综合任务：从 URDF 改写为 xacro

任务目标：训练脚本化模型修复能力。

操作要求：

1. 阅读 `07-physics.urdf`。
2. 对比 `08-macroed.urdf.xacro`。
3. 找出 xacro 中的 property 和 macro。
4. 修改 `width`、`leglen`、`wheeldiam`，观察模型变化。
5. 展开 xacro 并检查结果。

命令：

```bash
xacro src/urdf_tutorial/urdf/08-macroed.urdf.xacro > /tmp/macroed.urdf
check_urdf /tmp/macroed.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/08-macroed.urdf.xacro
```

验收标准：

1. xacro 能成功展开。
2. 展开后的 URDF 能通过 `check_urdf`。
3. 修改参数后，左右结构仍保持对称。
4. 学生能解释 macro 如何减少重复。

### 9.6 模拟题目 A：限时 2 小时

教师发放：

1. 一份错误模型文件，例如 `exam_broken_robot.urdf`。
2. 一份参考说明，例如“身体半径 0.2 m，腿长 0.6 m，轮子直径 0.07 m，夹爪开合角 0 到 0.548 rad”。
3. 一份提交要求。

学生需要提交：

1. 修复后的模型文件。
2. 如使用 xacro，提交 xacro 文件和展开后的 URDF。
3. RViz 截图。
4. TF 树截图或说明。
5. 修复报告。

---

## 十、评分建议与提交规范

### 10.1 20 分评分建议

| 评分项 | 分值 | 评分说明 |
| --- | --- | --- |
| 模型文件可解析 | 2 分 | XML/URDF/xacro 无语法错误，能被工具加载 |
| link-joint 结构完整 | 3 分 | link 和 joint 命名唯一，父子关系正确，TF 树连通 |
| 几何尺寸正确 | 3 分 | 主体、腿、轮子、夹爪等尺寸符合参考文件 |
| 坐标与姿态正确 | 3 分 | 主要部件安装位置、方向、左右镜像正确 |
| 关节配置正确 | 3 分 | joint type、axis、limit 符合运动要求 |
| visual/collision/inertial 完整 | 2 分 | 视觉、碰撞、惯性配置基本完整合理 |
| launch/xacro/资源路径正确 | 2 分 | 能通过 launch 运行，mesh 路径可移植，xacro 可展开 |
| 验证与报告规范 | 2 分 | 提交运行命令、截图、问题说明、修复结论 |

### 10.2 提交文件建议

建议建立如下目录：

```text
submit_A/
├── urdf/
│   ├── repaired_robot.urdf
│   └── repaired_robot.urdf.xacro
├── screenshots/
│   ├── rviz_robot_model.png
│   └── tf_tree.png
├── logs/
│   ├── check_urdf.txt
│   └── xacro_expand.txt
└── report.md
```

### 10.3 修复报告模板

```markdown
# 模块 A 机器人仿真模型修复报告

## 1. 基本信息

- 选手编号：
- 模型文件：
- 验证环境：

## 2. 参考要求提取

| 项目 | 参考要求 |
| --- | --- |
| 主体尺寸 |  |
| 腿部尺寸 |  |
| 轮子尺寸 |  |
| 夹爪运动范围 |  |
| 关节类型 |  |

## 3. 发现的问题

| 序号 | 问题描述 | 位置 |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## 4. 修复内容

| 序号 | 修改内容 | 修改原因 |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## 5. 验证过程

```bash
check_urdf ...
xacro ...
ros2 launch ...
```

## 6. 验证结果

- URDF 检查：
- RViz 显示：
- TF 连通：
- 关节运动：

## 7. 最终结论

模型已按参考要求完成修复，能够正常加载、显示和验证。
```

---

## 十一、教师授课提示

### 11.1 课堂讲解重点

1. **不要把 URDF 当成普通三维模型文件讲**  
   URDF 的核心是 link-joint 树，不只是“画一个机器人外观”。

2. **origin 要多讲几遍**  
   学生最容易混淆 `joint origin` 和 `visual origin`。每次模型错位时，可以先问一句：“这是坐标系挂错了，还是几何体相对坐标系偏了？”

3. **TF 树最好画出来**  
   让学生在纸上画：

   ```text
   base_link
   ├── right_leg
   │   └── right_base
   │       ├── right_front_wheel
   │       └── right_back_wheel
   ├── left_leg
   │   └── left_base
   │       ├── left_front_wheel
   │       └── left_back_wheel
   ├── gripper_pole
   │   ├── left_gripper
   │   │   └── left_tip
   │   └── right_gripper
   │       └── right_tip
   └── head
       └── box
   ```

4. **xacro 要强调“先展开，再验证”**  
   只看 xacro 源文件不够，要检查展开后的 URDF。

5. **训练报告要从一开始就练**  
   竞赛里不只是把模型修好，还要让裁判看得明白：你发现了什么、怎么改的、怎么证明已经修好了。

### 11.2 课堂提问建议

| 问题 | 期待回答 |
| --- | --- |
| `link` 和 `joint` 谁表示零件，谁表示连接？ | link 表示刚体部件，joint 表示部件之间的连接 |
| 为什么模型中每个 link 名称都要唯一？ | TF 和 robot_state_publisher 需要唯一坐标系名称 |
| `visual origin` 和 `joint origin` 有什么区别？ | 一个移动几何体，一个移动子坐标系 |
| 为什么轮子需要 `continuous` joint？ | 轮子应能连续旋转，没有固定角度上下限 |
| 为什么 `revolute` 和 `prismatic` 需要 limit？ | 限制运动范围，避免不符合真实机构 |
| 为什么不建议使用绝对 mesh 路径？ | 换机器、换目录后资源会找不到 |
| 为什么 RViz 正常不代表 Gazebo 一定正常？ | RViz 主要看 visual，Gazebo 还需要 collision 和 inertial |

### 11.3 常见误区

| 误区 | 正确认识 |
| --- | --- |
| 只要 RViz 看起来对就一定对 | 还要检查 TF、关节、collision、inertial |
| link 顺序决定父子关系 | 父子关系由 joint 的 parent/child 决定 |
| `xyz` 单位是厘米 | URDF 中通常使用米 |
| `rpy` 单位是角度 | URDF 中使用弧度 |
| xacro 文件就是最终模型 | xacro 需要展开成 URDF |
| mesh 路径写绝对路径更稳 | package URI 更适合提交和迁移 |

---

## 附录 A：常用命令速查

### A.1 工作空间构建

```bash
cd /home/js/robot/HumanoidTeaching
colcon build --packages-select urdf_tutorial
source install/setup.bash
```

### A.2 启动默认模型

```bash
ros2 launch urdf_tutorial display.launch.py
```

### A.3 启动指定模型

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/06-flexible.urdf
```

### A.4 启动 xacro 模型

```bash
ros2 launch urdf_tutorial display.launch.py model:=urdf/08-macroed.urdf.xacro
```

### A.5 检查 URDF

```bash
check_urdf src/urdf_tutorial/urdf/07-physics.urdf
```

### A.6 展开 xacro

```bash
xacro src/urdf_tutorial/urdf/08-macroed.urdf.xacro > /tmp/macroed.urdf
check_urdf /tmp/macroed.urdf
```

### A.7 查看 robot_description

```bash
ros2 topic echo /robot_description --once
```

### A.8 查看 topic 列表

```bash
ros2 topic list
```

### A.9 生成 TF 树

```bash
ros2 run tf2_tools view_frames
```

如果环境中没有 `tf2_tools`，可安装：

```bash
sudo apt install -y ros-${ROS_DISTRO}-tf2-tools
```

---

## 附录 B：URDF 标签速查

| 标签 | 用途 | 示例 |
| --- | --- | --- |
| `<robot>` | 机器人根标签 | `<robot name="my_robot">` |
| `<link>` | 刚体部件 | `<link name="base_link">` |
| `<joint>` | 两个 link 的连接 | `<joint name="base_to_head" type="fixed">` |
| `<parent>` | 父 link | `<parent link="base_link"/>` |
| `<child>` | 子 link | `<child link="head"/>` |
| `<origin>` | 平移和旋转 | `<origin xyz="0 0 0.3" rpy="0 0 0"/>` |
| `<visual>` | 视觉模型 | RViz 中看到的外观 |
| `<collision>` | 碰撞模型 | Gazebo/物理碰撞使用 |
| `<inertial>` | 惯性模型 | 质量和惯量 |
| `<geometry>` | 几何形状容器 | 包含 box/cylinder/sphere/mesh |
| `<box>` | 长方体 | `<box size="0.6 0.1 0.2"/>` |
| `<cylinder>` | 圆柱体 | `<cylinder radius="0.2" length="0.6"/>` |
| `<sphere>` | 球体 | `<sphere radius="0.2"/>` |
| `<mesh>` | 外部模型 | `<mesh filename="package://..."/>` |
| `<material>` | 材质颜色 | `<material name="blue"/>` |
| `<axis>` | 关节轴向 | `<axis xyz="0 0 1"/>` |
| `<limit>` | 运动限制 | `<limit lower="0" upper="0.548" effort="1000" velocity="0.5"/>` |
| `<mass>` | 质量 | `<mass value="10"/>` |
| `<inertia>` | 惯量矩阵 | `<inertia ixx="1e-3" .../>` |

---

## 附录 C：推荐训练顺序

建议教师按以下 4 轮组织训练：

### 第一轮：会看

目标：学生能读懂模型。

文件：

```text
01-myfirst.urdf
02-multipleshapes.urdf
03-origins.urdf
04-materials.urdf
```

训练重点：

1. 找出所有 link。
2. 找出所有 joint。
3. 说明每个 origin 的含义。
4. 在 RViz 中确认变化。

### 第二轮：会改

目标：学生能修改模型。

文件：

```text
05-visual.urdf
06-flexible.urdf
```

训练重点：

1. 修改尺寸。
2. 修改坐标。
3. 修改关节类型。
4. 修改 axis 和 limit。

### 第三轮：会验

目标：学生能证明模型正确。

工具：

```text
check_urdf
ros2 launch
RViz
Joint State Publisher GUI
TF
```

训练重点：

1. 记录命令输出。
2. 截图保存。
3. 说明验证结论。

### 第四轮：会交

目标：学生能按竞赛形式提交。

提交内容：

```text
修复模型文件
运行命令记录
RViz 截图
TF 验证
修复报告
```

训练重点：

1. 文件命名清楚。
2. 不使用本机绝对路径。
3. 报告能复现。
4. 修改说明准确。
