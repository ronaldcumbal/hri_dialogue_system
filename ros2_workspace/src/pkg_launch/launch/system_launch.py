from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler, Shutdown
from launch.conditions import IfCondition
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.events.lifecycle import ChangeState
from launch_ros.event_handlers import OnStateTransition
from lifecycle_msgs.msg import Transition

from pkg_launch.camera_config import CameraConfig


def generate_launch_description():

    use_audio = LaunchConfiguration('use_audio')
    use_reasoning = LaunchConfiguration('use_reasoning')
    stt_backend = LaunchConfiguration('stt_backend')
    llm_model = LaunchConfiguration('llm_model')

    ld = LaunchDescription([
        DeclareLaunchArgument(
            'use_audio', default_value='false',
            description='Start the speech-to-text node (stt_backend selects which one)'),
        DeclareLaunchArgument(
            'use_reasoning', default_value='false',
            description='Start the dialogue_manager and llm_prompter nodes'),
        DeclareLaunchArgument(
            'stt_backend', default_value='google',
            description="Speech-to-text backend to use when use_audio:=true: 'google' or 'vosk'"),
        DeclareLaunchArgument(
            'llm_model', default_value='test',
            description="LLM backend for llm_prompter: 'test', 'openai', 'anthropic' or 'google'"),
    ])

    camera_config = CameraConfig(filename='params_logitech.yaml', name='laptop_camera')
    usb_camera = Node(
            package='usb_cam',
            namespace='',
            executable='usb_cam_node_exe',
            name=camera_config.name,
            output='screen',
            parameters=[str(camera_config.param_path)],
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
                {'deterministic_ids': True},
                {'debug': True}
            ],
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

    dialogue_manager = Node(
            package='pkg_reasoning',
            namespace='pkg_reasoning',
            executable='dialogue_manager',
            name='dialogue_manager',
            condition=IfCondition(use_reasoning),
    )
    ld.add_action(dialogue_manager)

    llm_prompter = Node(
            package='pkg_reasoning',
            namespace='pkg_reasoning',
            executable='llm_prompter',
            name='llm_prompter',
            parameters=[{'llm_model': llm_model}],
            condition=IfCondition(use_reasoning),
    )
    ld.add_action(llm_prompter)

    speech_to_text_google = Node(
            package='pkg_audio_input',
            namespace='pkg_audio_input',
            executable='stt_google',
            name='stt_google',
            parameters=[
                {'device': 0},
                {'language': 'en-us'},
                {'sample_rate': 44100},
                {'channels': 1},
                {'start_listening': True}
            ],
            condition=IfCondition(PythonExpression(
                ["'", use_audio, "' == 'true' and '", stt_backend, "' == 'google'"])),
    )
    ld.add_action(speech_to_text_google)

    speech_to_text_vosk = Node(
            package='pkg_audio_input',
            namespace='pkg_audio_input',
            executable='stt_vosk',
            name='stt_vosk',
            parameters=[
                {'device': 0},
                {'language': 'en-us'},
                {'sample_rate': 44100},
                {'channels': 1},
                {'start_listening': True}
            ],
            condition=IfCondition(PythonExpression(
                ["'", use_audio, "' == 'true' and '", stt_backend, "' == 'vosk'"])),
    )
    ld.add_action(speech_to_text_vosk)

    return ld
