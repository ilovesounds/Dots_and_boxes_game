cmake_minimum_required(VERSION 3.10)
project(agents CXX)
set(CMAKE_BUILD_TYPE Debug)

set(CMAKE_C_STANDARD 23)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)



# Executable for the game
add_executable(agent
    src/submission/agent.cpp
    src/controller.cpp
    src/run.cpp
)

target_include_directories(agent PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(agent PRIVATE board_lib)

add_subdirectory(cpp_board_lib)
