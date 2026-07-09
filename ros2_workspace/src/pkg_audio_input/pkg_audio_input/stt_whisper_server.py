# Wraps whisper_live.server.TranscriptionServer (https://github.com/collabora/WhisperLive)
#
# Example CLI commands:
# ros2 run pkg_audio_input stt_whisper_server --ros-args -p port:=9090
# ros2 run pkg_audio_input stt_whisper_server --ros-args -p backend:=faster_whisper -p max_clients:=2

import os
import threading

import rclpy
from rclpy.node import Node


class WhisperServerNode(Node):

    def __init__(self):
        super().__init__('stt_whisper_server')

        self.declare_parameter('host', 'localhost')
        self.declare_parameter('port', 9090)
        # TranscriptionServer.run() itself defaults backend to "tensorrt"; we default to
        # "faster_whisper" here since that's the only backend we support/test against.
        self.declare_parameter('backend', 'faster_whisper')
        self.declare_parameter('faster_whisper_custom_model_path', '')
        self.declare_parameter('max_clients', 4)
        self.declare_parameter('max_connection_time', 600)
        self.declare_parameter('cache_path', '~/.cache/whisper-live/')
        self.declare_parameter('omp_num_threads', 1)
        self.declare_parameter('enable_rest', False)
        self.declare_parameter('rest_port', 8000)
        self.declare_parameter('cors_origins', '')
        self.declare_parameter('batch_enabled', False)
        self.declare_parameter('batch_max_size', 8)
        self.declare_parameter('batch_window_ms', 50)
        self.declare_parameter('api_key', '')

        self._host = self.get_parameter('host').value
        self._port = self.get_parameter('port').value
        self._backend = self.get_parameter('backend').value
        self._faster_whisper_custom_model_path = self.get_parameter(
            'faster_whisper_custom_model_path').value or None
        self._max_clients = self.get_parameter('max_clients').value
        self._max_connection_time = self.get_parameter('max_connection_time').value
        self._cache_path = self.get_parameter('cache_path').value
        self._omp_num_threads = self.get_parameter('omp_num_threads').value
        self._enable_rest = self.get_parameter('enable_rest').value
        self._rest_port = self.get_parameter('rest_port').value
        self._cors_origins = self.get_parameter('cors_origins').value or None
        self._batch_enabled = self.get_parameter('batch_enabled').value
        self._batch_max_size = self.get_parameter('batch_max_size').value
        self._batch_window_ms = self.get_parameter('batch_window_ms').value
        self._api_key = self.get_parameter('api_key').value or None

        self.get_logger().info(
            f"Starting WhisperLive server (backend={self._backend}) on "
            f"{self._host}:{self._port} in the background, this may take a while "
            f"to import/load models...")

        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()

    def _run_server(self):
        os.environ.setdefault('OMP_NUM_THREADS', str(self._omp_num_threads))
        try:
            from whisper_live.server import TranscriptionServer
        except Exception:
            self.get_logger().error(
                "Failed to import whisper_live.server. Is 'whisper-live' installed? "
                "See pkg_audio_input/README.md.")
            return

        try:
            TranscriptionServer().run(
                self._host,
                port=self._port,
                backend=self._backend,
                faster_whisper_custom_model_path=self._faster_whisper_custom_model_path,
                max_clients=self._max_clients,
                max_connection_time=self._max_connection_time,
                cache_path=self._cache_path,
                rest_port=self._rest_port,
                enable_rest=self._enable_rest,
                cors_origins=self._cors_origins,
                batch_enabled=self._batch_enabled,
                batch_max_size=self._batch_max_size,
                batch_window_ms=self._batch_window_ms,
                api_key=self._api_key,
            )
        except Exception:
            self.get_logger().error("WhisperLive server failed to start")


def main(args=None):
    rclpy.init(args=args)
    node = WhisperServerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
