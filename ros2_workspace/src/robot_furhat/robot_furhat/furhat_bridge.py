import os
import json
import random
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from furhat_remote_api import FurhatRemoteAPI

class FurhatBridgeNode(Node):

    def __init__(self):
        super().__init__('furhat_bridge')
        self.publisher_ = self.create_publisher(String, 'furhat_bridge', 10)

        self.robot = "virtual"
        self.robot = None

        if self.robot == "physical":
            self.robot_present = True
            robot_IP = "192.168.0.10"
            self.furhat = FurhatRemoteAPI(host=robot_IP)
        elif self.robot == "virtual":
            self.robot_present = True
            self.furhat = FurhatRemoteAPI(host="localhost")
        else:
            self.robot_present = False

        # if self.language_code == "en-US":
        #     voice = 'Salli (en-US) - Amazon Polly'
        # elif self.language_code == "sv-SE":
        #     voice = 'Astrid (sv-SE) - Amazon Polly'

        if self.robot_present:
            self.furhat.set_voice(name='Salli (en-US) - Amazon Polly')

        self.attend_locations = { 'left': "-0.7,0.14,2.0",
                                  'right': "0.5,0.14,2.0",
                                  'away': "0.1,0.1,2.0",
                                  'all': "0.0,0.2,2.0",
                                  'screen': "0.7,0.2,2.0"}

        self.create_subscription(String, 'robot_speak', self.robot_speak_callback, 10)
        self.create_subscription(String, 'robot_gesture', self.robot_gesture_callback, 10)
        self.create_subscription(String, 'robot_attend', self.robot_attend_callback, 10)
        self.create_subscription(String, 'robot_stop', self.robot_stop_callback, 10)

        self.get_logger().info(f'wizard_interface NODE has been started')

    def robot_speak_callback(self, msg):
        text = msg.text
        if self.robot_present:
            self.furhat.say(text=text)
        else:
            self.get_logger().info(f"furhat_bridge text: {text}")

    def robot_gesture_callback(self, msg):
        gesture = msg.text
        if self.robot_present:
            self.furhat.gesture(name=gesture)
        else:
            self.get_logger().info(f"furhat_bridge gesture: {gesture}")

    def robot_attend_callback(self, msg):
        direction = msg.data 
        if self.robot_present:
            if direction== "attend_other":
                if len(self.furhat.get_users())>1:
                    self.furhat.attend(user="OTHER")
                else:
                    self.furhat.attend(location=self.attend_locations['left'])
            if direction == "attend_user":
                self.furhat.attend(user="CLOSEST")
        else:
            self.get_logger().info(f"furhat_bridge attend: {direction}")

    def robot_stop_callback(self, msg):
        if self.robot_present:
            self.furhat.stop()
        else:
            self.get_logger().info(f"furhat_bridge stop")

def main(args=None):
    rclpy.init(args=args)
    global furhat_bridge_node 
    furhat_bridge_node= FurhatBridgeNode()
    rclpy.spin(furhat_bridge_node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
