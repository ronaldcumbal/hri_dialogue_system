import os
import rclpy
import threading
from rclpy.node import Node
from std_msgs.msg import String

from flask import Flask, render_template, request, jsonify
import random

template_dir = os.path.join(os.getcwd(),"src", "woz_reception", "woz_reception", "templates")
print(template_dir)
app = Flask(__name__, template_folder=template_dir)

# Start the Flask app in a separate thread
threading.Thread(target=lambda: app.run(host="localhost", port=8181, debug=False)).start()

# --------- ROS2 --------- #
wizard_interface_node = None
class WizardInterfaceNode(Node):

    def __init__(self):
        super().__init__('wizard_interface')
        self.publisher_ = self.create_publisher(String, 'wizard_commands', 10)
        self.get_logger().info(f'wizard_interface node has been started')

    def publish_command(self, command):
        msg = String()
        msg.data = command
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)

def main(args=None):
    rclpy.init(args=args)
    global wizard_interface_node 
    wizard_interface_node= WizardInterfaceNode()
    rclpy.spin(wizard_interface_node)
    rclpy.shutdown()


# --------- FLASK --------- #
menus = {
    "menuA": ["Apple", "Banana", "Cherry", "Date", "Elderberry"],
    "menuB": ["Red", "Green", "Blue", "Yellow", "Purple"],
    "menuC": ["Cat", "Dog", "Mouse", "Elephant", "Lion"]
}

def get_menus(menu):
    menus[menu] = random.sample(menus[menu], 3)
    return menus

@app.route("/")
def home():
    return render_template('index.html')

@app.route('/update_menus', methods=['POST'])
def update_menu():
    key = request.json.get('key')

    global wizard_interface_node
    wizard_interface_node.publish_command(key)

    if key in ["1", "2", "3", "4", "5"]:
       updated_data = get_menus("menuA")
    elif key in ["6", "7", "8", "9", "0"]:
       updated_data = get_menus("menuB")
    else:
       updated_data = get_menus("menuC")

    return jsonify(updated_data)

if __name__ == '__main__':
    main()
