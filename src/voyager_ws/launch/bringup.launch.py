import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_name = 'voyager_ws'  # <-- Replace with your package name
    pkg_share = get_package_share_directory(pkg_name)

    world_file = os.path.join(pkg_share, 'worlds', 'simulation_env.sdf')
    models_dir = os.path.join(pkg_share, 'models')
    
    # Path to Voyager URDF/Xacro
    xacro_file = os.path.join(pkg_share, 'voyager_ws_description', 'urdf', 'mobile_manipulator.urdf.xacro')    
    # Path to default RViz config (optional)
    rviz_config_file = os.path.join(pkg_share, 'rviz', 'simulation.rviz')

    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    use_rviz = LaunchConfiguration('use_rviz', default='true')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to start RViz2'
    )

    # Export model path for Gazebo Sim
    set_gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
            ':',
            models_dir
        ]
    )

    # 1. Process Xacro to generate robot_description
    robot_description_content = Command([
    PathJoinSubstitution([FindExecutable(name='xacro')]),
    ' ',
    xacro_file
])

    # Wrap the command output with ParameterValue:
    robot_description = {
    'robot_description': ParameterValue(robot_description_content, value_type=str)
}

    # 2. Robot State Publisher Node
    robot_state_publisher = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    output='screen',
    parameters=[robot_description, {'use_sim_time': use_sim_time}]
)

    # 3. Start Gazebo Sim Server + GUI
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    # 4. Spawn Voyager Entity
    spawn_voyager = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'voyager',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.05',
            '-Y', '0.0'
        ],
        output='screen'
    )

    # 5. Topic Bridge (Clock, Control, Sensor, and Joint State messages)
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/camera/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
        ],
        output='screen'
    )

    # 6. RViz2 Node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file] if os.path.exists(rviz_config_file) else [],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz)
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_use_rviz,
        set_gz_resource_path,
        robot_state_publisher,
        gazebo,
        spawn_voyager,
        gz_bridge,
        rviz_node
    ])