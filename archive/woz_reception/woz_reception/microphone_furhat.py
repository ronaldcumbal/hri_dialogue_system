import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import zmq
import pyaudio
import struct
import threading
import io
import os
from pydub import AudioSegment
from datetime import datetime

REPO_PATH = "/home/roncu858/Github/hri_dialogue_system"

# ZMQ Configuration
ZMQ_ADDRESS = "tcp://10.0.1.10:3001"

# Audio Parameters
CHANNELS = 1        # Mono output
RATE = 16000        # 16kHz sample rate
FORMAT = pyaudio.paInt16  # 16-bit audio
CHUNK_SIZE = 1024   # Number of frames per buffer

# Choose output: 'both', 'left', or 'right'
OUTPUT_MODE = 'left'

def split_channels(data):
    """Split interleaved stereo PCM data into left and right channels."""
    samples = struct.iter_unpack('<hh', data)
    left = bytearray()
    right = bytearray()

    for l, r in samples:
        if OUTPUT_MODE == 'both':
            left.extend(struct.pack('<h', l))
            right.extend(struct.pack('<h', r))
        elif OUTPUT_MODE == 'left':
            left.extend(struct.pack('<h', l))
            right.extend(struct.pack('<h', l))
        elif OUTPUT_MODE == 'right':
            left.extend(struct.pack('<h', r))
            right.extend(struct.pack('<h', r))

    # Re-interleave left and right
    interleaved = bytearray()
    for l, r in zip(struct.iter_unpack('<h', left), struct.iter_unpack('<h', right)):
        interleaved.extend(struct.pack('<hh', l[0], r[0]))

    return bytes(interleaved)

class MicrophoneFurhatNode(Node):
    def __init__(self):
        super().__init__('microphone_furhat_node')
        self.get_logger().info("AudioStreamNode started.")

        self.create_subscription(String, '/state', self.state_callback, 10)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_audio= f"{timestamp}_audio.mp3"
        self.video_path = os.path.join(REPO_PATH, "data", output_audio)

        # Setup ZMQ
        self.__context = zmq.Context()
        self.socket = self.__context.socket(zmq.SUB)
        self.socket.connect(ZMQ_ADDRESS)
        self.socket.setsockopt(zmq.SUBSCRIBE, b'')

        # Setup PyAudio
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  output=True,
                                  frames_per_buffer=CHUNK_SIZE)

        # Memory buffer to collect raw audio
        self.audio_buffer = io.BytesIO()

        # # Run listener thread
        # self.running = True
        # self.thread = threading.Thread(target=self.receive_audio)
        # self.thread.start()

    def state_callback(self, msg):
        if msg.data == "START":
            # Run listener thread
            self.running = True
            self.thread = threading.Thread(target=self.receive_audio)
            self.thread.start()
        elif msg.data == "END":
            self.destroy_node()

    def receive_audio(self):
        while rclpy.ok() and self.running:
            try:
                data = self.socket.recv()
                # self.get_logger().info(f"Received {len(data)} bytes")
                processed = split_channels(data)
                self.stream.write(processed)
                # Write raw PCM to buffer
                self.audio_buffer.write(processed)
            except zmq.error.ZMQError:
                break

    def save_mp3(self):
        self.get_logger().info("Saving audio to MP3...")
        self.audio_buffer.seek(0)

        audio_segment = AudioSegment(
            data=self.audio_buffer.read(),
            sample_width=2,  # 16-bit PCM
            frame_rate=RATE,
            channels=2  # stereo output
        )

        audio_segment.export(self.video_path, format="mp3")
        self.get_logger().info(f"Saved MP3 to: {self.video_path}")

    def destroy_node(self):
        self.get_logger().info("Shutting down AudioStreamNode.")
        self.running = False
        self.thread.join()
        self.save_mp3()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.socket.close()
        self.__context.term()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = MicrophoneFurhatNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()