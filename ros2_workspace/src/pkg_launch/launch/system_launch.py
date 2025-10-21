
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    ld = LaunchDescription()

    dialogue_manager = Node(
            package='pkg_reasoning',
            namespace='pkg_reasoning',
            executable='dialogue_manager',
            name='dialogue_manager',
    )
    ld.add_action(dialogue_manager)

    llm_prompter = Node(
            package='pkg_reasoning',
            namespace='pkg_reasoning',
            executable='llm_prompter',
            name='llm_prompter',
            parameters=[
                {'llm_model': 'openai'},
            ]

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
            ]
    )
    ld.add_action(speech_to_text_google)

    # furnat_bridge_node = Node(
    #         package='woz_reception',
    #         namespace='robot_furhat',
    #         executable='furhat_bridge',
    #         name='furhat_bridge',
    #         parameters=[
    #             {'robot_type': 'physical'},  # virtual or physical or none
    #             {'furhat_ip': '10.0.1.10'},  
    #             {'language_code': "en-US"},  # en-US, sv-SE
    #         ]
    # )   

    # camera_furhat_node = Node(
    #         package='woz_reception',
    #         namespace='woz_reception',
    #         executable='camera_furhat',
    #         name='camera_furhat',
    #         parameters=[
    #             {'camera_ip': '10.0.1.10:3000'}
    #         ]
    # )

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
 
