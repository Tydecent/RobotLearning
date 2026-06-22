# 题目 A：urdf_tutorial 机器人仿真模型修复训练材料与参考答案

> 配套文档：`题目A-urdf_tutorial机器人仿真模型修复与验证教程.md`  
> 训练项目：`/home/js/robot/HumanoidTeaching/src/urdf_tutorial`  
> 建议环境：Ubuntu 22.04 + ROS 2 Humble

---

## 一、材料使用说明

本材料用于“模块 A：机器人仿真模型修复与验证”的课堂训练或模拟考核。当前项目已提供一份待修复模型：

```text
src/urdf_tutorial/urdf/exam_broken_robot.urdf
```

它与原始正确文件分开保存，不会覆盖 `05-visual.urdf`、`06-flexible.urdf`、`07-physics.urdf`、`08-macroed.urdf.xacro`。其中 `07-physics.urdf` 可作为完整 URDF 参考答案。

如需重新制作或调整难度，建议方法：

1. 复制 `07-physics.urdf` 作为原始正确模型。
2. 按“教师用错误注入清单”修改出错误版本。
3. 发给学生 `exam_broken_robot.urdf`、本材料中的“学生任务书”和“参考要求”。
4. 不要把“教师参考答案”发给学生。

也可以降低难度：复制 `05-visual.urdf` 训练外观、姿态、坐标修复；复制 `06-flexible.urdf` 训练关节修复；复制 `07-physics.urdf` 训练完整模型修复。

---

## 二、学生任务书

### 2.1 任务背景

现有一份机器人 URDF 模型文件 `exam_broken_robot.urdf`，模型中存在结构、坐标、姿态、关节、mesh 路径和物理属性等错误。请根据参考要求修复模型，并使用 ROS 2 工具验证修复结果。

### 2.2 待修复机器人组成

机器人应由以下部分组成：

| 序号 | 部件 | link 名称 | 说明 |
| --- | --- | --- | --- |
| 1 | 主体 | `base_link` | 蓝色圆柱体，作为机器人根节点 |
| 2 | 右腿 | `right_leg` | 安装在主体右侧 |
| 3 | 右底座 | `right_base` | 安装在右腿下端 |
| 4 | 右前轮 | `right_front_wheel` | 安装在右底座前方 |
| 5 | 右后轮 | `right_back_wheel` | 安装在右底座后方 |
| 6 | 左腿 | `left_leg` | 安装在主体左侧，与右腿对称 |
| 7 | 左底座 | `left_base` | 安装在左腿下端 |
| 8 | 左前轮 | `left_front_wheel` | 安装在左底座前方 |
| 9 | 左后轮 | `left_back_wheel` | 安装在左底座后方 |
| 10 | 伸缩杆 | `gripper_pole` | 安装在主体前方，可沿 x 方向伸缩 |
| 11 | 左夹爪 | `left_gripper`、`left_tip` | 位于伸缩杆左侧 |
| 12 | 右夹爪 | `right_gripper`、`right_tip` | 位于伸缩杆右侧，与左夹爪镜像 |
| 13 | 头部 | `head` | 安装在主体上方，可绕 z 轴旋转 |
| 14 | 顶部方块 | `box` | 安装在头部斜上方 |

### 2.3 参考尺寸、坐标和姿态要求

所有长度单位均为 m，所有姿态角单位均为 rad。

| 部件/连接 | 正确要求 |
| --- | --- |
| 主体 `base_link` | 圆柱体，`radius="0.2"`，`length="0.6"`，蓝色 |
| 左右腿 `left_leg` / `right_leg` | 长方体，`box size="0.6 0.1 0.2"` |
| 腿部 visual/collision 姿态 | `origin rpy="0 1.57075 0" xyz="0 0 -0.3"` |
| 右腿连接 | `base_to_right_leg`：`parent="base_link"`，`child="right_leg"`，`origin xyz="0 -0.22 0.25"` |
| 左腿连接 | `base_to_left_leg`：`parent="base_link"`，`child="left_leg"`，`origin xyz="0 0.22 0.25"` |
| 左右底座 | `box size="0.4 0.1 0.1"` |
| 底座连接 | `right_base_joint` / `left_base_joint`：`origin xyz="0 0 -0.6"` |
| 四个轮子 | 圆柱体，`radius="0.035"`，`length="0.1"`，黑色 |
| 轮子 visual/collision 姿态 | `origin rpy="1.57075 0 0" xyz="0 0 0"` |
| 前轮连接位置 | `origin xyz="0.133333333333 0 -0.085"` |
| 后轮连接位置 | `origin xyz="-0.133333333333 0 -0.085"` |
| 伸缩杆连接 | `gripper_extension`：`origin xyz="0.19 0 0.2"` |
| 伸缩杆外形 | 圆柱体，`radius="0.01"`，`length="0.2"` |
| 伸缩杆姿态 | `origin rpy="0 1.57075 0" xyz="0.1 0 0"` |
| 左夹爪连接 | `left_gripper_joint`：`origin xyz="0.2 0.01 0"` |
| 右夹爪连接 | `right_gripper_joint`：`origin xyz="0.2 -0.01 0"` |
| 左夹爪 mesh 姿态 | `origin rpy="0.0 0 0" xyz="0 0 0"` |
| 右夹爪 mesh 姿态 | `origin rpy="-3.1415 0 0" xyz="0 0 0"` |
| 左指尖 mesh 姿态 | `origin rpy="0.0 0 0" xyz="0.09137 0.00495 0"` |
| 右指尖 mesh 姿态 | `origin rpy="-3.1415 0 0" xyz="0.09137 0.00495 0"` |
| 头部 | 球体，`radius="0.2"`，白色 |
| 头部连接 | `head_swivel`：`origin xyz="0 0 0.3"` |
| 顶部方块 | `box size="0.08 0.08 0.08"`，蓝色 |
| 顶部方块连接 | `tobox`：`origin xyz="0.1814 0 0.1414"` |

### 2.4 关节运动要求

| joint 名称 | 类型 | axis | limit |
| --- | --- | --- | --- |
| `right_front_wheel_joint` | `continuous` | `0 1 0` | 不需要 limit |
| `right_back_wheel_joint` | `continuous` | `0 1 0` | 不需要 limit |
| `left_front_wheel_joint` | `continuous` | `0 1 0` | 不需要 limit |
| `left_back_wheel_joint` | `continuous` | `0 1 0` | 不需要 limit |
| `gripper_extension` | `prismatic` | 默认 x 方向 | `lower="-0.38"`，`upper="0"`，`effort="1000.0"`，`velocity="0.5"` |
| `left_gripper_joint` | `revolute` | `0 0 1` | `lower="0.0"`，`upper="0.548"`，`effort="1000.0"`，`velocity="0.5"` |
| `right_gripper_joint` | `revolute` | `0 0 -1` | `lower="0.0"`，`upper="0.548"`，`effort="1000.0"`，`velocity="0.5"` |
| `head_swivel` | `continuous` | `0 0 1` | 不需要 limit |

### 2.5 mesh 和物理属性要求

| 项目 | 正确要求 |
| --- | --- |
| 夹爪主体 mesh | `package://urdf_tutorial/meshes/l_finger.dae` |
| 夹爪指尖 mesh | `package://urdf_tutorial/meshes/l_finger_tip.dae` |
| mesh 路径 | 不允许使用本机绝对路径 |
| collision | 主要 link 应与 visual 几何形状和姿态一致 |
| inertial | 每个参与完整模型的 link 应有 `mass` 和 `inertia` |
| 简化惯量 | 可统一使用 `ixx="1e-3" iyy="1e-3" izz="1e-3"`，交叉项为 `0.0` |

### 2.6 学生需要完成的工作

1. 运行错误模型，记录初始现象。
2. 使用 `check_urdf` 检查语法。
3. 检查 link-joint 父子关系，保证所有 link 连入同一棵 TF 树。
4. 修复尺寸、坐标、姿态和左右镜像错误。
5. 修复关节类型、运动轴和运动范围。
6. 修复 mesh 路径。
7. 补齐或修正 `collision`、`inertial`。
8. 使用 RViz、TF、Joint State Publisher GUI 验证模型。
9. 提交修复后的 URDF 和修复报告。

### 2.7 推荐验证命令

```bash
cd /home/js/robot/HumanoidTeaching
source /opt/ros/humble/setup.bash
colcon build --packages-select urdf_tutorial
source install/setup.bash

check_urdf src/urdf_tutorial/urdf/exam_broken_robot.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/exam_broken_robot.urdf
```

如需生成 TF 树：

```bash
ros2 run tf2_tools view_frames
```

---

## 三、教师用错误注入清单

本节用于教师制作错误模型。建议按学生水平选择 6 到 12 个错误，不一定全部注入。

| 编号 | 待修复位置 | 建议错误写法 | 学生应观察到的现象 | 正确答案 |
| --- | --- | --- | --- | --- |
| E01 | `base_to_right_leg` | `origin xyz="0 0.22 0.25"` | 两条腿跑到同一侧，左右不对称 | `origin xyz="0 -0.22 0.25"` |
| E02 | `base_to_left_leg` | `origin xyz="0 -0.22 0.25"` | 两条腿跑到同一侧 | `origin xyz="0 0.22 0.25"` |
| E03 | `right_leg` visual/collision | `rpy="0 0 0"` | 腿部朝向不对，长方体不像支腿 | `rpy="0 1.57075 0"` |
| E04 | 任意轮子 visual/collision | `rpy="0 0 0"` | 轮子竖直方向不对 | `rpy="1.57075 0 0"` |
| E05 | `right_front_wheel_joint` | `xyz="0.133333333333 0 0.085"` | 轮子漂浮或装到错误高度 | `xyz="0.133333333333 0 -0.085"` |
| E06 | `right_back_wheel_joint` | `xyz="0.133333333333 0 -0.085"` | 前后轮重合 | `xyz="-0.133333333333 0 -0.085"` |
| E07 | 轮子 joint type | `type="fixed"` | GUI 中轮子不可连续转动 | `type="continuous"` |
| E08 | 轮子 axis | `axis xyz="1 0 0"` | 轮子绕错轴旋转 | `axis xyz="0 1 0"` |
| E09 | `gripper_extension` | `type="fixed"` 或删除 `limit` | 伸缩杆不可动或缺少运动范围 | `type="prismatic"`，`limit lower="-0.38" upper="0"` |
| E10 | `left_gripper_joint` | `axis xyz="0 0 -1"` | 左夹爪开合方向错误 | `axis xyz="0 0 1"` |
| E11 | `right_gripper_joint` | `axis xyz="0 0 1"` | 右夹爪开合方向错误 | `axis xyz="0 0 -1"` |
| E12 | `right_gripper` visual/collision | `rpy="0.0 0 0"` | 右夹爪没有镜像翻转 | `rpy="-3.1415 0 0"` |
| E13 | `right_tip` visual/collision | `rpy="0.0 0 0"` | 右指尖方向与右夹爪不一致 | `rpy="-3.1415 0 0"` |
| E14 | `head_swivel` | `type="fixed"` 或缺少 `axis` | 头部不可转动 | `type="continuous"`，`axis xyz="0 0 1"` |
| E15 | mesh 路径 | `/home/js/robot/HumanoidTeaching/src/urdf_tutorial/meshes/l_finger.dae` | 换环境或安装后可能加载失败 | `package://urdf_tutorial/meshes/l_finger.dae` |
| E16 | `collision` | 删除轮子、腿、夹爪的 collision | RViz 外观可能正常，但物理属性不完整 | collision 几何和姿态与 visual 保持一致 |
| E17 | `inertial` | 删除 `mass` 或把惯量写成 0 | 物理仿真不稳定或检查不合格 | 补 `mass` 与简化 `inertia` |
| E18 | parent/child | 将 `right_base_joint` 的 `parent` 改为不存在的 `right_leg_wrong` | URDF 检查报错或 TF 断裂 | `parent link="right_leg"` |

---

## 四、教师参考答案

### 4.1 标准 link-joint 树

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

### 4.2 坐标和姿态答案

| 检查项 | 正确值 |
| --- | --- |
| `base_to_right_leg` | `xyz="0 -0.22 0.25"` |
| `base_to_left_leg` | `xyz="0 0.22 0.25"` |
| `right_leg` / `left_leg` visual origin | `rpy="0 1.57075 0" xyz="0 0 -0.3"` |
| `right_base_joint` / `left_base_joint` | `xyz="0 0 -0.6"` |
| 前轮 joint origin | `xyz="0.133333333333 0 -0.085"` |
| 后轮 joint origin | `xyz="-0.133333333333 0 -0.085"` |
| 四个轮子 visual/collision origin | `rpy="1.57075 0 0" xyz="0 0 0"` |
| `gripper_extension` joint origin | `rpy="0 0 0" xyz="0.19 0 0.2"` |
| `gripper_pole` visual/collision origin | `rpy="0 1.57075 0" xyz="0.1 0 0"` |
| `left_gripper_joint` | `xyz="0.2 0.01 0"` |
| `right_gripper_joint` | `xyz="0.2 -0.01 0"` |
| `left_gripper` / `left_tip` mesh origin | `rpy="0.0 0 0"` |
| `right_gripper` / `right_tip` mesh origin | `rpy="-3.1415 0 0"` |
| `head_swivel` joint origin | `xyz="0 0 0.3"` |
| `tobox` joint origin | `xyz="0.1814 0 0.1414"` |

### 4.3 关节答案

```xml
<joint name="right_front_wheel_joint" type="continuous">
  <axis rpy="0 0 0" xyz="0 1 0"/>
  <parent link="right_base"/>
  <child link="right_front_wheel"/>
  <origin rpy="0 0 0" xyz="0.133333333333 0 -0.085"/>
</joint>
```

```xml
<joint name="right_back_wheel_joint" type="continuous">
  <axis rpy="0 0 0" xyz="0 1 0"/>
  <parent link="right_base"/>
  <child link="right_back_wheel"/>
  <origin rpy="0 0 0" xyz="-0.133333333333 0 -0.085"/>
</joint>
```

```xml
<joint name="left_front_wheel_joint" type="continuous">
  <axis rpy="0 0 0" xyz="0 1 0"/>
  <parent link="left_base"/>
  <child link="left_front_wheel"/>
  <origin rpy="0 0 0" xyz="0.133333333333 0 -0.085"/>
</joint>
```

```xml
<joint name="left_back_wheel_joint" type="continuous">
  <axis rpy="0 0 0" xyz="0 1 0"/>
  <parent link="left_base"/>
  <child link="left_back_wheel"/>
  <origin rpy="0 0 0" xyz="-0.133333333333 0 -0.085"/>
</joint>
```

```xml
<joint name="gripper_extension" type="prismatic">
  <parent link="base_link"/>
  <child link="gripper_pole"/>
  <limit effort="1000.0" lower="-0.38" upper="0" velocity="0.5"/>
  <origin rpy="0 0 0" xyz="0.19 0 0.2"/>
</joint>
```

```xml
<joint name="left_gripper_joint" type="revolute">
  <axis xyz="0 0 1"/>
  <limit effort="1000.0" lower="0.0" upper="0.548" velocity="0.5"/>
  <origin rpy="0 0 0" xyz="0.2 0.01 0"/>
  <parent link="gripper_pole"/>
  <child link="left_gripper"/>
</joint>
```

```xml
<joint name="right_gripper_joint" type="revolute">
  <axis xyz="0 0 -1"/>
  <limit effort="1000.0" lower="0.0" upper="0.548" velocity="0.5"/>
  <origin rpy="0 0 0" xyz="0.2 -0.01 0"/>
  <parent link="gripper_pole"/>
  <child link="right_gripper"/>
</joint>
```

```xml
<joint name="head_swivel" type="continuous">
  <parent link="base_link"/>
  <child link="head"/>
  <axis xyz="0 0 1"/>
  <origin xyz="0 0 0.3"/>
</joint>
```

### 4.4 mesh 姿态答案

```xml
<link name="left_gripper">
  <visual>
    <origin rpy="0.0 0 0" xyz="0 0 0"/>
    <geometry>
      <mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
    </geometry>
  </visual>
</link>
```

```xml
<link name="right_gripper">
  <visual>
    <origin rpy="-3.1415 0 0" xyz="0 0 0"/>
    <geometry>
      <mesh filename="package://urdf_tutorial/meshes/l_finger.dae"/>
    </geometry>
  </visual>
</link>
```

```xml
<link name="left_tip">
  <visual>
    <origin rpy="0.0 0 0" xyz="0.09137 0.00495 0"/>
    <geometry>
      <mesh filename="package://urdf_tutorial/meshes/l_finger_tip.dae"/>
    </geometry>
  </visual>
</link>
```

```xml
<link name="right_tip">
  <visual>
    <origin rpy="-3.1415 0 0" xyz="0.09137 0.00495 0"/>
    <geometry>
      <mesh filename="package://urdf_tutorial/meshes/l_finger_tip.dae"/>
    </geometry>
  </visual>
</link>
```

### 4.5 物理属性答案

完整训练建议以 `07-physics.urdf` 为参考答案。每个主要 link 至少包含：

```xml
<collision>
  <geometry>
    <!-- 与 visual 使用相同或近似的 geometry -->
  </geometry>
</collision>
<inertial>
  <mass value="1"/>
  <inertia ixx="1e-3" ixy="0.0" ixz="0.0" iyy="1e-3" iyz="0.0" izz="1e-3"/>
</inertial>
```

建议质量参考：

| link 类型 | mass |
| --- | --- |
| 主体、腿、底座 | `10` |
| 轮子、顶部方块 | `1` |
| 头部 | `2` |
| 伸缩杆、夹爪、指尖 | `0.05` |

---

## 五、xacro 进阶训练答案

如果要求学生把修复后的模型整理为 xacro，可参考 `08-macroed.urdf.xacro` 的参数化方式。

### 5.1 标准参数

| property | 正确值 | 含义 |
| --- | --- | --- |
| `width` | `0.2` | 主体半径、头部半径参考值 |
| `leglen` | `0.6` | 腿长 |
| `polelen` | `0.2` | 伸缩杆长度 |
| `bodylen` | `0.6` | 主体圆柱长度 |
| `baselen` | `0.4` | 底座长度 |
| `wheeldiam` | `0.07` | 轮子直径 |

### 5.2 关键公式

| 位置 | xacro 公式 | 展开后的值 |
| --- | --- | --- |
| 腿部 y 坐标 | `${reflect*(width+.02)}` | 右腿 `-0.22`，左腿 `0.22` |
| 腿部 visual z 坐标 | `-${leglen/2}` | `-0.3` |
| 底座 z 坐标 | `${-leglen}` | `-0.6` |
| 轮子 x 坐标 | `${baselen*reflect/3}` | 前轮 `0.133333333333`，后轮 `-0.133333333333` |
| 轮子 z 坐标 | `-${wheeldiam/2+.05}` | `-0.085` |
| 伸缩杆 lower | `-${width*2-.02}` | `-0.38` |
| 伸缩杆 x 坐标 | `${width-.01}` | `0.19` |
| 夹爪 y 坐标 | `${reflect*0.01}` | 左 `0.01`，右 `-0.01` |
| 右夹爪镜像姿态 | `${(reflect-1)/2*pi}` | `-3.14159` 左右 |
| 头部 z 坐标 | `${bodylen/2}` | `0.3` |
| 顶部方块连接 | `${.707*width+0.04} 0 ${.707*width}` | 约 `0.1814 0 0.1414` |

### 5.3 xacro 验证命令

```bash
cd /home/js/robot/HumanoidTeaching
source install/setup.bash
xacro src/urdf_tutorial/urdf/08-macroed.urdf.xacro > /tmp/macroed.urdf
check_urdf /tmp/macroed.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/08-macroed.urdf.xacro
```

---

## 六、评分建议

总分 20 分。

| 评分项 | 分值 | 评分说明 |
| --- | --- | --- |
| URDF 可解析 | 2 分 | `check_urdf` 无 XML/URDF 解析错误 |
| link-joint 树完整 | 3 分 | 所有 link 命名唯一，父子关系正确，TF 连通 |
| 尺寸正确 | 3 分 | 主体、腿、底座、轮子、夹爪、头部尺寸符合参考要求 |
| 坐标和姿态正确 | 3 分 | 左右对称、轮子方向、夹爪镜像、头部和顶部方块位置正确 |
| 关节配置正确 | 3 分 | wheel、gripper、head、extension 的 type、axis、limit 正确 |
| mesh 和资源路径正确 | 2 分 | 使用 `package://` 路径，mesh 能加载 |
| collision/inertial 完整 | 2 分 | 主要 link 具备碰撞和惯性属性，质量和惯量基本合理 |
| 验证报告规范 | 2 分 | 有运行命令、截图、问题说明、修复结论 |

---

## 七、学生提交模板

````markdown
# 模块 A 机器人仿真模型修复报告

## 1. 基本信息

- 学生姓名：
- 模型文件：
- 验证环境：

## 2. 初始问题记录

| 序号 | 观察到的问题 | 可能原因 |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## 3. 修复内容

| 序号 | 修改位置 | 修改前 | 修改后 | 修改原因 |
| --- | --- | --- | --- | --- |
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

## 4. 验证命令

```bash
check_urdf src/urdf_tutorial/urdf/exam_broken_robot.urdf
ros2 launch urdf_tutorial display.launch.py model:=urdf/exam_broken_robot.urdf
```

## 5. 验证结果

- URDF 检查结果：
- RViz 显示结果：
- TF 连通结果：
- 关节运动结果：

## 6. 最终结论

模型已完成修复，能够正常加载、显示和验证。
````

