import os
import json
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
        self.pub_robot_state = self.create_publisher(String, '/robot_furhat/robot_state', 10)

        self.get_logger().info(f'furhat_bridge NODE has been started')

        self.action_buffer = Queue(maxsize=10)

        self.declare_parameter('robot_type', 'None')
        self.declare_parameter('furhat_ip', '10.0.1.10')
        self.declare_parameter('language_code', 'en-US')

        self._robot_type = self.get_parameter('robot_type').value
        self._furhat_ip = self.get_parameter('furhat_ip').value
        self._language = self.get_parameter('language_code').value

        self.set_embodiment()

        self.attend_locations = { 'left':  "-0.7, 0.14, 2.0",
                                  'right': " 0.5, 0.14, 2.0",
                                  'up':    " 0.0, 0.2,  2.0",
                                  'down':  " 0.0, 0.0,  2.0",
                                  'away':  " 0.1, 0.1,  2.0",
                                  'center':" 0.0, 0.2,  2.0"}

        # Hack to reproduce utterance duration
        self.utt_duration_file = os.path.join(os.getcwd(),"src", "woz_reception", "config", "utterance_duration.json")
        with open(self.utt_duration_file, 'r') as file:
            self.utt_delays = json.load(file)
        self.motion_delay = 0.25

        self.timer_running = False
        self.lock = threading.Lock()
        self.timer = None

    def robot_action_callback(self, msg):
        data = msg.data
        if "/" in data: 
           parsed_data = data.split("/")
           for item in parsed_data:
               if item.strip() != "":
                   self.action_buffer.put(item.strip())
        elif "*" in data:
            parsed_data = data.replace("*","")
            self.force_action(parsed_data)
        else:
            self.action_buffer.put(data.strip())
 
        with self.lock:
            if not self.timer_running:
                self.start_action()

    def start_action(self):
        if not self.action_buffer.empty():
            action = self.action_buffer.get(block=False)
            if "attend_" in action:
                self.robot_attend(action)
                delay = self.motion_delay
                self._start_timer(delay)
            elif "gesture_" in action:
                self.robot_gesture(action)
                delay = self.motion_delay
                self._start_timer(delay)
            else:
                if action in self.utt_delays.keys():
                    duration = self.utt_delays[action]
                    if duration-1 > 0:
                        duration = duration-1
                else:
                  duration = 0.4965 * int(len(action.split()))
                self.robot_speak(action)
                self._start_timer(duration)

    def force_action(self, action):
        if "attend_" in action:
            self.robot_attend(action)
        elif "gesture_" in action:
            self.robot_gesture(action)
        # elif "stop_speech" in action:
        #     self.robot_stop_speech(action)

    def _start_timer(self, time):
        self.timer_running = True
        self.timer = threading.Timer(time, self._on_timer_end)
        self.timer.start()

    def _on_timer_end(self):
        with self.lock:
            self.timer_running = False

        if not self.action_buffer.empty():
            self.start_action()

    def _stop_timer(self):
        with self.lock:
            if self.timer_running and self.timer is not None:
                self.timer.cancel()
            self.timer_running = False
            self.timer = None

    def robot_speak(self, text):
        if self.robot_present:
            self.furhat.say(text=text)
        self.get_logger().info(f"Publishing: speak {text}")

    def robot_gesture(self, gesture):
        if self.robot_present:
            self.furhat.gesture(name=gesture)
        self.get_logger().info(f"'Publishing: gesture {gesture}")

    def robot_attend(self, direction):
        direction = direction.replace("attend_", "")

        if self.robot_present:
            if direction== "other":
                self.furhat.attend(location=self.attend_locations["left"])
                # if len(self.furhat.get_users())>1:
                #     try:
                #         self.furhat.attend(userid="user-1") #For virtual use :"virtual-user-1",
                #     except Exception:
                #         self.furhat.attend(user="OTHER")
                # else:
                    # self.furhat.attend(location=self.attend_locations["left"])
            elif direction == "user":
                self.furhat.attend(location=self.attend_locations['center'])
                # try:
                #     self.furhat.attend(user="CLOSEST")
                #     # self.furhat.attend(userid="user-0") #For virtual use :"virtual-user-0",
                # except Exception:
                #     self.furhat.attend(location=self.attend_locations['center'])

            elif direction in ["up", "down", "left", "right", "center"]:
                self.furhat.attend(location=self.attend_locations[direction])

        self.get_logger().info(f"'Publishing: attend {direction}")

    # def robot_speech_stop(self):
    #     if self.robot_present:
    #         self.furhat.say(text=text)
    #     self._stop_timer()


    def publish_robot_state(self, data):
        msg = String()
        msg.data = data
        self.pub_robot_state.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)

    def set_embodiment(self):
        if self._robot_type == "physical":
            self.robot_present = True
            self.furhat = FurhatRemoteAPI(host=self._furhat_ip)
        elif self._robot_type == "virtual":
            self.robot_present = True
            self.furhat = FurhatRemoteAPI(host="localhost")
        else:
            self.robot_present = False

        if self._language == "en-US":
            voice = 'Matthew-Neural (en-US) - Amazon Polly'
        elif self._language == "sv-SE":
            voice = 'Astrid (sv-SE) - Amazon Polly'

        if self.robot_present:
            self.furhat.set_voice(name=voice)
        # self.get_logger().info(f"furhat_bridge language set to: {self._language}")

def main(args=None):
    rclpy.init(args=args)
    global furhat_bridge_node 
    furhat_bridge_node= FurhatBridgeNode()
    rclpy.spin(furhat_bridge_node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
