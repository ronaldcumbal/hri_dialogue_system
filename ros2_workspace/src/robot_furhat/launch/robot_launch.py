
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()

    furnat_bridge_node = Node(
            package='robot_furhat',
            namespace='robot_furhat',
            executable='furhat_bridge',
            name='furhat_bridge',
            parameters=[
                {'robot_type': 'physical'},  # virtual or physical or none
                {'furhat_ip': '10.0.1.10'},  
                {'language_code': "en-US"},  # en-US, sv-SE
            ]
    )   
    ld.add_action(furnat_bridge_node)
    return ld   
 