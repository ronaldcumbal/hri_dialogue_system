# pip install speechmatics-tts sounddevice numpy
# Requires the SPEECHMATICS_API_KEY environment variable.
#
# Example CLI commands:
# ros2 run pkg_audio_output tts_speechmatics --ros-args -p device:=3 -p voice:=jack
# ros2 topic pub /robo_speech std_msgs/String "data: 'hello there'"

import asyncio
import os
import queue
import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TTSNode(Node):

    def __init__(self):
        super().__init__('tts_speechmatics')

        self.create_subscription(String, '/robo_speech', self.robo_speech_callback, 0)

        self.declare_parameter('url', '')
        self.declare_parameter('voice', 'jack')
        self.declare_parameter('device', -1)
        self.declare_parameter('buffer_size', 4096)

        self._api_key = os.getenv('SPEECHMATICS_API_KEY')
        if not self._api_key:
            self.get_logger().warn("SPEECHMATICS_API_KEY is not set")
        self._url = self.get_parameter('url').value or None
        self._voice = self.get_parameter('voice').value
        self._device = self.get_parameter('device').value
        self._buffer_size = self.get_parameter('buffer_size').value

        self._text_queue = queue.Queue()

        self._log_output_devices()
        self.get_logger().info("TTS client initialized")

    def _log_output_devices(self):
        try:
            import sounddevice as sd
        except Exception:
            self.get_logger().warn("sounddevice not available, cannot list output devices")
            return

        self.get_logger().info("Available output devices:")
        for i, info in enumerate(sd.query_devices()):
            if info.get('max_output_channels', 0) > 0:
                self.get_logger().info(f"  [{i}] {info.get('name')}")

    def robo_speech_callback(self, msg):
        self._text_queue.put(msg.data)

    async def worker(self):
        from speechmatics.tts import AsyncClient

        async with AsyncClient(api_key=self._api_key, url=self._url) as client:
            while True:
                text = await asyncio.to_thread(self._text_queue.get)
                try:
                    await self._speak(client, text)
                except Exception:
                    self.get_logger().error(f"Failed to speak: {text!r}", exc_info=True)

    async def _speak(self, client, text):
        import numpy as np
        import sounddevice as sd
        from speechmatics.tts import OutputFormat, Voice

        self.get_logger().info(f"Topic: /robo_speech msg: {text}")

        async with await client.generate(
                text=text, voice=Voice(self._voice),
                output_format=OutputFormat.RAW_PCM_16000) as response:
            with sd.OutputStream(
                    samplerate=16000, channels=1, dtype='int16',
                    device=(self._device if self._device >= 0 else None)) as stream:
                buffer = bytearray()
                async for chunk in response.content.iter_chunked(self._buffer_size):
                    if not chunk:
                        continue
                    buffer.extend(chunk)
                    usable = len(buffer) - (len(buffer) % 2)  # whole 16-bit samples only
                    if usable:
                        stream.write(np.frombuffer(bytes(buffer[:usable]), dtype='<i2'))
                        del buffer[:usable]


def main(args=None):
    rclpy.init(args=args)
    node = TTSNode()
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        asyncio.run(node.worker())
    except KeyboardInterrupt:
        pass
    except Exception:
        node.get_logger().error("tts_speechmatics failed")
    finally:
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)
        node.destroy_node()


if __name__ == '__main__':
    main()
