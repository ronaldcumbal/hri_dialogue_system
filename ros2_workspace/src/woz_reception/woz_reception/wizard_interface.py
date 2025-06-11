import os
import json
import random
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from flask import Flask, render_template, request, jsonify

template_dir = os.path.join(os.getcwd(),"src", "woz_reception", "woz_reception", "templates")
app = Flask(__name__, template_folder=template_dir)

# Start the Flask app in a separate thread
threading.Thread(target=lambda: app.run(host="localhost", port=8181, debug=False)).start()

# --------- ROS2 --------- #
wizard_interface_node = None

class WizardInterfaceNode(Node):

    def __init__(self):
        super().__init__('wizard_interface')
        self.publisher_ = self.create_publisher(String, 'wizard_commands', 10)
        self.utterances_file = os.path.join(os.getcwd(),"src", "woz_reception", "config", "utterances.json")
        self.load_utterances()
        self.get_logger().info(f'wizard_interface NODE has been started')

    def load_utterances(self):
        # Hack to load utterances from a JSON file. TODO: move code to separte node 
        with open(self.utterances_file, 'r') as file:
            self.raw_utterances = json.load(file)
        self.utterances = {}
        self.utterances["normal_bridge"] = self.raw_utterances["normal_bridge"]
        self.utterances["main"] = [random.choice(u) for u in self.raw_utterances["main_dialogue"]]
        self.utterances["normal"] = [random.choice(u) for u in self.raw_utterances["normal_condition"]]
        self.utterances["rushed"] = [random.choice(u) for u in self.raw_utterances["rushed_condition"]]
        self.utterances["very_rushed"] = [random.choice(u) for u in self.raw_utterances["very_rushed_condition"]]

    def set_content(self, condition):
        self.condition = condition
        self.content = {}
        self.content["menuA"] = self.utterances["main"]
        self.content["menuB"] = self.utterances[condition]
        return self.content

    def get_content(self):
        return self.content

    def publish_command(self, command):
        msg = String()
        msg.data = command
        self.publisher_.publish(msg)
        # self.get_logger().info('Publishing: "%s"' % msg.data)

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
    return jsonify(content)

@app.route('/end', methods=['POST'])
def end_dialogue():
    pass

@app.route('/select', methods=['POST'])
def select_utterance():

    global wizard_interface_node
    content = wizard_interface_node.get_content()

    key = request.json.get('key')
    if key in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
        ind = int(key)
        menu_ind = "menuA"+str(ind)
        print(f"Selected utterance: {menu_ind}")

        data = content["menuA"][ind]
        if "<attend_other>" in data:
           utterance = data.replace("<attend_other>", "")
           gesture = "attend_other"
        else:
           utterance = data
           gesture = "None"
        data = {"Id": menu_ind}
        publish_enabled = True

    elif key in ["q", "w", "e", "r"]:
        key2int = {"q": 0, "w": 1, "e": 2, "r": 3}
        ind = key2int[key]
        menu_ind = "menuB"+str(ind)
        print(f"Selected utterance: {menu_ind}")

        data = content["menuB"][ind]
        if "<attend_other>" in data:
           utterance = data.replace("<attend_other>", "")
           gesture = "attend_other"
        else:
           utterance = data
           gesture = "None"
        data = {"Id": menu_ind}
        publish_enabled = True

    if publish_enabled:
        wizard_interface_node.publish_command(utterance)
        wizard_interface_node.publish_command(gesture)

    return jsonify(data)

if __name__ == '__main__':
    main()
