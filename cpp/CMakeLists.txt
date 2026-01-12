# ApexQuant C++ 核心模块

# 包含目录
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# 收集源文件
file(GLOB_RECURSE SOURCES 
    ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
)

# 创建 Python 模块
pybind11_add_module(apexquant_core ${SOURCES})

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

