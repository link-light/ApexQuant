cmake_minimum_required(VERSION 3.15)
project(ApexQuant VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准设置
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 编译选项
if(MSVC)
    add_compile_options(/W4 /O2)
else()
    add_compile_options(-Wall -Wextra -O3 -march=native)
endif()

# 查找依赖
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG)

if(NOT pybind11_FOUND)
    # 如果系统没有安装 pybind11，从子模块获取
    message(STATUS "pybind11 not found, fetching from GitHub...")
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v2.11.1
    )
    FetchContent_MakeAvailable(pybind11)
endif()

# 添加 Eigen3（矩阵运算库）
find_package(Eigen3 3.4 QUIET)
if(NOT Eigen3_FOUND)
    message(STATUS "Eigen3 not found, fetching from GitLab...")
    include(FetchContent)
    FetchContent_Declare(
        Eigen
        GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
        GIT_TAG 3.4.0
        GIT_SHALLOW TRUE
    )
    set(EIGEN_BUILD_DOC OFF)
    set(BUILD_TESTING OFF)
    set(EIGEN_BUILD_PKGCONFIG OFF)
    FetchContent_MakeAvailable(Eigen)
endif()

# 添加 cpp 子目录
add_subdirectory(cpp)

# 安装配置
install(TARGETS apexquant_core
    LIBRARY DESTINATION python/apexquant
    RUNTIME DESTINATION python/apexquant
)

