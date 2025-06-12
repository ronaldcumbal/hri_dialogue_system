import os
import json
import random
import threading
from queue import Queue, Full

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from furhat_remote_api import FurhatRemoteAPI

class FurhatBridgeNode(Node):

    def __init__(self):
        super().__init__('furhat_bridge')
        # self.publisher_ = self.create_publisher(String, 'furhat_bridge', 10)
        self.create_subscription(String, '/robot_furhat/robot_action', self.robot_action_callback, 10)
        self.create_subscription(String, '/robot_furhat/robot_stop', self.robot_stop_callback, 10)
        self.get_logger().info(f'furhat_bridge NODE has been started')

        self.action_buffer = Queue(maxsize=5)
        self.action_timer = self.create_timer(1.5, self.action_timer_callback)

        self.declare_parameter('robot_type', 'virtual')
        self.declare_parameter('furhat_ip', 'localhost')
        self.declare_parameter('language_code', 'en-US')

        self._robot_type = self.get_parameter('robot_type').value
        self._furhat_ip = self.get_parameter('furhat_ip').value
        self._language = self.get_parameter('language_code').value

        if self._robot_type == "physical":
            self.robot_present = True
            self.furhat = FurhatRemoteAPI(host=self._furhat_ip)
        elif self._robot_type == "virtual":
            self.robot_present = True
            self.furhat = FurhatRemoteAPI(host="localhost")
        else:
            self.robot_present = False

        # if self._language == "en-US":
        #     voice = 'Salli (en-US) - Amazon Polly'
        #     voice = 'ChristopherNeural (en-US) - Microsoft Azure'
        # elif self._language == "sv-SE":
        #     voice = 'Astrid (sv-SE) - Amazon Polly'

        # if self.robot_present:
        #     self.furhat.set_voice(name=voice)

        self.attend_locations = { 'left':  "-0.7, 0.14, 2.0",
                                  'right': " 0.5, 0.14, 2.0",
                                  'up':    " 0.0, 0.2,  2.0",
                                  'down':  " 0.0, 0.0,  2.0",
                                  'away':  " 0.1, 0.1,  2.0",
                                  'center':" 0.0, 0.2,  2.0"}

    def robot_action_callback(self, msg):
        data = msg.data
        if "/" in data: 
           pased_data = data.split("/")
        #    self.get_logger().info(f"-----------------------: {pased_data}")
           for item in pased_data:
               if item.strip() != "":
                   self.action_buffer.put(item.strip())
        else:
            self.action_buffer.put(data.strip())
        # self.get_logger().info(f"robot_action_callback")

    def action_timer_callback(self):
        if not self.action_buffer.empty():
            action = self.action_buffer.get(block=False)
            if "attend_" in action:
                self.robot_attend(action)
            elif "gesture_" in action:
                self.robot_gesture(action)
            else:
                self.robot_speak(action)
        # self.get_logger().info(f"action_timer_callback")

    def robot_stop_callback(self, msg):
        if self.robot_present:
            self.furhat.stop()
        self.get_logger().info(f"furhat_bridge stop")

    def robot_speak(self, text):
        if self.robot_present:
            self.furhat.say(text=text)
        self.get_logger().info(f"furhat_bridge text: {text}")

    def robot_gesture(self, gesture):
        if self.robot_present:
            self.furhat.gesture(name=gesture)
        self.get_logger().info(f"furhat_bridge gesture: {gesture}")

    def robot_attend(self, direction):
        direction = direction.replace("attend_", "")
        if self.robot_present:
            # self.get_logger().info(f" +++++ {self.furhat.get_users()}")
            if direction== "other":
                if len(self.furhat.get_users())>1:
                    try:
                        self.furhat.attend(userid="user-1") #For virtual use :"virtual-user-1",
                    except Exception:
                        self.furhat.attend(user="OTHER")
            elif direction == "user":
                try:
                    self.furhat.attend(userid="user-0") #For virtual use :"virtual-user-1",
                except Exception:
                    self.furhat.attend(user="CLOSEST")
            elif direction in ["up", "down", "left", "right", "center"]:
                self.furhat.attend(location=self.attend_locations[direction])

        self.get_logger().info(f"furhat_bridge attend: {direction}")


def main(args=None):
    rclpy.init(args=args)
    global furhat_bridge_node 
    furhat_bridge_node= FurhatBridgeNode()
    rclpy.spin(furhat_bridge_node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
