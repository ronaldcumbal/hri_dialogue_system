
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='woz_reception',
            namespace='woz_reception',
            executable='wizard_interface',
            name='wizard_interface',
        )
    ])
