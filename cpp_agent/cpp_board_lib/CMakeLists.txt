cmake_minimum_required(VERSION 3.10)
project(board_lib CXX)

set(CMAKE_C_STANDARD 23)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)


# Add a static library target named 'board_lib'.
# It uses src/lib/board.cpp as its source file.
add_library(board_lib STATIC
    src/lib/board.cpp
    src/lib/utils.cpp
)

# Add tests for the 'board_lib' target.
add_executable(board_lib_test
    src/tests/board_test.cpp
    src/lib/board.cpp
    src/lib/utils.cpp
)

# Specify the include directories for the 'board_lib' target.
# INTERFACE means that any target that links to 'board_lib' will also
# get this include directory added to its search path.
target_include_directories(board_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include/
)

# Specify the include directories for the 'board_lib_test' target.
target_include_directories(board_lib_test PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include/
)
