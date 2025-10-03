import rclpy
from rclpy.node import Node

from pkg_commons.srv import DialogueTurn
from std_msgs.msg import String

class MinimalClientAsync(Node):

    def __init__(self):
        super().__init__('minimal_client_async')
        self.client = self.create_client(DialogueTurn, 'dialogue_service')
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.request = DialogueTurn.Request()

    def send_request(self, text):
        self.request.input_text = text
        self.future = self.client.call_async(self.request)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

def main(args=None):
    rclpy.init(args=args)

    minimal_client = MinimalClientAsync()
    response = minimal_client.send_request("This is a text.")
    print(response.output_text)

    minimal_client.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()