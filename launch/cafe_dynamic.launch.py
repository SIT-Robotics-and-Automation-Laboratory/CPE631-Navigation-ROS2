import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression, TextSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('cpe631_ros2')
    tb3_share = get_package_share_directory('turtlebot3_gazebo')
    prefix_path = os.environ.get('AMENT_PREFIX_PATH', '/opt/ros/jazzy').split(':')[0] or '/opt/ros/jazzy'
    world_file = os.path.join(pkg_share, 'worlds', 'cafe.world')
    table_model = os.path.join(pkg_share, 'models', 'cafe_table', 'model.sdf')
    tb3_bridge = os.path.join(pkg_share, 'param', 'turtlebot3_burger_bridge_local.yaml')
    nav2_params = os.path.join(pkg_share, 'param', 'nav2_dynamic_conservative.yaml')
    default_map = os.path.join(pkg_share, 'maps', 'cafe.yaml')
    # Reuse the known-good RViz layout / tools from the standard navigation launch.
    rviz_config = os.path.join(pkg_share, 'rviz', 'navigation.rviz')

    mapping_arg = DeclareLaunchArgument('mapping', default_value='false')
    navigation_arg = DeclareLaunchArgument('navigation', default_value='false')
    enable_peds_arg = DeclareLaunchArgument('enable_peds', default_value='true')
    map_file_arg = DeclareLaunchArgument('map_file', default_value=default_map)
    use_sim_time_arg = DeclareLaunchArgument('use_sim_time', default_value='true')
    model_arg = DeclareLaunchArgument('model', default_value='burger')
    use_composition_arg = DeclareLaunchArgument('use_composition', default_value='False')
    nav2_log_level_arg = DeclareLaunchArgument('nav2_log_level', default_value='info')

    mapping = LaunchConfiguration('mapping')
    navigation = LaunchConfiguration('navigation')
    enable_peds = LaunchConfiguration('enable_peds')
    map_file = LaunchConfiguration('map_file')
    use_sim_time = LaunchConfiguration('use_sim_time')
    model = LaunchConfiguration('model')
    use_composition = LaunchConfiguration('use_composition')
    nav2_log_level = LaunchConfiguration('nav2_log_level')

    gz_server = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': TextSubstitution(text=f'-r -v 4 {world_file}')
        }.items(),
    )

    set_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=':'.join([
            os.path.join(pkg_share, 'models'),
            os.path.join(pkg_share, 'models', 'cafe', 'materials', 'textures'),
            os.path.join(pkg_share, 'models', 'cafe_table', 'materials', 'textures'),
            os.path.join(pkg_share, 'models', 'person_walking', 'materials', 'textures'),
            os.path.join(pkg_share, 'models', 'person_standing', 'materials', 'textures'),
            os.path.join(tb3_share, 'models'),
            os.environ.get('GZ_SIM_RESOURCE_PATH', ''),
        ])
    )

    plugin_path_value = ':'.join([
        os.path.join(prefix_path, 'opt', 'gz_sim_vendor', 'lib', 'gz-sim-8', 'plugins'),
        os.path.join(prefix_path, 'opt', 'gz_sim_vendor', 'lib'),
        os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', ''),
    ])

    set_plugin_path = SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value=plugin_path_value,
    )

    set_ign_plugin_path = SetEnvironmentVariable(
        name='IGN_GAZEBO_SYSTEM_PLUGIN_PATH',
        value=':'.join([
            plugin_path_value,
            os.environ.get('IGN_GAZEBO_SYSTEM_PLUGIN_PATH', ''),
        ]),
    )

    set_tb3_model = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value=model,
    )

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(tb3_share, 'launch', 'robot_state_publisher.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items(),
    )

    spawn_table = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'cafe_table',
            '-file', table_model,
        ],
        output='screen',
    )

    spawn_actor_1 = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'person_walking_actor_1',
            '-file', os.path.join(pkg_share, 'models', 'person_walking_actor_1', 'model.sdf'),
        ],
        output='screen',
        condition=IfCondition(PythonExpression(["'", mapping, "' == 'false' and '", enable_peds, "' == 'true'"])),
    )

    spawn_actor_2 = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'person_walking_actor_2',
            '-file', os.path.join(pkg_share, 'models', 'person_walking_actor_2', 'model.sdf'),
        ],
        output='screen',
        condition=IfCondition(PythonExpression(["'", mapping, "' == 'false' and '", enable_peds, "' == 'true'"])),
    )

    spawn_actor_3 = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'person_walking_actor_3',
            '-file', os.path.join(pkg_share, 'models', 'person_walking_actor_3', 'model.sdf'),
        ],
        output='screen',
        condition=IfCondition(PythonExpression(["'", mapping, "' == 'false' and '", enable_peds, "' == 'true'"])),
    )

    spawn_standing = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'person_standing',
            '-file', os.path.join(pkg_share, 'models', 'person_standing', 'model.sdf'),
            '-x', '0.0',
            '-y', '6.0',
            '-z', '0.0',
            '-Y', '0.0',
        ],
        output='screen',
        condition=IfCondition(PythonExpression(["'", mapping, "' == 'false' and '", enable_peds, "' == 'true'"])),
    )

    bridge_tb3 = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': tb3_bridge}],
        output='screen',
    )

    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')
        ),
        condition=IfCondition(mapping),
        launch_arguments={
            'use_sim_time': use_sim_time,
        }.items(),
    )

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')
        ),
        condition=IfCondition(navigation),
        launch_arguments={
            'slam': 'False',
            'use_localization': 'True',
            'map': map_file,
            'use_sim_time': use_sim_time,
            'autostart': 'true',
            'params_file': nav2_params,
            'use_composition': use_composition,
            'log_level': nav2_log_level,
        }.items(),
    )

    map_republisher = Node(
        package='cpe631_ros2',
        executable='cpe631_map_republisher',
        name='map_republisher',
        output='screen',
        condition=IfCondition(navigation),
        parameters=[
            {
                'use_sim_time': use_sim_time,
                'input_map_topic': '/map',
                'output_map_topic': '/map_viz',
                'input_metadata_topic': '/map_metadata',
                'output_metadata_topic': '/map_metadata_viz',
                'republish_hz': 1.0,
            }
        ],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        remappings=[
            ('/map', '/map_viz'),
            ('/map_metadata', '/map_metadata_viz'),
        ],
        output='screen',
    )

    return LaunchDescription([
        mapping_arg,
        navigation_arg,
        enable_peds_arg,
        map_file_arg,
        use_sim_time_arg,
        model_arg,
        use_composition_arg,
        nav2_log_level_arg,
        set_resource_path,
        set_plugin_path,
        set_ign_plugin_path,
        set_tb3_model,
        gz_server,
        robot_state_publisher,
        spawn_table,
        spawn_actor_1,
        spawn_actor_2,
        spawn_actor_3,
        spawn_standing,
        bridge_tb3,
        slam_toolbox,
        nav2_bringup,
        map_republisher,
        rviz,
    ])
