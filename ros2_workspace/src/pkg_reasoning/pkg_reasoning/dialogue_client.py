import rclpy
from rclpy.node import Node

from pkg_commons.srv import DialogueTurn
from std_msgs.msg import String

class MinimalClientAsync(Node):

    def __init__(self):
        super().__init__('minimal_client_async')

        # subscribers
        self.state_subscriber = self.create_subscription(String, "/state", self.state_callback, 0)
        self.user_speech_subscriber = self.create_subscription(String, "/user_speech", self.user_speech_callback, 0)
        self.user_speech_partial_sub = self.create_subscription(String, "/user_speech_partial", self.user_speech_partial_callback, 0)

        self.client = self.create_client(DialogueTurn, 'dialogue_service')
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.request = DialogueTurn.Request()

    def user_speech_callback(self, msg):
        print("---------------------------", msg)

        response = self.send_request(msg.data)
        self.get_logger().info(f'Response: {response.output_text}')

    def user_speech_partial_callback(self, msg):
        # Get quick responses if partial results match with FAQ or known commands
        pass

    def send_request(self, text):
        self.request.input_text = text
        self.future = self.client.call_async(self.request)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

    def state_callback(self):
        pass


def main(args=None):
    rclpy.init(args=args)
    node = MinimalClientAsync()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()