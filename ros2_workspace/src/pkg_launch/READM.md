## Create a ROS 2 package
```
cd ~/ros2_workspace/src
ros2 pkg create pkg_launch --build-type ament_python --dependencies rclpy
```

Then build the workspace:

```
cd ~/ros2_workspace
colcon build
source install/setup.bash
```

## Create a `launch` directory
```
cd ~/ros2_workspace/src/pkg_launch
mkdir launch

```

## Create a launch file (Python example)
Write launch file, in this calse `system_launch.py`

## Install the launch file
Modify `setup.py` it to include your launch folder (3rd line in data_files):

```
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/pkg_launch/launch', ['launch/system_launch.py']),
    ],
```
