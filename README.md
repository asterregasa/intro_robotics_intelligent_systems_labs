# Introduction to Robotics and Intelligent Systems Labs

ROS 2 and Gazebo lab material for **Introduction to Robotics and Intelligent Systems**, a course in the
BSc in Software Engineering at Addis Ababa University, academic year 2026.

| Program | Course | Lecturer | Lab Assistant |
|---------|--------|----------|---------------|
| BSc in Software Engineering | Introduction to Robotics and Intelligent Systems | Mohammed Sraj (MSc AI), part-time | Mohammed Sraj (MSc AI) |

Each lab session has a folder of its own, with its ROS 2 packages, a README that walks through them,
and an exercise. Start with the README of the lab folder for your session.

| Lab | Topic |
|-----|-------|
| [lab_01](lab_01) | ROS 2 and custom robot simulation: ROS 2 concepts, a differential-drive robot in Gazebo, and nodes that use topics, services and actions |

## Requirements

- Ubuntu 22.04 with ROS 2 Humble
- Gazebo Harmonic with its ROS 2 packages (`ros-humble-ros-gzharmonic`)

Each lab's README lists anything else it needs.

## Getting started

Clone the repository into the `src` folder of a ROS 2 workspace:

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/berito/intro_robotics_intelligent_systems_labs.git
```

A new lab folder is added for every lab session. To get it, pull the repository:

```bash
cd ~/ros2_ws/src/intro_robotics_intelligent_systems_labs
git pull
```

colcon finds the packages of every lab in the repository. Build only the lab you are working on, as
its README shows; for Lab 1:

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to diffdrive_bot
source install/setup.bash
```

## License

The packages are released under the MIT license; see [LICENSE](LICENSE).
