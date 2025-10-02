# Based on https://github.com/alphacep/vosk-api/blob/master/python/example/test_microphone.py
# When run this node alone while debugging:
# ros2 run pkg_audio_input stt_vosk --ros-args -p start_listening:=True --log-level debug

import queue
import sys
import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SpeechTotext(Node):
    def __init__(self):
        super().__init__("microphone_stt")

        # publishers
        self.state_pub = self.create_publisher(String, "/state", 0)
        self.speech_final_pub = self.create_publisher(String, "/speech_final", 0)
        self.speech_partial_pub = self.create_publisher(String, "/speech_partial", 0)

        # subscribers
        self.state_subscriber = self.create_subscription(String, "/state", self.state_callback, 0)

        self.declare_parameter('device', 0)
        self.declare_parameter('language', 'en-us')
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('channels', 1)
        self.declare_parameter('start_listening', False)

        self._device = self.get_parameter('device').value
        self._language = self.get_parameter('language').value
        self._samplerate = self.get_parameter('sample_rate').value
        self._channels = self.get_parameter('channels').value
        self._start_listening = self.get_parameter('start_listening').value

        self.device_initialization()

    def device_initialization(self):
        # show list of audio devices 
        print("-" * 70)
        print("Devices: ")
        print(sd.query_devices())
        print("-" * 70)

        device_info = sd.query_devices(self._device, "input")
        # samplerate = int(device_info["default_samplerate"])

        self.model = Model(lang=self._language)
        self.q = queue.Queue()

        self.get_logger().info(f"Device initialized")

        if self._start_listening:
            self.start_listening()
        else:
            self.get_logger().warn(f"Device ########## NOT LISTENING ##########")

    def state_callback(self, msg):
        if not self._listenning and msg.data == "listening":
            self.get_logger().info(f"STATE: {msg.data}")
            self.start_listening()

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def start_listening(self):
        self.get_logger().info(f"Device listening")

        with sd.RawInputStream(samplerate=self._samplerate, 
                            blocksize = 8000, 
                            device=self._device,
                            dtype="int16", 
                            channels=self._channels, 
                            callback=self.audio_callback):

            rec = KaldiRecognizer(self.model, self._samplerate)
            while True:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result())["text"]
                    msg = String()
                    msg.data = text
                    self.speech_final_pub.publish(msg)
                    self.get_logger().info(f"Topic: {self.speech_final_pub.topic_name} msg: {msg.data}")

                else:
                    partial = json.loads(rec.PartialResult())["partial"]
                    if partial != "":
                        msg = String()
                        msg.data = partial
                        self.speech_partial_pub.publish(msg)
                        self.get_logger().debug(f"Topic: {self.speech_partial_pub.topic_name} msg: {msg.data}")

    # def publish_string(self, string_to_send, publisher_to_use):
    #     msg = String()
    #     msg.data = string_to_send
    #     publisher_to_use.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = SpeechTotext()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()