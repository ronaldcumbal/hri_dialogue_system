# Based on https://cloud.google.com/speech-to-text/docs/transcribe-streaming-audio
#
# Example CLI commands:
# ros2 run pkg_audio_input stt_google --ros-args -p start_listening:=True
# ros2 run pkg_audio_input stt_google --ros-args -p start_listening:=True --log-level debug
# ros2 topic echo /speech_final

import queue
import time
import pyaudio
import sounddevice as sd
from google.cloud import speech

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

STREAMING_LIMIT = 240000  # 4 minutes

def get_current_time() -> int:
    """Return Current Time in MS.
    Returns:
        int: Current Time in MS.
    """
    value = int(round(time.time() * 1000))
    return value

class SpeechTotextNode(Node):
    def __init__(self):
        super().__init__("microphone_stt")

        # publishers
        self.state_publisher = self.create_publisher(String, "/state", 0)
        self.speech_final_publisher = self.create_publisher(String, "/user_speech", 0)
        self.speech_partial_publisher = self.create_publisher(String, "/user_speech_partial", 0)

        # subscribers
        self.state_subscriber = self.create_subscription(String, "/state", self.state_callback, 0)

        self.declare_parameter('device', 0)
        self.declare_parameter('language', 'en-US')
        self.declare_parameter('sample_rate', 44100)
        self.declare_parameter('channels', 1)
        self.declare_parameter('start_listening', True)

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

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True
        self.start_time = get_current_time()
        self._chunk = int(self._samplerate / 10)

        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16, # The API currently only supports 1-channel (mono) audio https://goo.gl/z757pE
            channels=self._channels, 
            rate=self._samplerate,
            input=True,
            input_device_index = self._device,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
            )

        self.get_logger().info(f"Device initialized")

        if self._start_listening:
            self.start_streaming()
        else:
            self.get_logger().warn(f"Device ########## NOT LISTENING ##########")


    def __enter__(self):
        """Opens the stream.
        Args:
        self: The class instance.
        returns: None
        """
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break
            yield b''.join(data)

    def state_callback(self, msg):
        if not self.stream_running and msg.data == "listening":
            self.get_logger().info(f"STATE: {msg.data}")
            self.start_streaming()

    def start_streaming(self):
        self.get_logger().info(f"Device listening")
        self._audio_stream.start_stream()
        self.stream_running = True
        self.recognition_start = time.time()

    def get_rate(self):
        return self._samplerate

    def get_language(self):
        return self._language

def listen_loop(responses, stream):

    for response in responses:
        if get_current_time() - stream.start_time > STREAMING_LIMIT:
            stream.start_time = get_current_time()
            break

        if not response.results:
            continue
        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.

        result = response.results[0]
        if not result.alternatives:
            continue

        text = result.alternatives[0].transcript
        duration_sec = result.result_end_time.seconds
        confidence = result.alternatives[0].confidence
        # duration_nano = result.result_end_time.nano

        if result.is_final:
            result_length = time.time() - (stream.recognition_start+duration_sec)
            if confidence > 0.4 and result_length > 0.75: # TODO: adjust confidence threshold
                msg = String()
                msg.data = text
                stream.speech_final_publisher.publish(msg)
                stream.get_logger().info(f"Topic: {stream.speech_final_publisher.topic_name} confidence: {confidence:.2f} msg: {text}")
            else:
                stream.get_logger().warn(f"Topic: {stream.speech_final_publisher.topic_name} Rejected (conf: {confidence:.2f} len: {result_length:.2f} s) msg: {text}")
        else:
            msg = String()
            msg.data = text
            stream.speech_partial_publisher.publish(msg)
            stream.get_logger().debug(f"Topic: {stream.speech_partial_publisher.topic_name} msg: {text}")

def main(args=None):
    rclpy.init(args=args)
    node = SpeechTotextNode()

    RATE = node.get_rate()
    LANG = node.get_language() 

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=LANG)
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    try:
        # rclpy.spin(node)
        with node as stream:
            audio_generator = stream.generator()
            requests = (speech.StreamingRecognizeRequest(audio_content=content)
                        for content in audio_generator)
            responses = client.streaming_recognize(streaming_config, requests)
            listen_loop(responses, stream)

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        # rclpy.shutdown()

if __name__ == '__main__':
    main()