import os
import zmq
import cv2
import json
import numpy as np

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from datetime import datetime

class FurhatCameraNode(Node):
    def __init__(self):
        super().__init__('camera_furhat')

        self.create_subscription(String, '/state', self.state_callback, 10)

        self.declare_parameter('camera_ip', '10.0.1.10:3000')
        camera_ip = self.get_parameter('camera_ip').get_parameter_value().string_value
        self.url = f'tcp://{camera_ip}'

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_video = f"furhat_video_{timestamp}.avi"
        self.video_path = os.path.join(os.getcwd(),"src", "woz_reception", "data", output_video)


        # Setup the sockets
        context = zmq.Context()
        # Input camera feed from furhat using a SUB socket
        self.insocket = context.socket(zmq.SUB)
        self.insocket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.insocket.connect(self.url)
        self.insocket.setsockopt(zmq.RCVHWM, 1)
        self.insocket.setsockopt(zmq.CONFLATE, 1)

        self.get_logger().info(f'Listening to {self.url}, entering loop')
        self.img = None
        self.ov = None  # VideoWriter, initialized lazily

        self.record_video = True
        self.show_video = False


        # Timer to call main loop periodically
        # self.timer = self.create_timer(0.01, self.receive_loop)


    def state_callback(self, msg):
        if msg.data == "start":
            # Timer to call main loop periodically
            self.timer = self.create_timer(0.01, self.receive_loop)
        elif msg.data == "end":
            self.cleanup()

    def receive_loop(self):
        try:
            string = self.insocket.recv(flags=zmq.NOBLOCK)
        except zmq.Again:
            return  # no message available

        magicnumber = string[0:3]

        if magicnumber == b'\xff\xd8\xff':  # JPEG image
            buf = np.frombuffer(string, dtype=np.uint8)
            self.img = cv2.imdecode(buf, flags=1)

            if self.img is not None:
                if self.record_video and self.ov is None:
                    height, width = self.img.shape[:2]
                    self.ov = cv2.VideoWriter(
                        self.video_path,
                        cv2.VideoWriter_fourcc(*'MJPG'),
                        10,
                        (width, height)
                    )

                if self.record_video and self.ov is not None:
                    self.ov.write(self.img)

        else:  # assume JSON
            try:
                furhat_recognition = json.loads(string.decode())
                # self.get_logger().info(f'Furhat Recognition: {furhat_recognition}')
            except json.JSONDecodeError as e:
                self.get_logger().warn(f'JSON decode error: {e}')
                return
            if self.show_video:
                if isinstance(self.img, np.ndarray):
                    # optionally annotate(self.img, furhat_recognition)
                    cv2.imshow('FurhatTube', self.img)
                    k = cv2.waitKey(1)
                    if k % 256 == 27:  # ESC
                        self.get_logger().info("Escape hit, closing...")
                        self.cleanup()
                        # rclpy.shutdown()

    def cleanup(self):
        if self.ov:
            self.get_logger().info('Releasing video')
            self.ov.release()
        if self.show_video:
            cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = FurhatCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard interrupt, shutting down...")
        node.cleanup()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()