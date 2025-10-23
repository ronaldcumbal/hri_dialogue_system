import rclpy
from rclpy.node import Node

from pkg_commons.srv import DialogueTurn
from std_msgs.msg import String

import threading
from queue import Queue, Full

class DialogueManagerNode(Node):

    def __init__(self):
        super().__init__('dialogue_manager')
        # subscribers
        self.create_subscription(String, "/state", self.state_callback, 0)
        self.create_subscription(String, "/user_speech", self.user_speech_callback, 0)
        self.create_subscription(String, "/user_speech_partial", self.user_speech_partial_callback, 0)
        self.create_subscription(String, "/robot_state", self.robot_state_callback, 0)
        self.create_subscription(String, "/llm_response", self.llm_response_callback, 0)

        # publishers
        self.robot_action_pub = self.create_publisher(String, "/robot_action", 0)
        self.llm_request_pub = self.create_publisher(String, "/llm_request", 0)

        self.user_utterance_buffer = Queue(maxsize=10)

        # System and Robot state Initialzation
        self.robot_state = "idle"
        self.state = "init"

        self.timer_running = False
        self.lock = threading.Lock()
        self.timer = None

        self.get_logger().info(f"Dialogue Manager initialized")

    def user_speech_partial_callback(self, msg):
        ''' Callback, get quick responses if partial results match with FAQ or known commands'''
        pass

    def user_speech_callback(self, msg):
        '''Callback for TTS final results'''
        self.user_utterance_buffer.put(msg.data)

        with self.lock:
            if not self.timer_running:
                self.process_llm_request()

    def llm_response_callback(self, msg:str):
        '''Callback for LLM response'''
        self.process_robot_action(msg.data)
        print(f"LLM ----------: {msg.data}")

    def robot_state_callback(self, msg:str):
        '''Callback for robot state updates'''
        self.robot_state = msg.data

    def state_callback(self, msg:str):
        '''Callback for system state updates'''
        self.state = msg.data

    def process_robot_action(self, action:str):
        '''Process LLM response and decide robot action'''
        if self.robot_state == "idle":
            action = action
        else:
            action = action
        self.send_robot_action(action)

    def process_llm_request(self):
        if not self.user_utterance_buffer.empty():
            text = self.user_utterance_buffer.get()
            self.send_llm_request(text)

    def send_llm_request(self, text:str):
        self.llm_request_pub.publish(String(data=text))
        self.get_logger().info(f"Topic: {self.llm_request_pub.topic_name} text: {text}")

    def send_robot_action(self, text:str):
        '''Send action options: say_ attend_ gesture_ ... '''
        self.robot_action_pub.publish(String(data=text))
        self.get_logger().info(f"Topic: {self.robot_action_pub.topic_name} text: {text}")



def main(args=None):
    rclpy.init(args=args)
    node = DialogueManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()