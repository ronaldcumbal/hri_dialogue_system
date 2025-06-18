import zmq
import pyaudio
from pydub import AudioSegment
import threading
import io

# Configuration
ZMQ_ADDRESS = "tcp://10.0.1.10:3001"
SAMPLE_RATE = 16000
CHANNELS = 2
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes
CHUNK_SIZE = 1024  # in bytes
OUTPUT_FILE_LEFT = "microphone_left.mp3"
OUTPUT_FILE_RIGHT = "speech_right.mp3"

# PyAudio setup for playback
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=CHUNK_SIZE)

# Buffers for left and right channels
buffer_left = bytearray()
buffer_right = bytearray()

# ZMQ setup
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect(ZMQ_ADDRESS)
socket.setsockopt(zmq.SUBSCRIBE, b'')

def separate_channels(stereo_bytes: bytes) -> tuple[bytes, bytes]:
    """Split interleaved stereo PCM bytes into (left, right)"""
    import array
    samples = array.array('h', stereo_bytes)  # 'h' = 16-bit signed
    left = samples[::2]
    right = samples[1::2]
    return (array.array('h', left).tobytes(), array.array('h', right).tobytes())

def save_audio_thread():
    """Periodically saves audio buffers into MP3 files."""
    import time
    while True:
        if len(buffer_left) > SAMPLE_RATE * SAMPLE_WIDTH * 10:  # ~10 seconds
            segment_left = AudioSegment(
                data=bytes(buffer_left),
                sample_width=SAMPLE_WIDTH,
                frame_rate=SAMPLE_RATE,
                channels=1
            )
            segment_left.export(OUTPUT_FILE_LEFT, format="mp3")
            buffer_left.clear()
            print(f"[+] Saved left channel to {OUTPUT_FILE_LEFT}")

        if len(buffer_right) > SAMPLE_RATE * SAMPLE_WIDTH * 10:
            segment_right = AudioSegment(
                data=bytes(buffer_right),
                sample_width=SAMPLE_WIDTH,
                frame_rate=SAMPLE_RATE,
                channels=1
            )
            segment_right.export(OUTPUT_FILE_RIGHT, format="mp3")
            buffer_right.clear()
            print(f"[+] Saved right channel to {OUTPUT_FILE_RIGHT}")

        time.sleep(5)

# Start saving thread
threading.Thread(target=save_audio_thread, daemon=True).start()

print("Streaming and saving audio... Press Ctrl+C to stop.")

try:
    while True:
        chunk = socket.recv()
        stream.write(chunk)  # Playback as stereo
        left, right = separate_channels(chunk)
        buffer_left.extend(left)
        buffer_right.extend(right)
except KeyboardInterrupt:
    print("Interrupted by user.")
finally:
    print("Cleaning up and saving remaining audio...")
    
    if buffer_left:
        segment_left = AudioSegment(
            data=bytes(buffer_left),
            sample_width=SAMPLE_WIDTH,
            frame_rate=SAMPLE_RATE,
            channels=1
        )
        segment_left.export(OUTPUT_FILE_LEFT, format="mp3")
        print(f"[+] Saved final left channel to {OUTPUT_FILE_LEFT}")

    if buffer_right:
        segment_right = AudioSegment(
            data=bytes(buffer_right),
            sample_width=SAMPLE_WIDTH,
            frame_rate=SAMPLE_RATE,
            channels=1
        )
        segment_right.export(OUTPUT_FILE_RIGHT, format="mp3")
        print(f"[+] Saved final right channel to {OUTPUT_FILE_RIGHT}")

    stream.stop_stream()
    stream.close()
    p.terminate()
    socket.close()
    context.term()