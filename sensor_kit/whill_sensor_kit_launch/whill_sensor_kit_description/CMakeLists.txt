cmake_minimum_required(VERSION 3.8)
project(whill_sensor_kit_description)

find_package(ament_cmake_auto REQUIRED)

ament_auto_find_build_dependencies()

ament_auto_package(INSTALL_TO_SHARE
    urdf
    config
)
