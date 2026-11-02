**Program:** BSc in Software Engineering

**Course:** Introduction to Robotics and Intelligent Systems

**Lecturer:** Mohammed Sraj (MSc AI)

**Lab Assistant:** Mohammed Sraj (MSc AI)

**Academic year:** 2026

# Lab 1 Exercise: Program diffdrive_bot

In this exercise you first give diffdrive_bot two more sensors, a depth camera and an IMU, by
extending its URDF. Then you write your own ROS 2 packages for the robot. You start with a node that
reacts to obstacles and add one idea at a time: parameters, a message type of your own, a service, an
action server, and finally an action client that drives the robot around a square.

Each step has a working example in this folder. Read the example first, then write your own version;
do not copy the example and rename it.

## Before you start

Finish the [diffdrive_bot README](diffdrive_bot/README.md) up to the end of Step 11, so that the
robot, its nodes and the `ros2` tools all work on your computer.

You need the Python versions of these official ROS 2 tutorials, listed on the documentation site for
[Humble](https://docs.ros.org/en/humble/Tutorials.html):

- URDF: Building a visual robot model, Building a movable robot model, Adding physical and collision
  properties, Using Xacro, and Using URDF with robot_state_publisher
- Creating a package
- Writing a simple publisher and subscriber
- Writing a simple service and client
- Creating custom msg and srv files
- Using parameters in a class
- Creating an action
- Writing an action server and client
- Creating a launch file, and Integrating launch files into ROS 2 packages

## Your project folder

You do the whole exercise in a folder of your own, `lab1_exercise`, in the `src` folder of your
workspace. It holds your own copy of the two lab packages, diffdrive_bot and lab_interfaces, which
you change and use, and the two packages you write. This folder is what you hand in at the end.

Create the folder and copy the lab packages into it:

```bash
cd ~/ros2_ws/src
mkdir lab1_exercise
cp -r intro_robotics_intelligent_systems_labs/lab_01/diffdrive_bot intro_robotics_intelligent_systems_labs/lab_01/lab_interfaces lab1_exercise/
touch intro_robotics_intelligent_systems_labs/lab_01/COLCON_IGNORE
```

colcon refuses to build two packages with the same name, so the `COLCON_IGNORE` file tells it to skip
the lab's own lab_01 packages; from now on it builds your copies. Because the packages moved, build
the workspace once from scratch:

```bash
cd ~/ros2_ws
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

The examples this exercise points to are the same files in your copy of diffdrive_bot and
lab_interfaces.

## Step 1: Add a depth camera and an IMU to the robot

In this step you change your copy of diffdrive_bot, in `lab1_exercise/diffdrive_bot`: its URDF, its
world and its bridge configuration. Comments marked `TODO (exercise Step 1)` in each of these files
show where your additions go.

Add two sensors to `urdf/diffdrive_bot.urdf.xacro`:

1. A **depth camera** on the back face of the chassis, looking backwards, the opposite way to the
   front camera. Give it a link, `depth_camera_link`, the same size as `camera_link`, with a visual,
   a collision and an inertial, and a fixed joint to `base_link` that turns it half a turn about the
   z axis. Its Gazebo sensor has type `depth_camera`, publishes on `/depth_camera` at 10 Hz, and has
   a 320 x 240 image in the `R_FLOAT32` format with a range of 0.1 to 10 m. Set its
   `camera_info_topic` to `/depth_camera/camera_info`; otherwise Gazebo publishes it on `/camera_info`.
2. An **IMU** at the centre of the chassis. Give it a link, `imu_link`, and a fixed joint to
   `base_link`. Its Gazebo sensor has type `imu` and publishes on `/imu` at 50 Hz.

Gazebo only simulates an IMU when the world loads the IMU system, so add this line next to the other
plugins in `worlds/obstacles.sdf`:

```xml
<plugin filename="gz-sim-imu-system" name="gz::sim::systems::Imu" />
```

Then add the new topics to `config/bridge.yaml`, from Gazebo to ROS 2:

| Gazebo topic | Gazebo type | ROS 2 topic | ROS 2 type |
|--------------|-------------|-------------|------------|
| `/depth_camera` | `gz.msgs.Image` | `/depth_camera/image` | `sensor_msgs/msg/Image` |
| `/depth_camera/points` | `gz.msgs.PointCloudPacked` | `/depth_camera/points` | `sensor_msgs/msg/PointCloud2` |
| `/depth_camera/camera_info` | `gz.msgs.CameraInfo` | `/depth_camera/camera_info` | `sensor_msgs/msg/CameraInfo` |
| `/imu` | `gz.msgs.IMU` | `/imu` | `sensor_msgs/msg/Imu` |

Example: `camera_link`, its joint and its `<gazebo>` sensor block in the URDF show the same pattern for
the front camera, and the camera entries in `bridge.yaml` show the bridge format.

**Check.** Rebuild and source the workspace first, as for every step below.

1. `ros2 launch diffdrive_bot display.launch.py` shows the depth camera on the back of the robot, and
   RViz draws the frames `depth_camera_link` and `imu_link`.
2. `ros2 run tf2_ros tf2_echo base_link depth_camera_link` shows the camera 0.215 m behind the centre
   of the chassis, turned half a turn.
3. Start `gazebo.launch.py`. The robot starts with the wall behind it, so the depth camera sees the
   wall. In RViz, add an Image display for `/depth_camera/image` and a PointCloud2 display for
   `/depth_camera/points`.
4. `ros2 topic hz /imu` shows about 50 Hz. `ros2 topic echo /imu` shows a `linear_acceleration.z` of
   about 9.8 while the robot stands still, and an `angular_velocity.z` that is not zero while you turn
   it with the keyboard.

## Your packages

You write two packages, in your `lab1_exercise` folder next to your copies of the lab packages:

| Package | Build type | Holds |
|---------|------------|-------|
| `my_robot_interfaces` | `ament_cmake` | your message, service and action types |
| `my_robot_nodes` | `ament_python` | your nodes and your launch file |

The interface types need a CMake package because only CMake packages can generate them. Look at
[lab_interfaces/CMakeLists.txt](lab_interfaces/CMakeLists.txt) and
[lab_interfaces/package.xml](lab_interfaces/package.xml) to see what such a package needs.

Create both packages:

```bash
cd ~/ros2_ws/src/lab1_exercise
ros2 pkg create --build-type ament_cmake --license MIT my_robot_interfaces
ros2 pkg create my_robot_nodes --build-type ament_python --license MIT \
  --dependencies rclpy geometry_msgs nav_msgs std_srvs lab_interfaces my_robot_interfaces
```

For every step, rebuild, source, start the robot and run your node in a second terminal:

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch diffdrive_bot control.launch.py
```

Your nodes and the diffdrive_bot nodes all publish to `/cmd_vel`. Only one of them should drive the
robot at a time, so while your nodes drive it, do not switch on `/drive_enable` and do not send goals
to `/drive_distance` yourself. The diffdrive_bot nodes publish nothing while they are idle.

## Step 2: A node that turns away from obstacles

Write a node, `turn_away`, that subscribes to `/obstacle` (`lab_interfaces/msg/ObstacleInfo`) and
publishes to `/cmd_vel` (`geometry_msgs/msg/Twist`). Each time an `ObstacleInfo` message arrives:

- if `too_close` is false, drive forward at 0.2 m/s;
- if `too_close` is true, stop moving forward and turn on the spot at 0.5 rad/s, away from the
  obstacle. `angle` is positive when the obstacle is to the left, so turn right then
  (negative `angular.z`), and left otherwise.

Example: [drive_controller.py](diffdrive_bot/scripts/drive_controller.py) subscribes to `/obstacle`
and publishes to `/cmd_vel`.

**Check.** The robot drives towards the red box, turns before it reaches it, and drives on. Open
`rqt_graph` and find your node between `/obstacle` and `/cmd_vel`.

## Step 3: Parameters

Replace the two fixed speeds with parameters, `forward_speed` (default 0.2 m/s) and `turn_speed`
(default 0.5 rad/s). Read them each time a message arrives, not once at start-up, so a change takes
effect at once.

Example: [obstacle_detector.py](diffdrive_bot/scripts/obstacle_detector.py) reads its parameters in
the scan callback.

**Check.** While the robot drives, change a parameter and watch the robot change speed:

```bash
ros2 param list /turn_away
ros2 param set /turn_away forward_speed 0.4
```

## Step 4: A message type of your own

In `my_robot_interfaces`, define `msg/RobotStatus.msg`:

```
string state               # "forward", "turning" or "stopped"
float32 obstacle_distance  # m, distance to the nearest obstacle in front
```

`turn_away` publishes a `RobotStatus` on `/robot_status` each time an `ObstacleInfo` message arrives.
The state `stopped` is used from Step 5 on.

Example: [ObstacleInfo.msg](lab_interfaces/msg/ObstacleInfo.msg) is defined in lab_interfaces and
published by [obstacle_detector.py](diffdrive_bot/scripts/obstacle_detector.py).

**Check.**

```bash
ros2 interface show my_robot_interfaces/msg/RobotStatus
ros2 topic echo /robot_status
```

## Step 5: Services

Give `turn_away` two services.

1. `/turn_away_enable` (`std_srvs/srv/SetBool`) switches the node on and off. The node starts
   switched off. While it is off it publishes no velocities, apart from one zero velocity when it is
   switched off, and its state is `stopped`.
2. `/set_turn_speed` with a service type of your own, `srv/SetTurnSpeed.srv` in
   `my_robot_interfaces`:

   ```
   float32 turn_speed   # rad/s
   ---
   bool success
   string message
   ```

   It rejects a speed of zero or less, or above a `max_turn_speed` parameter (default 1.5 rad/s).
   An accepted speed is stored as the `turn_speed` parameter.

Example: [drive_controller.py](diffdrive_bot/scripts/drive_controller.py) serves `/drive_enable` and
`/set_speed`, and [SetSpeed.srv](lab_interfaces/srv/SetSpeed.srv) is its service type.

**Check.**

```bash
ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: true}"
ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 1.0}"
ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 3.0}"
ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: false}"
```

The second call is accepted and the third is rejected. After the last call the robot stops.

## Step 6: An action server

In `my_robot_interfaces`, define `action/Rotate.action`:

```
float32 angle     # goal, rad, positive turns left
---
float32 turned    # result, rad
---
float32 turned    # feedback, rad
```

Write a node, `rotate_server`, that serves `/rotate`. It turns the robot on the spot at a
`turn_speed` parameter (default 0.5 rad/s) until it has turned through the goal angle, sends the angle
turned so far as feedback, stops, and returns the angle turned. It rejects a goal of zero and stops
the robot when the goal is canceled.

Measure the turn with the yaw angle from `/odom`. The yaw jumps from pi to -pi as the robot turns
past backwards, so add up the small change in yaw between one odometry message and the next rather
than subtracting the start yaw from the current one.

Example: [drive_distance_server.py](diffdrive_bot/scripts/drive_distance_server.py) serves
`/drive_distance`. Its functions `yaw_from_quaternion` and `angle_difference` show how to get the yaw
and how to take the difference of two angles. It also shows why the server needs a
`MultiThreadedExecutor`.

**Check.** The robot turns a quarter turn to the left, and the feedback climbs to about 1.57:

```bash
ros2 action send_goal --feedback /rotate my_robot_interfaces/action/Rotate "{angle: 1.57}"
```

`ros2 run tf2_ros tf2_echo odom base_link` shows the new heading.

## Step 7: An action client and a launch file

Write a node, `square_driver`, that drives the robot around a square. It is a client of two actions:
`/drive_distance` from diffdrive_bot and your `/rotate`. Four times over, it sends a `DriveDistance`
goal of one side length, waits for the result, then sends a `Rotate` goal of a quarter turn to the
left and waits for that result. The side length is a parameter, `side_length` (default 0.5 m). If a
goal does not succeed, the node stops and logs which side it was on.

Send each goal only when the one before it has finished.
[drive_distance_client.py](diffdrive_bot/scripts/drive_distance_client.py) shows how to send one goal
and wait for its result; your node does the same eight times.

Then write a launch file, `square.launch.py`, in `my_robot_nodes`. It includes diffdrive_bot's
`control.launch.py` and starts `rotate_server` and `square_driver`, with `side_length` as a launch
argument. An `ament_python` package installs launch files only when they are listed in `data_files` in
its `setup.py`, as the launch tutorial shows.

Example: [control.launch.py](diffdrive_bot/launch/control.launch.py) includes `gazebo.launch.py` and
passes launch arguments to its nodes as parameters.

**Check.** One command starts everything, and the robot drives a square and comes back close to where
it started:

```bash
ros2 launch my_robot_nodes square.launch.py side_length:=0.8
```

From the start position there is room for a square of up to 1 m a side.

## Hand in

Make your `lab1_exercise` folder a Git repository and push it to GitHub. It holds four packages: your
changed diffdrive_bot, lab_interfaces, `my_robot_interfaces` and `my_robot_nodes`, so it builds on its
own in the `src` folder of any workspace. Add a README that says how to build the packages and how to
run each step. Add a screenshot of RViz showing the depth image and point
cloud from Step 1, and a screenshot of `rqt_graph` while `square.launch.py` runs. Write what did not
work and why you think so. Share your exercise by sending the GitHub URL of this repository.
