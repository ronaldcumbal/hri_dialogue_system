import os
import json
import random
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from flask import Flask, render_template, request, jsonify, Response

template_dir = os.path.join(os.getcwd(),"src", "woz_reception", "woz_reception", "templates")
app = Flask(__name__, template_folder=template_dir)

# Start the Flask app in a separate thread
threading.Thread(target=lambda: app.run(host="localhost", port=8181, debug=False)).start()

# --------- ROS2 --------- #
wizard_interface_node = None
last_robot_action = None
last_menu_ind = -1
chat_enabled = False

class WizardInterfaceNode(Node):

    def __init__(self):
        super().__init__('wizard_interface')
        self.pub_robot_action = self.create_publisher(String, '/robot_furhat/robot_action', 10)
        
        self.utterances_file = os.path.join(os.getcwd(),"src", "woz_reception", "config", "utterances.json")
        self.load_utterances()
        self.get_logger().debug(f'wizard_interface NODE has been started')

    def load_utterances(self):
        # Hack to load utterances from a JSON file. TODO: move code to separte node 
        with open(self.utterances_file, 'r') as file:
            self.raw_utterances = json.load(file)
        self.utterances = {}
        self.utterances["bridge"] = self.raw_utterances["bridge"]
        self.utterances["normal_condition"] = self.raw_utterances["normal_condition"]
        self.utterances["rushed_condition"] = self.raw_utterances["rushed_condition"]
        self.utterances["very_rushed_condition"] = self.raw_utterances["very_rushed_condition"]

    def set_content(self, condition):
        self.condition = condition
        self.content = {}
        self.content["menuA_"] = self.utterances[condition]["main_dialogue"]
        self.content["menuB_"] = self.utterances[condition]["interruption_reply"]
        return self.content

    def get_content(self):
        return self.content

    def publish_robot_action(self, data):
        msg = String()
        msg.data = data
        self.pub_robot_action.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)

def main(args=None):
    rclpy.init(args=args)
    global wizard_interface_node 
    wizard_interface_node= WizardInterfaceNode()
    rclpy.spin(wizard_interface_node)
    rclpy.shutdown()


# --------- FLASK --------- #
@app.route("/")
def home():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_dialogue():
    condition = request.json.get('setting')
    global wizard_interface_node
    content = wizard_interface_node.set_content(condition)
    wizard_interface_node.publish_robot_action("/attend_user/")

    global chat_enabled
    chat_enabled = True
    return jsonify(content)

@app.route('/stop', methods=['POST'])
def end_dialogue():
    global chat_enabled
    chat_enabled = False

@app.route('/select', methods=['POST'])
def select_utterance():

    global chat_enabled
    if not chat_enabled:
        return Response(status=204)

    global last_robot_action
    global last_menu_ind

    global wizard_interface_node
    content = wizard_interface_node.get_content()

    key = request.json.get('key')
    # Main Dialogue action
    if key in ["q", "w", "e", "r", "t", "a", "s", "d", "f", "g", "z", "x", "c", "v"]:
        key2int = {"q": 0, "w": 1, "e": 2, "r": 3, "t": 4, "a": 5, "s": 6, "d": 7, "f": 8, "g": 9, "z": 10, "x": 11, "c": 12, "v": 13} 
        ind = key2int[key]
        menu_ind = "menuA_" + str(ind)
        robot_action = content["menuA_"][ind]
    # Automatically progress in Main Dialogue
    elif key in [" "]: # Space key
        if last_menu_ind == -1:
            ind = -1
        else:
            ind = int(last_menu_ind.split("_")[-1])

        if ind < len(content["menuA_"])-1:
            ind = int(ind)+1
            menu_ind = "menuA_" + str(ind)
            robot_action = content["menuA_"][ind]
        else:
            return Response(status=204)
    # Interruption action
    elif key in ["1", "2", "3", "4"]:
        ind = int(key)-1
        if ind < len(content["menuB_"]):
            menu_ind = "menuB_" + str(ind)
            robot_action = content["menuB_"][ind]
        else:
            return Response(status=204)
    elif key in ["Enter"]:
        wizard_interface_node.publish_robot_action("*attend_user*")
        return Response(status=204)
    elif key in ["0"]:
        wizard_interface_node.publish_robot_action("*attend_other*")
        return Response(status=204)
    # Repeat last action
    # elif key in ["Escape"]:
    #     robot_action = last_robot_action
    #     menu_ind = last_menu_ind 
    #     return jsonify({"Id": menu_ind})
    elif key in ["ArrowUp"]:
        wizard_interface_node.publish_robot_action("*attend_up*")
        return Response(status=204)
    elif key in ["ArrowLeft"]:
        wizard_interface_node.publish_robot_action("*attend_left*")
        return Response(status=204)
    elif key in ["ArrowRight"]:
        wizard_interface_node.publish_robot_action("*attend_right*")
        return Response(status=204)
    elif key in ["ArrowDown"]:
        wizard_interface_node.publish_robot_action("*attend_center*")
        return Response(status=204)
    else:
        return Response(status=204)

    wizard_interface_node.publish_robot_action(robot_action)
    last_robot_action = robot_action
    last_menu_ind = menu_ind

    return jsonify({"Id": menu_ind})

if __name__ == '__main__':
    main()
