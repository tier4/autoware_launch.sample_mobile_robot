# Copyright 2023 Tier IV, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from ament_index_python.packages import get_package_share_directory
import launch
from launch.actions import DeclareLaunchArgument
from launch.actions import OpaqueFunction
from launch.actions import SetLaunchConfiguration
from launch.conditions import IfCondition
from launch.conditions import UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def get_lidar_make(sensor_name):
    if sensor_name[:6].lower() == "pandar":
        return "Hesai", ".csv"
    elif sensor_name[:3].lower() in ["hdl", "vlp", "vls"]:
        return "Velodyne", ".yaml"
    elif sensor_name.lower() in ["helios", "bpearl"]:
        return "Robosense", None
    return "unrecognized_sensor_model"


def launch_setup(context, *args, **kwargs):
    def create_parameter_dict(*args):
        result = {}
        for x in args:
            result[x] = LaunchConfiguration(x)
        return result

    # Model and make
    sensor_model = LaunchConfiguration("sensor_model").perform(context)
    sensor_make, sensor_extension = get_lidar_make(sensor_model)
    nebula_decoders_share_dir = get_package_share_directory("nebula_decoders")

    # Calibration file
    sensor_calib_fp = os.path.join(
        nebula_decoders_share_dir,
        "calibration",
        sensor_make.lower(),
        sensor_model + sensor_extension,
    )
    assert os.path.exists(
        sensor_calib_fp
    ), "Sensor calib file under calibration/ was not found: {}".format(sensor_calib_fp)

    nodes = []

    nodes.append(
        ComposableNode(
            package="nebula_ros",
            plugin=sensor_make + "RosWrapper",
            name=sensor_make.lower() + "_ros_wrapper_node",
            parameters=[
                {
                    "sensor_model": sensor_model,
                    "calibration_file": sensor_calib_fp,
                    "launch_hw": LaunchConfiguration("launch_driver"),
                    **create_parameter_dict(
                        "return_mode",
                        "host_ip",
                        "sensor_ip",
                        "multicast_ip",
                        "data_port",
                        "gnss_port",
                        "frame_id",
                        "cut_angle",
                        "sync_angle",
                        "min_range",
                        "max_range",
                        "packet_mtu_size",
                        "rotation_speed",
                        "cloud_min_angle",
                        "cloud_max_angle",
                        "dual_return_distance_threshold",
                        "ptp_profile",
                        "ptp_transport_type",
                        "ptp_switch_type",
                        "ptp_domain",
                        "ptp_lock_threshold",
                        "udp_only",
                        "diag_span",
                        "setup_sensor",
                        "retry_hw",
                    ),
                },
            ],
            remappings=[
                ("pandar_points", "pointcloud_raw_ex"),
            ],
            extra_arguments=[{"use_intra_process_comms": LaunchConfiguration("use_intra_process")}],
        )
    )

    # set container to run all required components in the same process
    container = ComposableNodeContainer(
        name=LaunchConfiguration("container_name"),
        namespace="pointcloud_preprocessor",
        package="rclcpp_components",
        executable=LaunchConfiguration("container_executable"),
        composable_node_descriptions=nodes,
        output="both",
    )

    return [container]


def generate_launch_description():
    launch_arguments = []

    def add_launch_arg(name: str, default_value=None, description=None):
        # a default_value of None is equivalent to not passing that kwarg at all
        launch_arguments.append(
            DeclareLaunchArgument(name, default_value=default_value, description=description)
        )

    add_launch_arg("sensor_model", description="sensor model name")
    add_launch_arg("launch_driver", "True", "do launch driver")
    add_launch_arg("return_mode", "Strongest")
    add_launch_arg("host_ip", "255.255.255.255", "host ip address")
    add_launch_arg("sensor_ip", "192.168.1.201", "device ip address")
    add_launch_arg("multicast_ip", "")
    add_launch_arg("data_port", "2368", "device data port number")
    add_launch_arg("gnss_port", "2380", "device gnss port number")
    add_launch_arg("frame_id", "lidar", "frame id")
    add_launch_arg("cut_angle", "0.0")
    add_launch_arg("sync_angle", "0.0")
    add_launch_arg("min_range", "0.3", "minimum view range for Velodyne sensors")
    add_launch_arg("max_range", "300.0", "maximum view range for Velodyne sensors")
    add_launch_arg("packet_mtu_size", "1500", "packet mtu size")
    add_launch_arg("rotation_speed", "600", "rotational frequency")
    add_launch_arg("cloud_min_angle", "0", "minimum view angle setting on device")
    add_launch_arg("cloud_max_angle", "360", "maximum view angle setting on device")
    add_launch_arg("dual_return_distance_threshold", "0.1", "dual return distance threshold")
    add_launch_arg("ptp_profile", "1588v2")
    add_launch_arg("ptp_transport_type", "UDP")
    add_launch_arg("ptp_switch_type", "TSN")
    add_launch_arg("ptp_domain", "0")
    add_launch_arg("ptp_lock_threshold", "100")
    add_launch_arg("udp_only", "false")
    add_launch_arg("diag_span", "1000")
    add_launch_arg("setup_sensor", "true")
    add_launch_arg("retry_hw", "true")
    add_launch_arg("processing_time_threshold_sec", "0.01")
    add_launch_arg("output_as_sensor_frame", "True", "output final pointcloud in sensor frame")
    add_launch_arg("enable_blockage_diag", "false")
    add_launch_arg("horizontal_ring_id", "64")
    add_launch_arg("vertical_bins", "128")
    add_launch_arg("is_channel_order_top2down", "true")
    add_launch_arg("horizontal_resolution", "0.4")
    add_launch_arg("use_multithread", "False", "use multithread")
    add_launch_arg("use_intra_process", "False", "use ROS 2 component container communication")
    add_launch_arg("use_pointcloud_container", "false")
    add_launch_arg("container_name", "nebula_node_container")

    set_container_executable = SetLaunchConfiguration(
        "container_executable",
        "component_container",
        condition=UnlessCondition(LaunchConfiguration("use_multithread")),
    )

    set_container_mt_executable = SetLaunchConfiguration(
        "container_executable",
        "component_container_mt",
        condition=IfCondition(LaunchConfiguration("use_multithread")),
    )

    return launch.LaunchDescription(
        launch_arguments
        + [set_container_executable, set_container_mt_executable]
        + [OpaqueFunction(function=launch_setup)]
    )
