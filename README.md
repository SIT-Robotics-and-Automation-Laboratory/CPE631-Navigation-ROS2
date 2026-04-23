# cpe631_ros2 (Gazebo Sim / ROS2 Jazzy)

## Overview
This project runs a Gazebo Sim cafe environment with a TurtleBot3 Burger, supports SLAM (mapping) and Nav2 navigation, and can optionally spawn moving pedestrians.

Workflow:
1) Mapping (SLAM) in a static environment, save a map.
2) Navigation with Nav2 using the saved map (dynamic pedestrians optional).

## Dependencies
ROS2 Jazzy and these packages:
- ros-jazzy-ros-gz-sim
- ros-jazzy-ros-gz-bridge
- ros-jazzy-ros-gz-image
- ros-jazzy-slam-toolbox
- ros-jazzy-nav2-bringup
- ros-jazzy-turtlebot3-gazebo
- ros-jazzy-turtlebot3-navigation2
- ros-jazzy-rviz2

## Build
```bash
cd ~/ros2_ws
colcon build --packages-select cpe631_ros2
source install/setup.bash
```

## Run
### 1) Mapping (static scene, no pedestrians)
```bash
ros2 launch cpe631_ros2 cafe.launch.py mapping:=true
```
- Use teleop to drive and build the map:
```bash
ros2 launch cpe631_ros2 teleop.launch.py model:=burger
```

### 2) Save the map
Relative output location (recommended):
```bash
mkdir -p ~/ros2_ws/src/cpe631_ros2/maps
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/cpe631_ros2/maps/cafe
```
This creates:
- `maps/cafe.yaml`
- `maps/cafe.pgm`

### 3) Navigation (load map, Nav2)
```bash
ros2 launch cpe631_ros2 cafe.launch.py navigation:=true map_file:=~/ros2_ws/src/cpe631_ros2/maps/cafe.yaml
```
In RViz:
- Click **2D Pose Estimate** to set the initial pose.
- Click **Nav2 Goal** to send a goal.

## Launch arguments
`launch/cafe.launch.py` supports:
- `mapping` (true/false): enable SLAM (no pedestrians)
- `navigation` (true/false): enable Nav2
- `enable_peds` (true/false): enable pedestrians (ignored when mapping=true)
- `map_file` (path): map YAML for navigation
- `model` (burger/waffle/waffle_pi)
- `use_sim_time` (true/false)

Example (navigation with pedestrians):
```bash
ros2 launch cpe631_ros2 cafe.launch.py navigation:=true map_file:=~/ros2_ws/src/cpe631_ros2/maps/cafe.yaml enable_peds:=true
```

## Configurable parameters
### Robot initial position
- Set in `worlds/cafe.world` under the TurtleBot3 include:
  - `<pose>1.0 0.0 0.05 0 0 0</pose>`

### Pedestrian positions and paths
- Static standing human pose in `launch/cafe.launch.py`.
- Moving actor paths in:
  - `models/person_walking_actor_1/model.sdf`
  - `models/person_walking_actor_2/model.sdf`
  - `models/person_walking_actor_3/model.sdf`

### Sensor configuration
- TurtleBot3 model and sensor settings:
  - `models/turtlebot3_burger/model.sdf`
- Lidar resolution, FOV, range, noise are under `<sensor name="hls_lfcd_lds">`.
- IMU noise parameters are under `<sensor name="tb3_imu">`.

### Topics used
- Command velocity: `/cmd_vel`
- Lidar: `/scan`
- Odometry: `/odom`
- TF: `/tf`, `/tf_static`
- Map: `/map`
- Initial pose: `/initialpose`
- AMCL pose: `/amcl_pose`
- Goal: `/goal_pose`

## Nav2 planning configuration
Current Nav2 settings are in:
- `param/nav2_burger.yaml`

This config uses:
- Global planner: `nav2_navfn_planner::NavfnPlanner` (Dijkstra / A*)
- Local controller: `dwb_core::DWBLocalPlanner`
- Behavior tree: `navigate_to_pose_w_replanning_and_recovery.xml`

### How to swap planners / controllers (dynamic environments)
You can replace plugins in `param/nav2_burger.yaml`:
- Global planner options:
  - `nav2_smac_planner/SmacPlannerHybrid`
  - `nav2_smac_planner/SmacPlannerLattice`
- Local controller options:
  - `nav2_regulated_pure_pursuit_controller/RegulatedPurePursuitController`
  - `nav2_mppi_controller::MPPIController`

To better handle dynamic environments:
- Increase obstacle layer update rate in costmaps.
- Ensure obstacle and voxel layers are enabled.
- Use `nav2_collision_monitor` and `velocity_smoother` (already available in the stack).

## Notes
- Pedestrians are disabled in mapping mode by default.
- RViz configuration lives at `rviz/navigation.rviz`.
