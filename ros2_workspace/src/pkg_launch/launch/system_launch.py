from launch import LaunchDescription
from launch_ros.actions import LifecycleNode, Node
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler, Shutdown
from launch.conditions import IfCondition
from launch.events import matches_action
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.events.lifecycle import ChangeState
from launch_ros.event_handlers import OnStateTransition
from lifecycle_msgs.msg import Transition

from pkg_launch.camera_config import CameraConfig


def generate_launch_description():

    use_reasoning = LaunchConfiguration('use_reasoning')
    llm_model = LaunchConfiguration('llm_model')
    use_audio = LaunchConfiguration('use_audio')
    stt_backend = LaunchConfiguration('stt_backend')
    whisper_model = LaunchConfiguration('whisper_model')
    microphone_device = LaunchConfiguration('microphone_device')

    ld = LaunchDescription([
        DeclareLaunchArgument(
            'use_reasoning', default_value='false',
            description='Start the dialogue_manager and llm_prompter nodes'),
        DeclareLaunchArgument(
            'llm_model', default_value='test',
            description="LLM backend for llm_prompter: 'test', 'openai', 'anthropic' or 'google'"),
        DeclareLaunchArgument(
            'use_audio', default_value='false',
            description='Start the speech-to-text nodes selected by stt_backend'),
        DeclareLaunchArgument(
            'stt_backend', default_value='whisper',
            description="Speech-to-text backend to use when use_audio:=true: "
                        "'whisper' or 'speechmatics'"),
        DeclareLaunchArgument(
            'whisper_model', default_value='small',
            description="WhisperLive model for stt_whisper_client, e.g. 'tiny', 'base', "
                        "'small', 'medium', 'large-v3'"),
        DeclareLaunchArgument(
            'microphone_device', default_value='-1',
            description='PyAudio input device index, used by whichever stt_backend '
                        'is selected; -1 = default input device'),
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

    def stt_backend_condition(name):
        return IfCondition(PythonExpression(
            ["'", use_audio, "' == 'true' and '", stt_backend, f"' == '{name}'"]))

    stt_whisper_server = Node(
            package='pkg_audio_input',
            namespace='pkg_audio_input',
            executable='stt_whisper_server',
            name='stt_whisper_server',
            output='screen',
            condition=stt_backend_condition('whisper'),
    )
    ld.add_action(stt_whisper_server)

    stt_whisper_client = Node(
            package='pkg_audio_input',
            namespace='pkg_audio_input',
            executable='stt_whisper_client',
            name='stt_whisper_client',
            output='screen',
            parameters=[{
                'model': whisper_model,
                'device': ParameterValue(microphone_device, value_type=int),
            }],
            condition=stt_backend_condition('whisper'),
    )
    ld.add_action(stt_whisper_client)

    stt_speechmatics = Node(
            package='pkg_audio_input',
            namespace='pkg_audio_input',
            executable='stt_speechmatics',
            name='stt_speechmatics',
            output='screen',
            parameters=[{
                'device': ParameterValue(microphone_device, value_type=int),
            }],
            condition=stt_backend_condition('speechmatics'),
    )
    ld.add_action(stt_speechmatics)

    return ld
