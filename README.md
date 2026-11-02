Before every step: build and source the workspace

cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash

Step 1 — Depth camera and IMU
ros2 launch diffdrive_bot display.launch.py

Check the depth camera sits 0.215 m behind the chassis, turned half a turn:
ros2 run tf2_ros tf2_echo base_link depth_camera_link

Run the simulation, then in RViz add an Image display for /depth_camera/image and a PointCloud2 display for /depth_camera/points:
ros2 launch diffdrive_bot gazebo.launch.py

Check the IMU publishes at 50 Hz and shows ~9.8 on linear_acceleration.z:
ros2 topic hz /imu
ros2 topic echo /imu

Step 2 — turn_away node
Terminal 1 — start the robot:
ros2 launch diffdrive_bot control.launch.py

Terminal 2 — run your node:
ros2 run my_robot_nodes turn_away

Step 3 — Parameters
With turn_away running, list and change the speeds (changes take effect on the next message):
ros2 param list /turn_away
ros2 param set /turn_away forward_speed 0.4
ros2 param set /turn_away turn_speed 0.8

Step 4 — Custom message
Check the message definition and watch it being published:
ros2 interface show my_robot_interfaces/msg/RobotStatus
ros2 topic echo /robot_status

Step 5 — Services
Turn the node on/off and change the turn speed (the 3.0 call is rejected, the 1.0 call is accepted):
ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: true}"
ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 1.0}"
ros2 service call /set_turn_speed my_robot_interfaces/srv/SetTurnSpeed "{turn_speed: 3.0}"
ros2 service call /turn_away_enable std_srvs/srv/SetBool "{data: false}"

Step 6 — rotate_server action
Terminal 1 — start the action server:
ros2 run my_robot_nodes rotate_server

Terminal 2 — send a quarter-turn goal and watch the feedback climb to about 1.57:
ros2 action send_goal --feedback /rotate my_robot_interfaces/action/Rotate "{angle: 1.57}"

Check the new heading:
ros2 run tf2_ros tf2_echo odom base_link

Step 7 — square_driver + launch file
One command starts everything (robot, rotate_server, square_driver) and drives a square:
ros2 launch my_robot_nodes square.launch.py side_length:=0.8


The robot drives the square and comes back close to where it started. A side of up to 1 m fits the arena.