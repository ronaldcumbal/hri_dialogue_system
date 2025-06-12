
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='robot_furhat',
            namespace='robot_furhat',
            executable='furhat_bridge',
            name='furhat_bridge',
        )
    ])
