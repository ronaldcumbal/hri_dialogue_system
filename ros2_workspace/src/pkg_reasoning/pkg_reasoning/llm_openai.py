# Based on https://github.com/Auromix/ROS-LLM/blob/ros2-humble/llm_model/llm_model/chatgpt.py

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# import openai
from pkg_commons.srv import DialogueTurn


class ChatGPTNode(Node):
    def __init__(self):
        super().__init__("chatgpt")

        # publishers
        self.state_publisher = self.create_publisher(String, "/state", 0)
        # self._pub = self.create_publisher(String, "/user_speech_final", 0)

        # subscribers
        self.state_subscriber = self.create_subscription(String, "/state", self.state_callback, 0)
        self.user_speech_subscriber = self.create_subscription(String, "/user_speech", self.user_speech_callback, 0)
        # self.user_speech_partial_sub = self.create_subscription(String, "/user_speech_partial", self.user_speech_partial_callback, 0)

        self.dialogue_service = self.create_service(DialogueTurn, 'dialogue_service', self.dialogue_callback)

    def dialogue_callback(self, request, response):
        response.output_text = self.chatgpt_response(request.input_text)
        self.get_logger().info(f'Incoming request: {request.input_text}')
        return response

    def state_callback(self):
        pass

    def user_speech_callback(self):
        pass

    def chatgpt_response(self, prompt):
        return "This is a response"

        

def main(args=None):
    rclpy.init(args=args)

    minimal_service = ChatGPTNode()

    rclpy.spin(minimal_service)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
