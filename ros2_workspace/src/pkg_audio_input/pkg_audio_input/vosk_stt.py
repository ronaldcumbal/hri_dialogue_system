# Based on https://github.com/alphacep/vosk-api/blob/master/python/example/test_microphone.py

import argparse
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
        super().__init__("microphone")

        # publishers
        self.state_pub = self.create_publisher(String, "/state", 0)
        self.speech_final_pub = self.create_publisher(String, "/speech_final", 0)
        self.speech_partial_pub = self.create_publisher(String, "/speech_partial", 0)

        # subscribers
        self.state_subscriber = self.create_subscription(String, "/state", self.state_callback, 0)

        self.device_initialization()

    def device_initialization(self):
        # show list of audio devices 
        print(sd.query_devices())

        self.declare_parameter('device', 0)
        self.declare_parameter('language', 'en-us')
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('channels', 1)

        self._device = self.get_parameter('device').value
        self._language = self.get_parameter('language').value
        self._samplerate = self.get_parameter('sample_rate').value
        self._channels = self.get_parameter('channels').value

        device_info = sd.query_devices(self._device, "input")
        # samplerate = int(device_info["default_samplerate"])

        self.model = Model(lang=self._language)
        self.q = queue.Queue()
        self.get_logger().info(f"device initialized")

        self.start_listening()

    def state_callback(self, msg):
        pass
        # if msg.data == "listening":
        #     self.get_logger().info(f"STATE: {msg.data}")
        #     self.start_listening()

    def audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def start_listening(self):

        with sd.RawInputStream(samplerate=self._samplerate, 
                            blocksize = 8000, 
                            device=self._device,
                            dtype="int16", 
                            channels=self._channels, 
                            callback=self.audio_callback):
            print("#" * 80)
            print("Press Ctrl+C to stop the recording")
            print("#" * 80)

            rec = KaldiRecognizer(self.model, self._samplerate)
            while True:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result())["text"]
                    self.publish_string(text, self.speech_final_pub)
                    # print(rec.Result())
                else:
                    partial = json.loads(rec.PartialResult())["partial"]
                    if partial != "":
                        self.publish_string(partial, self.speech_partial_pub)
                        # print(rec.PartialResult())

    def publish_string(self, string_to_send, publisher_to_use):
        msg = String()
        msg.data = string_to_send

        publisher_to_use.publish(msg)
        self.get_logger().debug(
            f"Topic: {publisher_to_use.topic_name}\nMessage published: {msg.data}"
        )
        print(msg.data)


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