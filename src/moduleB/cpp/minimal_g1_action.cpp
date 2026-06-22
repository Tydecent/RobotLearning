#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>

#include <unitree/robot/channel/channel_factory.hpp>
#include <unitree/robot/g1/arm/g1_arm_action_error.hpp>
#include <unitree/robot/g1/arm/g1_arm_action_client.hpp>
#include <unitree/robot/g1/loco/g1_loco_client.hpp>

// 这个文件是模块 B 的 C++ 最小教学版本。
//
// 它演示的不是“底层关节控制”，而是 Unitree G1 官方 SDK2 的高层服务调用：
//   1. ChannelFactory::Init() 选择 DDS 通信用的网卡；
//   2. LocoClient.Start() 请求机器人进入高层运动 FSM 500；
//   3. G1ArmActionClient.ExecuteAction(id) 请求机器人执行固件内置预置动作；
//   4. 可选 ExecuteAction(99) 释放手臂保持姿态。
//
// 运行前请确保当前终端加载的是 unitree_sdk2 源码树 thirdparty/lib/x86_64
// 下的 CycloneDDS 动态库。若 LD_LIBRARY_PATH 指向 third_party/unitree_robotics/lib，
// 本机环境中可能在初始化 SDK2 Client 时触发 free(): invalid pointer。

namespace {

constexpr int32_t kDefaultActionId = 17;  // clap
constexpr int32_t kReleaseArmActionId = 99;

// 命令行选项集中放在一个结构体中，便于把“参数解析”和“机器人控制流程”分开。
// 这样教学时可以先看 main() 的控制主线，再回来看每个参数的具体含义。
struct Options {
  std::string network;
  int32_t action_id = kDefaultActionId;
  float timeout = 10.0F;
  double release_delay = 2.0;
  bool list = false;
  bool release = false;
  bool check_fsm = false;
  bool no_start = false;
  bool help = false;
};

void PrintUsage(const char* program) {
  std::cout
      << "Unitree G1 C++ minimal arm action example\n\n"
      << "Usage:\n"
      << "  " << program << " --network eth0 [--action-id 17] [--release]\n"
      << "  " << program << " --network eth0 --list\n\n"
      << "Options:\n"
      << "  -h, --help               Show this help message\n"
      << "  -n, --network IFACE      DDS network interface connected to G1\n"
      << "      --iface IFACE        Alias of --network\n"
      << "  -i, --action-id ID       Preset arm action id, default 17=clap\n"
      << "  -l, --list               Read supported actions from the robot\n"
      << "      --check-fsm          Print sport fsm_id/fsm_mode before arm action\n"
      << "      --release            Execute 99=release arm after the action\n"
      << "      --release-delay SEC  Delay before release, default 2.0\n"
      << "      --no-start           Do not call LocoClient.Start() first\n"
      << "      --timeout SEC        Unitree RPC timeout, default 10.0\n\n"
      << "Common action ids:\n"
      << "  17=clap, 20=heart, 25=face wave, 26=high wave,\n"
      << "  27=shake hand, 99=release arm\n";
}

// 手写一个很小的参数解析器，避免为了教学示例额外引入 Boost/program_options。
// Unitree 官方示例使用 Boost，这里为了便于比赛现场快速阅读和修改，保留纯标准库实现。
std::string RequireValue(int argc, const char** argv, int* index, const std::string& option) {
  if (*index + 1 >= argc) {
    throw std::invalid_argument(option + " requires a value");
  }
  ++(*index);
  return argv[*index];
}

// 把字符串转换成动作 ID。动作 ID 是 Unitree 固件内部预置动作编号，
// 例如 17=clap、20=heart、99=release_arm。
int32_t ParseInt32(const std::string& value, const std::string& option) {
  try {
    size_t parsed = 0;
    int value_int = std::stoi(value, &parsed);
    if (parsed != value.size()) {
      throw std::invalid_argument("trailing characters");
    }
    return static_cast<int32_t>(value_int);
  } catch (const std::exception&) {
    throw std::invalid_argument(option + " expects an integer, got: " + value);
  }
}

// SDK2 的 SetTimeout() 接收秒数；保留浮点参数便于现场临时调大 RPC 等待时间。
float ParseFloat(const std::string& value, const std::string& option) {
  try {
    size_t parsed = 0;
    float value_float = std::stof(value, &parsed);
    if (parsed != value.size()) {
      throw std::invalid_argument("trailing characters");
    }
    return value_float;
  } catch (const std::exception&) {
    throw std::invalid_argument(option + " expects a number, got: " + value);
  }
}

// release_delay 用 double 是为了直接传给 std::chrono::duration<double>。
double ParseDouble(const std::string& value, const std::string& option) {
  try {
    size_t parsed = 0;
    double value_double = std::stod(value, &parsed);
    if (parsed != value.size()) {
      throw std::invalid_argument("trailing characters");
    }
    return value_double;
  } catch (const std::exception&) {
    throw std::invalid_argument(option + " expects a number, got: " + value);
  }
}

// 支持 --iface 是为了和 Python 版脚本的参数习惯一致；
// C++ 官方示例通常叫 --network。
Options ParseOptions(int argc, const char** argv) {
  Options options;
  for (int i = 1; i < argc; ++i) {
    const std::string arg = argv[i];
    if (arg == "-h" || arg == "--help") {
      options.help = true;
    } else if (arg == "-n" || arg == "--network" || arg == "--iface") {
      options.network = RequireValue(argc, argv, &i, arg);
    } else if (arg == "-i" || arg == "--action-id") {
      options.action_id = ParseInt32(RequireValue(argc, argv, &i, arg), arg);
    } else if (arg == "-l" || arg == "--list") {
      options.list = true;
    } else if (arg == "--check-fsm") {
      options.check_fsm = true;
    } else if (arg == "--release") {
      options.release = true;
    } else if (arg == "--release-delay") {
      options.release_delay = ParseDouble(RequireValue(argc, argv, &i, arg), arg);
    } else if (arg == "--no-start") {
      options.no_start = true;
    } else if (arg == "--timeout") {
      options.timeout = ParseFloat(RequireValue(argc, argv, &i, arg), arg);
    } else {
      throw std::invalid_argument("unknown option: " + arg);
    }
  }
  return options;
}

// G1ArmActionClient 会返回 SDK2/机器人服务的错误码。
// 对教学最重要的是 INVALID_FSM_ID：它说明不是动作 ID 本身错了，
// 而是机器人当前 FSM 状态不允许执行该手臂动作。
void PrintArmActionReturnCode(int32_t ret) {
  if (ret == 0) {
    std::cout << "return code: 0\n";
    return;
  }

  namespace g1 = unitree::robot::g1;
  std::cout << "return code: " << ret << "\n";
  switch (ret) {
    case g1::UT_ROBOT_ARM_ACTION_ERR_ARMSDK:
      std::cout << g1::UT_ROBOT_ARM_ACTION_ERR_ARMSDK_DESC << "\n";
      break;
    case g1::UT_ROBOT_ARM_ACTION_ERR_HOLDING:
      std::cout << g1::UT_ROBOT_ARM_ACTION_ERR_HOLDING_DESC << "\n";
      break;
    case g1::UT_ROBOT_ARM_ACTION_ERR_INVALID_ACTION_ID:
      std::cout << g1::UT_ROBOT_ARM_ACTION_ERR_INVALID_ACTION_ID_DESC << "\n";
      break;
    case g1::UT_ROBOT_ARM_ACTION_ERR_INVALID_FSM_ID:
      std::cout << "The actions are only supported in fsm id {500, 501, 801}.\n"
                << "Try calling LocoClient.Start() first, or subscribe to rt/sportmodestate "
                << "to check the current fsm id.\n";
      break;
    default:
      std::cout << "Execute action failed with an unrecognized Unitree error code.\n";
      break;
  }
}

// ExecuteAction(id) 只是在发“执行动作 ID”的高层请求。
// 动作轨迹、平衡、时序等都由 G1 内部动作服务完成，用户程序不直接发关节角度。
int ExecuteArmAction(unitree::robot::g1::G1ArmActionClient& arm_client, int32_t action_id) {
  std::cout << "G1ArmActionClient.ExecuteAction(" << action_id << ")" << std::endl;
  const int32_t ret = arm_client.ExecuteAction(action_id);
  PrintArmActionReturnCode(ret);
  return ret;
}

// Sport Services Interface 中的 fsm_id / fsm_mode 是排查高层动作失败的关键。
// 手臂预置动作一般要求 fsm_id 属于 {500, 501, 801}；
// 若 fsm_id=801，还要注意 fsm_mode 是否在官方允许范围内。
void PrintLocoState(unitree::robot::g1::LocoClient& loco_client) {
  int fsm_id = -1;
  const int32_t fsm_id_ret = loco_client.GetFsmId(fsm_id);
  if (fsm_id_ret == 0) {
    std::cout << "SportServices.GetFsmId() -> " << fsm_id << "\n";
  } else {
    std::cout << "SportServices.GetFsmId() failed, return code: " << fsm_id_ret << "\n";
  }

  int fsm_mode = -1;
  const int32_t fsm_mode_ret = loco_client.GetFsmMode(fsm_mode);
  if (fsm_mode_ret == 0) {
    std::cout << "SportServices.GetFsmMode() -> " << fsm_mode << "\n";
  } else {
    std::cout << "SportServices.GetFsmMode() failed, return code: " << fsm_mode_ret << "\n";
  }

  std::cout << "Arm actions usually require fsm_id in {500, 501, 801}; "
            << "when fsm_id=801, fsm_mode should be {0, 3}.\n";
}

[[noreturn]] void ExitAfterSdkInit(int exit_code) {
  std::cout.flush();
  std::cerr.flush();
  // 一些 SDK2/CycloneDDS 组合在进程退出、全局对象析构或 Client 清理时不稳定。
  // 这个程序是一次性命令行工具：所有请求和返回码已经打印完毕后，直接退出进程
  // 可以避免“动作已执行但退出时 free(): invalid pointer”干扰教学判断。
  std::_Exit(exit_code);
}

}  // namespace

int main(int argc, const char** argv) {
  try {
    const Options options = ParseOptions(argc, argv);
    if (options.help) {
      PrintUsage(argv[0]);
      return EXIT_SUCCESS;
    }
    if (options.network.empty()) {
      std::cerr << "Missing required option: --network IFACE\n\n";
      PrintUsage(argv[0]);
      return EXIT_FAILURE;
    }

    // 第 1 步：初始化 SDK2 DDS 通道。
    //
    // domain id 这里使用 0，和当前 Python 最小脚本保持一致。
    // network 必须是连接 G1 的有线网卡，例如 enp88s0/eth0。
    // 如果网卡名错误，后续 RPC 往往表现为超时或没有响应。
    std::cerr << "[1/4] Init ChannelFactory on network: " << options.network << std::endl;
    unitree::robot::ChannelFactory::Instance()->Init(0, options.network);
    std::cerr << "[1/4] ChannelFactory initialized" << std::endl;

    // 第 2 步：初始化手臂预置动作客户端。
    //
    // G1ArmActionClient 对应官方 Arm Action Interface：
    //   - ExecuteAction(id)：执行固件内置预置动作；
    //   - GetActionList()：读取当前机器人固件支持的动作列表。
    std::cerr << "[2/4] Init G1ArmActionClient" << std::endl;
    auto arm_client = std::make_shared<unitree::robot::g1::G1ArmActionClient>();
    arm_client->Init();
    arm_client->SetTimeout(options.timeout);
    std::cerr << "[2/4] G1ArmActionClient initialized" << std::endl;

    // --list 只读取动作列表，不会让机器人运动。
    // 建议每次换固件或换机器人时先运行 --list，因为实际动作列表以真机返回为准。
    if (options.list) {
      std::cerr << "[3/4] Get action list" << std::endl;
      std::string action_list_data;
      const int32_t ret = arm_client->GetActionList(action_list_data);
      if (ret != 0) {
        std::cerr << "Failed to get action list, return code: " << ret << "\n";
        ExitAfterSdkInit(EXIT_FAILURE);
      }
      std::cout << "Available actions:\n" << action_list_data << "\n";
      ExitAfterSdkInit(EXIT_SUCCESS);
    }

    std::shared_ptr<unitree::robot::g1::LocoClient> loco_client;
    if (!options.no_start) {
      // 第 3 步：通过 Sport Services 请求进入 FSM 500。
      //
      // 官方手臂动作错误提示中明确提到，动作通常只支持 fsm_id {500,501,801}。
      // LocoClient.Start() 本质上就是请求机器人进入常用的高层运动 FSM 500。
      std::cerr << "[3/4] Init LocoClient" << std::endl;
      loco_client = std::make_shared<unitree::robot::g1::LocoClient>();
      loco_client->Init();
      loco_client->SetTimeout(options.timeout);
      std::cerr << "[3/4] LocoClient initialized" << std::endl;

      std::cout << "LocoClient.Start() -> FSM 500" << std::endl;
      const int32_t ret = loco_client->Start();
      std::cout << "return code: " << ret << "\n";
      // 给机器人内部 FSM 切换留一点时间，再发手臂动作请求。
      std::this_thread::sleep_for(std::chrono::milliseconds(500));
    } else {
      std::cerr << "[3/4] Skip LocoClient.Start()" << std::endl;
    }

    if (options.check_fsm) {
      // --check-fsm 用于现场排查：如果 ExecuteAction 返回 INVALID_FSM_ID，
      // 先看这里打印出来的 fsm_id/fsm_mode 是否满足官方 Sport Services 限制。
      if (!loco_client) {
        std::cerr << "[3/4] Init LocoClient for FSM check" << std::endl;
        loco_client = std::make_shared<unitree::robot::g1::LocoClient>();
        loco_client->Init();
        loco_client->SetTimeout(options.timeout);
      }
      PrintLocoState(*loco_client);
    }

    // 第 4 步：真正执行手臂/上半身预置动作。
    // 注意这里传的是“动作 ID”，不是关节角度，也不是 ROS action goal。
    std::cerr << "[4/4] Execute arm action" << std::endl;
    const int action_ret = ExecuteArmAction(*arm_client, options.action_id);

    if (options.release) {
      // 一些动作会保持最后一帧姿态，例如比心、拥抱、举手等。
      // ID 99 是官方 release_arm，用于退出保持姿态。
      std::this_thread::sleep_for(std::chrono::duration<double>(options.release_delay));
      const int release_ret = ExecuteArmAction(*arm_client, kReleaseArmActionId);
      ExitAfterSdkInit((action_ret == 0 && release_ret == 0) ? EXIT_SUCCESS : EXIT_FAILURE);
    }

    ExitAfterSdkInit(action_ret == 0 ? EXIT_SUCCESS : EXIT_FAILURE);
  } catch (const std::exception& exc) {
    std::cerr << exc.what() << "\n\n";
    PrintUsage(argv[0]);
    return EXIT_FAILURE;
  }
}
