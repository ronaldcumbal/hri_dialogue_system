import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from pkg_reasoning.llm_clients import create_llm_client


class LLMNode(Node):
    def __init__(self):
        super().__init__("llm_prompter")

        # subscribers
        self.create_subscription(String, "/state", self.state_callback, 0)
        self.create_subscription(String, "/llm_request", self.llm_request_callback, 0)

        # publishers
        self.state_pub = self.create_publisher(String, "/state", 0)
        self.llm_response_pub = self.create_publisher(String, "/llm_response", 0)

        self.declare_parameter('llm_model', 'test')
        model_name = self.get_parameter('llm_model').value
        self.client = create_llm_client(model_name)
        self.get_logger().info(f"Working with {model_name.upper()} model")

        # System and Robot state Initialzation
        self.robot_state = "idle"
        self.state = "init"

    def llm_request_callback(self, msg: String):
        '''Callback for LLM request'''
        response = self.client.generate(self.process_user_input(msg.data))
        self.send_llm_response(response)

    def state_callback(self, msg: String):
        '''Callback for system state updates'''
        self.state = msg.data

    def send_llm_response(self, response: str):
        self.llm_response_pub.publish(String(data=response))
        self.get_logger().info(f"Topic: {self.llm_response_pub.topic_name} text: {response}")

    def process_user_input(self, user_input: str) -> str:
        '''Process user input before sending to LLM
            Possible actions: say_ ,attend_ , gesture_
        '''
        return user_input


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
