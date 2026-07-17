#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
# Import a specific function/class from your module
# from cpp_py_pkg.module_to_import import …
def main(args=None):
# Initiate ROS communications
    rclpy.init(args=args)
# Instantiate the node
    node = Node(‘my_node_name’)
# Make the node spin
    rclpy.spin(node)
# Shutdown ROS communications
    rclpy.shutdown()
if __name__ == ‘__main__’:
    main()
