# Wraps whisper_live.client.TranscriptionClient (https://github.com/collabora/WhisperLive)
#
# Example CLI commands:
# ros2 run pkg_audio_input stt_whisper_client --ros-args -p device:=3 -p model:=small
# ros2 topic echo /user_speech_partial
# ros2 topic echo /user_speech

import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class WhisperClientNode(Node):

    def __init__(self):
        super().__init__('stt_whisper_client')

        # publishers
        self.speech_final_pub = self.create_publisher(String, '/user_speech', 0)
        self.speech_partial_pub = self.create_publisher(String, '/user_speech_partial', 0)

        # subscribers
        self.create_subscription(String, '/state', self.state_callback, 0)

        self.declare_parameter('host', 'localhost')
        self.declare_parameter('port', 9090)
        self.declare_parameter('device', -1)
        self.declare_parameter('language', '')
        self.declare_parameter('model', 'small')
        self.declare_parameter('translate', False)
        self.declare_parameter('use_vad', True)
        self.declare_parameter('no_speech_thresh', 0.45)
        self.declare_parameter('send_last_n_segments', 10)
        self.declare_parameter('same_output_threshold', 10)
        self.declare_parameter('initial_prompt', '')
        self.declare_parameter('start_listening', True)
        self.declare_parameter('final_flush_silence_sec', 1.0)
        self.declare_parameter('flush_check_period_sec', 0.2)

        self._host = self.get_parameter('host').value
        self._port = self.get_parameter('port').value
        self._device = self.get_parameter('device').value
        self._language = self.get_parameter('language').value or None
        self._model = self.get_parameter('model').value
        self._translate = self.get_parameter('translate').value
        self._use_vad = self.get_parameter('use_vad').value
        self._no_speech_thresh = self.get_parameter('no_speech_thresh').value
        self._send_last_n_segments = self.get_parameter('send_last_n_segments').value
        self._same_output_threshold = self.get_parameter('same_output_threshold').value
        self._initial_prompt = self.get_parameter('initial_prompt').value or None
        self._final_flush_silence_sec = self.get_parameter('final_flush_silence_sec').value
        self._flush_check_period_sec = self.get_parameter('flush_check_period_sec').value

        # Coalescing state, guarded by _lock: transcription_callback() runs on WhisperLive's
        # websocket-recv thread while _flush_check() runs on the rclpy spin thread.
        self._lock = threading.Lock()
        self._accumulated_final_segments = []
        self._last_final_key = (-1.0, -1.0)
        self._last_partial_text = None
        self._has_in_progress = False
        self._last_activity_time = time.monotonic()

        self._listening_event = threading.Event()
        if self.get_parameter('start_listening').value:
            self._listening_event.set()

        self._log_input_devices()

        self.create_timer(self._flush_check_period_sec, self._flush_check)

        self.get_logger().info("Whisper client initialized")

    def _log_input_devices(self):
        try:
            import pyaudio
        except Exception:
            self.get_logger().warn("pyaudio not available, cannot list input devices")
            return

        pa = pyaudio.PyAudio()
        try:
            self.get_logger().info("Available input devices:")
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    self.get_logger().info(
                        f"  [{i}] {info.get('name')} "
                        f"(channels={info.get('maxInputChannels')}, "
                        f"default_rate={info.get('defaultSampleRate')})")
        finally:
            pa.terminate()

    def state_callback(self, msg):
        '''Callback for system state updates'''
        if msg.data == 'listening':
            self._listening_event.set()

    def wait_until_listening(self):
        self._listening_event.wait()

    def build_client(self):
        '''Construct the WhisperLive client, wired to publish through transcription_callback'''
        from whisper_live.client import TranscriptionClient

        class _DeviceClient(TranscriptionClient):
            """Relies on whisper_live.client.TranscriptionTeeClient's internal,
            undocumented attributes self.p/self.stream/self.format/self.channels/
            self.rate/self.chunk (verified against whisper-live 0.9.0). Re-verify
            after any whisper-live version bump."""

            def __init__(self, *args, input_device_index=None, **kwargs):
                super().__init__(*args, **kwargs)  # already opened self.p/self.stream + websocket
                if input_device_index is None or getattr(self, 'stream', None) is None:
                    return
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = self.p.open(
                        format=self.format, channels=self.channels, rate=self.rate,
                        input=True, input_device_index=input_device_index,
                        frames_per_buffer=self.chunk)
                except Exception as exc:
                    try:
                        self.close_all_clients()
                    finally:
                        self.p.terminate()
                    raise RuntimeError(
                        f"Failed to open input device {input_device_index}: {exc}") from exc

        return _DeviceClient(
            self._host,
            self._port,
            lang=self._language,
            translate=self._translate,
            model=self._model,
            use_vad=self._use_vad,
            log_transcription=False,
            no_speech_thresh=self._no_speech_thresh,
            send_last_n_segments=self._send_last_n_segments,
            same_output_threshold=self._same_output_threshold,
            initial_prompt=self._initial_prompt,
            transcription_callback=self.transcription_callback,
            input_device_index=(self._device if self._device >= 0 else None),
        )

    def transcription_callback(self, text, segments):
        '''Callback for WhisperLive transcription results, called from the websocket thread'''
        combined = None
        with self._lock:
            if not segments:
                return
            last = segments[-1]
            in_progress = last if not last.get('completed', False) else None
            completed = segments[:-1] if in_progress is not None else segments

            appended = False
            for seg in completed:
                try:
                    key = (float(seg.get('start', 0.0)), float(seg.get('end', 0.0)))
                except (TypeError, ValueError):
                    key = self._last_final_key
                if key <= self._last_final_key:
                    continue  # already accounted for (rolling window resend)
                seg_text = (seg.get('text') or '').strip()
                if seg_text:
                    self._accumulated_final_segments.append(seg_text)
                    appended = True
                self._last_final_key = key

            self._has_in_progress = in_progress is not None
            in_progress_text = (in_progress.get('text') or '').strip() if in_progress else ''
            if appended or in_progress_text:
                self._last_activity_time = time.monotonic()

            pending = self._accumulated_final_segments + (
                [in_progress_text] if in_progress_text else [])
            new_combined = ' '.join(pending).strip()
            if new_combined and new_combined != self._last_partial_text:
                self._last_partial_text = new_combined
                combined = new_combined

        if combined is not None:
            self._publish_partial(combined)

    def _flush_check(self):
        '''Timer callback: flush accumulated finalized segments to /user_speech after a pause'''
        utterance_text = None
        with self._lock:
            if not self._accumulated_final_segments:
                return
            idle_for = time.monotonic() - self._last_activity_time
            if self._has_in_progress or idle_for < self._final_flush_silence_sec:
                return
            utterance_text = ' '.join(self._accumulated_final_segments).strip()
            self._accumulated_final_segments = []
            self._last_partial_text = None
        if utterance_text:
            self._publish_final(utterance_text)

    def force_flush(self):
        '''Flush any pending finalized segments unconditionally, used on shutdown'''
        utterance_text = None
        with self._lock:
            if self._accumulated_final_segments:
                utterance_text = ' '.join(self._accumulated_final_segments).strip()
                self._accumulated_final_segments = []
        if utterance_text:
            self._publish_final(utterance_text)

    def _publish_final(self, text):
        self.speech_final_pub.publish(String(data=text))
        self.get_logger().info(f"Topic: {self.speech_final_pub.topic_name} msg: {text}")

    def _publish_partial(self, text):
        self.speech_partial_pub.publish(String(data=text))
        self.get_logger().debug(f"Topic: {self.speech_partial_pub.topic_name} msg: {text}")


def _safe_cleanup(client):
    '''Defensive: TranscriptionTeeClient.record()'s normal-exit and server-disconnect
    paths do NOT close the PyAudio stream / terminate self.p (only its internal
    KeyboardInterrupt handler does). All calls best-effort/idempotent.'''
    for fn in (
        lambda: client.close_all_clients(),
        lambda: (client.stream.stop_stream(), client.stream.close())
        if getattr(client, 'stream', None) else None,
        lambda: client.p.terminate(),
    ):
        try:
            fn()
        except Exception:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = WhisperClientNode()
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    client = None
    try:
        node.wait_until_listening()
        client = node.build_client()
        client()  # blocking: waits for SERVER_READY, then mic capture -> websocket send
    except KeyboardInterrupt:
        pass
    except Exception:
        node.get_logger().error("stt_whisper_client failed")
    finally:
        node.force_flush()
        if client is not None:
            _safe_cleanup(client)
        rclpy.shutdown()
        spin_thread.join(timeout=2.0)
        node.destroy_node()


if __name__ == '__main__':
    main()
