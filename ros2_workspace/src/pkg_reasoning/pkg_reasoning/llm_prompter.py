# Based on https://github.com/Auromix/ROS-LLM/blob/ros2-humble/llm_model/llm_model/chatgpt.py

import openai
import anthropic
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pkg_commons.srv import DialogueTurn


class LLMNode(Node):
    def __init__(self):
        super().__init__("chatgpt")

        # subscribers
        self.create_subscription(String, "/state", self.state_callback, 0)
        self.create_subscription(String, "/llm_request", self.llm_request_callback, 0)

        # publishers
        self.state_pub = self.create_publisher(String, "/state", 0)
        self.llm_response_pub = self.create_publisher(String, "/llm_response", 0)

        self.declare_parameter('llm_model', 'test')
        self.model = self.get_parameter('llm_model').value

        # System and Robot state Initialzation
        self.robot_state = "idle"
        self.state = "init"

    def llm_request_callback(self, msg:str):
        '''Callback for LLM request'''
        self.process_LLM_response(msg.data)

    def state_callback(self):
        '''Callback for system state updates'''
        pass

    def process_LLM_response(self, user_input:str):
        response = ""
        if self.model == "chatgpt":
            response = self.prompt_chatgpt(user_input)
        elif self.model == "claude":
            response = self.prompt_claude(user_input)
        elif self.model == "test":
            response = f"Response from test model {time.time()}"
        else:
            raise ValueError(f"Unsupported model: {self.model}")
        self.send_LLM_response(response)

    def send_LLM_response(self, response:str):
        self.llm_response_pub.publish(String(data=response))
        self.get_logger().info(f"Topic: {self.llm_response_pub.topic_name} text: {response}")

    def process_user_input(self, user_input:str) -> str:
        '''Process user input before sending to LLM
            Possible actions: say_ ,attend_ , gesture_  
        '''
        return user_input

    def prompt_chatgpt(self, user_input:str) -> str:
        client = openai.OpenAI()
        content = self.process_user_input(user_input)
        response = client.chat.completions.create(
            model="gpt-5", # gpt-4o , o3
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": content}
            ],
            max_tokens=200,
        )
        output = response.choices[0].message.content
        return output

    def prompt_claude(self, user_input:str):
        client = anthropic.Anthropic()
        content = self.process_user_input(user_input)
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=100, # 1000 words requires around 2000 tokens
            messages=[
                {"role": "user", "content": content}
            ]
        )

        output = response.content[0].text
        return output

def main(args=None):
    rclpy.init(args=args)
    node = LLMNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
