# Based on https://github.com/Auromix/ROS-LLM/blob/ros2-humble/llm_model/llm_model/chatgpt.py

import openai
import anthropic
from google import genai

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pkg_commons.srv import DialogueTurn


class LLMNode(Node):
    def __init__(self):
        super().__init__("chatgpt")

        # publishers
        self.state_publisher = self.create_publisher(String, "/state", 0)
        # subscribers
        self.state_subscriber = self.create_subscription(String, "/state", self.state_callback, 0)
        # services
        self.dialogue_service = self.create_service(DialogueTurn, 'dialogue_service', self.dialogue_callback)

    def dialogue_callback(self, request, response):
        response.output_text = self.get_LLM_response(request.input_text)
        self.get_logger().info(f'Incoming request: {request.input_text}')
        return response

    def state_callback(self):
        pass

    def get_LLM_response(self, user_input:str, model:str = "test"):
        if model == "chatgpt":
            return self.chatgpt_response(user_input)
        elif model == "claude":
            return self.claude_response(user_input)
        elif model == "gemini":
            return self.gemini_response(user_input)
        elif model == "test":
            return "Response from test model"
        else:
            raise ValueError(f"Unsupported model: {model}")

    def process_user_input(self, user_input:str) -> str:
        # Here you can add any preprocessing steps if needed
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

    def prompt_gemini(self, user_input:str):
        client = genai.Client()
        content = self.process_user_input(user_input)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=content,
            # config=types.GenerateContentConfig(
            #     thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            # ),
        )
        output = response.text
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

    minimal_service = LLMNode()

    rclpy.spin(minimal_service)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
