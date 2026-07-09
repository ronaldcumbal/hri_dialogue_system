# pip install speechmatics-rt (also requires pyaudio for microphone access)
# Requires the SPEECHMATICS_API_KEY environment variable.
#
# Example CLI commands:
# ros2 run pkg_audio_input stt_speechmatics --ros-args -p device:=3 -p language:=en

import asyncio
import os
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SpeechmaticsNode(Node):

    def __init__(self):
        super().__init__('stt_speechmatics')

        # publishers
        self.speech_final_pub = self.create_publisher(String, '/user_speech', 0)
        self.speech_partial_pub = self.create_publisher(String, '/user_speech_partial', 0)

        # subscribers
        self.create_subscription(String, '/state', self.state_callback, 0)

        self.declare_parameter('url', '')
        self.declare_parameter('language', 'en')
        self.declare_parameter('model', 'enhanced')
        self.declare_parameter('enable_partials', True)
        self.declare_parameter('sample_rate', 16000)
        self.declare_parameter('chunk_size', 4096)
        self.declare_parameter('device', -1)
        self.declare_parameter('start_listening', True)

        self._api_key = os.getenv('SPEECHMATICS_API_KEY')
        if not self._api_key:
            self.get_logger().warn("SPEECHMATICS_API_KEY is not set")
        self._url = self.get_parameter('url').value or None
        self._language = self.get_parameter('language').value
        self._model = self.get_parameter('model').value
        self._enable_partials = self.get_parameter('enable_partials').value
        self._sample_rate = self.get_parameter('sample_rate').value
        self._chunk_size = self.get_parameter('chunk_size').value
        self._device = self.get_parameter('device').value

        self._listening_event = threading.Event()
        if self.get_parameter('start_listening').value:
            self._listening_event.set()

        self._log_input_devices()
        self.get_logger().info("Speechmatics client initialized")

    def _log_input_devices(self):
        try:
            from speechmatics.rt import Microphone
        except Exception:
            self.get_logger().warn("speechmatics-rt not available, cannot list input devices")
            return

        self.get_logger().info("Available input devices:")
        for d in Microphone.list_devices():
            self.get_logger().info(f"  [{d['index']}] {d['name']} (channels={d['channels']})")

    def state_callback(self, msg):
        if msg.data == 'listening':
            self._listening_event.set()

    def wait_until_listening(self):
        self._listening_event.wait()

    def publish_final(self, text):
        self.speech_final_pub.publish(String(data=text))
        self.get_logger().info(f"Topic: {self.speech_final_pub.topic_name} msg: {text}")

    def publish_partial(self, text):
        self.speech_partial_pub.publish(String(data=text))
        self.get_logger().debug(f"Topic: {self.speech_partial_pub.topic_name} msg: {text}")

    async def run(self):
        from speechmatics.rt import (
            AsyncClient, AudioEncoding, AudioFormat, AuthenticationError,
            Microphone, Model, ServerMessageType, TranscriptionConfig, TranscriptResult,
        )

        audio_format = AudioFormat(
            encoding=AudioEncoding.PCM_S16LE,
            sample_rate=self._sample_rate,
            chunk_size=self._chunk_size,
        )
        transcription_config = TranscriptionConfig(
            language=self._language,
            model=Model(self._model),
            enable_partials=self._enable_partials,
        )
        mic = Microphone(
            sample_rate=audio_format.sample_rate,
            chunk_size=audio_format.chunk_size,
            device_index=(self._device if self._device >= 0 else None),
        )
        if not mic.start():
            self.get_logger().error("Failed to start microphone (is pyaudio installed?)")
            return

        try:
            async with AsyncClient(api_key=self._api_key, url=self._url) as client:

                @client.on(ServerMessageType.ADD_TRANSCRIPT)
                def handle_final(message):
                    transcript = TranscriptResult.from_message(message).metadata.transcript
                    if transcript:
                        self.publish_final(transcript)

                @client.on(ServerMessageType.ADD_PARTIAL_TRANSCRIPT)
                def handle_partial(message):
                    transcript = TranscriptResult.from_message(message).metadata.transcript
                    if transcript:
                        self.publish_partial(transcript)

                await client.start_session(
                    transcription_config=transcription_config, audio_format=audio_format)

                while True:
                    frame = await mic.read(audio_format.chunk_size)
                    await client.send_audio(frame)

        except AuthenticationError:
            self.get_logger().error("Speechmatics authentication failed, check api_key")
        finally:
            mic.stop()


def main(args=None):
    rclpy.init(args=args)
    node = SpeechmaticsNode()
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        node.wait_until_listening()
        asyncio.run(node.run())
    except KeyboardInterrupt:
        pass
    except Exception:
        node.get_logger().error("stt_speechmatics failed")
    finally:
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)
        node.destroy_node()


if __name__ == '__main__':
    main()
