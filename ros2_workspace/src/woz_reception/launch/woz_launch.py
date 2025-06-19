
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    ld = LaunchDescription()

    wizard_interface_node = Node(
            package='woz_reception',
            namespace='woz_reception',
            executable='wizard_interface',
            name='wizard_interface',
    )
    
    furnat_bridge_node = Node(
            package='woz_reception',
            namespace='robot_furhat',
            executable='furhat_bridge',
            name='furhat_bridge',
            parameters=[
                {'robot_type': 'physical'},  # virtual or physical or none
                {'furhat_ip': '10.0.1.10'},  
                {'language_code': "en-US"},  # en-US, sv-SE
            ]
    )   

    camera_furhat_node = Node(
            package='woz_reception',
            namespace='woz_reception',
            executable='camera_furhat',
            name='camera_furhat',
            parameters=[
                {'camera_ip': '10.0.1.10:3000'}
            ]
    )

    microphone_furhat_node = Node(
            package='woz_reception',
            namespace='woz_reception',
            executable='microphone_furhat',
            name='microphone_furhat',
            parameters=[
                {'camera_ip': '10.0.1.10:3001'}
            ]
    )

    ld.add_action(wizard_interface_node)
    ld.add_action(furnat_bridge_node)
    ld.add_action(camera_furhat_node)
    ld.add_action(microphone_furhat_node)
    return ld   
 
