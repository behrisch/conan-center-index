cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_path(FOX_INCLUDE_DIR NAMES fx.h)
include_directories(SYSTEM ${FOX_INCLUDE_DIR})
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE package::package)
