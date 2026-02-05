# ApexQuant C++ 核心模块

# 包含目录
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# 收集源文件（排除simulation模块，单独编译）
file(GLOB_RECURSE CORE_SOURCES 
    ${CMAKE_CURRENT_SOURCE_DIR}/src/backtest_engine.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/bindings.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/connection_manager.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/data_structures.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/indicators.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/risk_metrics.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/trading_interface.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/utils.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/websocket_client.cpp
)

# 创建核心 Python 模块
pybind11_add_module(apexquant_core ${CORE_SOURCES})

# 链接 Eigen
if(TARGET Eigen3::Eigen)
    target_link_libraries(apexquant_core PRIVATE Eigen3::Eigen)
elseif(TARGET eigen)
    target_link_libraries(apexquant_core PRIVATE eigen)
endif()

# 设置输出目录
set_target_properties(apexquant_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/python/apexquant
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/python/apexquant
)

# Windows 特殊处理
if(MSVC)
    target_compile_definitions(apexquant_core PRIVATE _USE_MATH_DEFINES)
    # 设置多配置生成器的输出目录
    foreach(CONFIG ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${CONFIG} CONFIG_UPPER)
        set_target_properties(apexquant_core PROPERTIES
            LIBRARY_OUTPUT_DIRECTORY_${CONFIG_UPPER} ${CMAKE_SOURCE_DIR}/python/apexquant
            RUNTIME_OUTPUT_DIRECTORY_${CONFIG_UPPER} ${CMAKE_SOURCE_DIR}/python/apexquant
        )
    endforeach()
endif()

# 启用优化
if(NOT MSVC)
    target_compile_options(apexquant_core PRIVATE -ffast-math)
endif()

# ============================================================================
# 模拟盘模块 (Simulation Module)
# ============================================================================

# 收集simulation源文件
set(SIMULATION_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/simulation/simulation_account.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/simulation/order_matcher.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/simulation/simulated_exchange.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/simulation/bindings.cpp
)

# 创建simulation Python模块
pybind11_add_module(apexquant_simulation ${SIMULATION_SOURCES})

# 链接 Eigen（如果需要）
if(TARGET Eigen3::Eigen)
    target_link_libraries(apexquant_simulation PRIVATE Eigen3::Eigen)
elseif(TARGET eigen)
    target_link_libraries(apexquant_simulation PRIVATE eigen)
endif()

# 设置输出目录
set_target_properties(apexquant_simulation PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/python/apexquant
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/python/apexquant
)

# Windows 特殊处理
if(MSVC)
    target_compile_definitions(apexquant_simulation PRIVATE _USE_MATH_DEFINES)
    # 设置多配置生成器的输出目录
    foreach(CONFIG ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${CONFIG} CONFIG_UPPER)
        set_target_properties(apexquant_simulation PROPERTIES
            LIBRARY_OUTPUT_DIRECTORY_${CONFIG_UPPER} ${CMAKE_SOURCE_DIR}/python/apexquant
            RUNTIME_OUTPUT_DIRECTORY_${CONFIG_UPPER} ${CMAKE_SOURCE_DIR}/python/apexquant
        )
    endforeach()
endif()

# 启用优化
if(NOT MSVC)
    target_compile_options(apexquant_simulation PRIVATE -ffast-math)
endif()

