cmake_minimum_required(VERSION 3.10)

project(moduleB_g1_cpp_action LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Threads REQUIRED)

set(UNITREE_SDK2_SOURCE_DIR "" CACHE PATH "Path to the unitree_sdk2 source tree")

if(UNITREE_SDK2_SOURCE_DIR)
  set(UNITREE_SDK2_ARCH_LIB_DIR "${UNITREE_SDK2_SOURCE_DIR}/lib/${CMAKE_SYSTEM_PROCESSOR}")
  set(UNITREE_SDK2_THIRDPARTY_LIB_DIR "${UNITREE_SDK2_SOURCE_DIR}/thirdparty/lib/${CMAKE_SYSTEM_PROCESSOR}")

  add_library(ddsc SHARED IMPORTED GLOBAL)
  set_target_properties(ddsc PROPERTIES
    IMPORTED_LOCATION "${UNITREE_SDK2_THIRDPARTY_LIB_DIR}/libddsc.so"
    INTERFACE_INCLUDE_DIRECTORIES "${UNITREE_SDK2_SOURCE_DIR}/thirdparty/include")

  add_library(ddscxx SHARED IMPORTED GLOBAL)
  set_target_properties(ddscxx PROPERTIES
    IMPORTED_LOCATION "${UNITREE_SDK2_THIRDPARTY_LIB_DIR}/libddscxx.so"
    INTERFACE_INCLUDE_DIRECTORIES "${UNITREE_SDK2_SOURCE_DIR}/thirdparty/include/ddscxx")

  add_library(unitree_sdk2 STATIC IMPORTED GLOBAL)
  set_target_properties(unitree_sdk2 PROPERTIES
    IMPORTED_LOCATION "${UNITREE_SDK2_ARCH_LIB_DIR}/libunitree_sdk2.a"
    INTERFACE_INCLUDE_DIRECTORIES "${UNITREE_SDK2_SOURCE_DIR}/include;${UNITREE_SDK2_SOURCE_DIR}/thirdparty/include;${UNITREE_SDK2_SOURCE_DIR}/thirdparty/include/ddscxx"
    INTERFACE_LINK_LIBRARIES "ddsc;ddscxx;Threads::Threads")
else()
  find_package(unitree_sdk2 REQUIRED)
endif()

add_executable(minimal_g1_action minimal_g1_action.cpp)
target_link_libraries(minimal_g1_action PRIVATE unitree_sdk2)
if(UNITREE_SDK2_SOURCE_DIR)
  set_target_properties(minimal_g1_action PROPERTIES
    BUILD_RPATH "${UNITREE_SDK2_THIRDPARTY_LIB_DIR}")
endif()

install(TARGETS minimal_g1_action RUNTIME DESTINATION bin)
