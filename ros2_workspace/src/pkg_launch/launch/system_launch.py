import os
import sys
from pathlib import Path

from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node
from launch.actions import EmitEvent, RegisterEventHandler, Shutdown
from launch.events import matches_action
from launch_ros.events.lifecycle import ChangeState
from launch_ros.event_handlers import OnStateTransition
from lifecycle_msgs.msg import Transition

from pkg_launch.camera_config import CameraConfig
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    ld = LaunchDescription()

#     dialogue_manager = Node(
#             package='pkg_reasoning',
#             namespace='pkg_reasoning',
#             executable='dialogue_manager',
#             name='dialogue_manager',
#     )
#     ld.add_action(dialogue_manager)

#     llm_prompter = Node(
#             package='pkg_reasoning',
#             namespace='pkg_reasoning',
#             executable='llm_prompter',
#             name='llm_prompter',
#             parameters=[
#                 {'llm_model': 'openai'},
#             ]
#     )
#     ld.add_action(llm_prompter)

#     speech_to_text_google = Node(
#             package='pkg_audio_input',
#             namespace='pkg_audio_input',
#             executable='stt_google',
#             name='stt_google',
#             parameters=[
#                 {'device': 0},
#                 {'language': 'en-us'},
#                 {'sample_rate': 44100},
#                 {'channels': 1},
#                 {'start_listening': True}
#             ]
#     )
#     ld.add_action(speech_to_text_google)

    config_file = os.path.join(get_package_share_directory('pkg_launch'), 'config', 'params_default.yaml')
    usb_camera = Node(
            package='usb_cam',
            namespace='',
            executable='usb_cam_node_exe',
            name='laptop_camera',
            output='screen',
            parameters=[config_file],
            remappings=[
                ('/image_raw', '/image'),
                ('/image_raw/compressed', '/image/compressed'),
                ('/image_raw/compressedDepth', '/image/compressedDepth'),
                ('/image_raw/theora', '/image/theora'),
            ],
    )
    ld.add_action(usb_camera)

    face_detection_node = LifecycleNode(
        package='hri_face_detect',
        namespace='',
        name='hri_face_detect',
        executable='hri_face_detect',
        parameters=[
                {'processing_rate': 30},
                {'image_compressed': True},
                {'confidence_threshold': 0.6},
                {'image_scale': 0.5},
                {'face_mesh': False},
                # {'filtering_frame': 'camera_color_optical_frame' },
                {'deterministic_ids': True},
                {'debug': True}
            ],
        # remappings=config["remappings"],
        # arguments=config["arguments"],
        output='both',
        emulate_tty=True,
        on_exit=Shutdown()
    )

    configure_event = EmitEvent(event=ChangeState(
        lifecycle_node_matcher=matches_action(face_detection_node),
        transition_id=Transition.TRANSITION_CONFIGURE))

    activate_event = RegisterEventHandler(OnStateTransition(
        target_lifecycle_node=face_detection_node, goal_state='inactive',
        entities=[EmitEvent(event=ChangeState(
            lifecycle_node_matcher=matches_action(face_detection_node),
            transition_id=Transition.TRANSITION_ACTIVATE))], handle_once=True))

    ld.add_action(face_detection_node)
    ld.add_action(configure_event)
    ld.add_action(activate_event)


#     furnat_bridge_node = Node(
#             package='woz_reception',
#             namespace='robot_furhat',
#             executable='furhat_bridge',
#             name='furhat_bridge',
#             parameters=[
#                 {'robot_type': 'physical'},  # virtual or physical or none
#                 {'furhat_ip': '10.0.1.10'},  
#                 {'language_code': "en-US"},  # en-US, sv-SE
#             ]
#     )   

#     camera_furhat_node = Node(
#             package='woz_reception',
#             namespace='woz_reception',
#             executable='camera_furhat',
#             name='camera_furhat',
#             parameters=[
#                 {'camera_ip': '10.0.1.10:3000'}
#             ]
#     )

#     speech_to_text_vosk = Node(
#             package='pkg_audio_input',
#             namespace='pkg_audio_input',
#             executable='stt_vosk',
#             name='stt_vosk',
#             parameters=[
#                 {'device': 0},
#                 {'language': 'en-us'},
#                 {'sample_rate': 44100},
#                 {'channels': 1},
#                 {'start_listening': False}
#             ]
#     )
#     ld.add_action(speech_to_text_vosk)

    return ld
