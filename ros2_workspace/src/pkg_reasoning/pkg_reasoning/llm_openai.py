# Based on https://github.com/Auromix/ROS-LLM/blob/ros2-humble/llm_model/llm_model/chatgpt.py

import json
import os
import time
import openai
from llm_config.user_config import UserConfig

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class ChatGPTNode(Node):
    def __init__(self):
        super().__init__("chatgpt")

        # publishers
        self.state_pub = self.create_publisher(String, "/state", 0)
        self._pub = self.create_publisher(String, "/user_speech_final", 0)
        self._pub = self.create_publisher(String, "/user_speech_partial", 0)

        self.state_sub = self.create_subscription(String, "/state", self.state_callback, 0)
        self.user_speech_sub = self.create_subscription(String, "/user_speech", self.user_speech_callback, 0)
        # self.user_speech_partial_sub = self.create_subscription(String, "/user_speech_partial", self.user_speech_partial_callback, 0)

        # ChatGPT function call client
        # When function call is detected
        # ChatGPT client will call function call service in robot node
        self.function_call_client = self.create_client(ChatGPT, "/ChatGPT_function_call_service")

        self.function_call_requst = ChatGPT.Request()  # Function call request
        self.get_logger().info("ChatGPT Function Call Server is ready")

        # ChatGPT output publisher
        # When feedback text to user is detected
        # ChatGPT node will publish feedback text to output node
        self.output_publisher = self.create_publisher(String, "ChatGPT_text_output", 10)

        # Chat history
        # The chat history contains user & ChatGPT interaction information
        # Chat history is stored in a JSON file in the user_config.chat_history_path
        # There is a maximum word limit for chat history
        # And the upper limit is user_config.chat_history_max_length
        # TODO: Longer interactive content should be stored in the JSON file
        # exceeding token limit, waiting to update @Herman Ye
        self.start_timestamp = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        self.chat_history_file = os.path.join(
            config.chat_history_path, f"chat_history_{self.start_timestamp}.json"
        )
        self.write_chat_history_to_json()
        self.get_logger().info(f"Chat history saved to {self.chat_history_file}")

        # Function name
        self.function_name = "null"
        # Initialization ready
        self.publish_string("llm_model_processing", self.initialization_publisher)
