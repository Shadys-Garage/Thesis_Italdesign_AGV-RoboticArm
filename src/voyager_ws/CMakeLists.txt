cmake_minimum_required(VERSION 3.8)
project(voyager_ws)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# Install directories into the share folder
install(
  DIRECTORY launch models worlds voyager_ws_description
  DESTINATION share/${PROJECT_NAME}
)

ament_package()