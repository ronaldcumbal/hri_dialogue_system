## Installing WhisperLive

The `stt_whisper_server` and `stt_whisper_client` nodes wrap
[WhisperLive](https://github.com/collabora/WhisperLive).

Install PortAudio (required for microphone input via PyAudio) then the pip package:

```bash
sudo apt update
sudo apt install portaudio19-dev
pip install whisper-live==0.9.0
```

**Install footprint:** `whisper-live` has no client/server extras — installing it
(even "just for the client node") pulls in `torch`, `torchaudio`, `faster-whisper`,
`openai-whisper`, `openvino*`, `optimum*`, and on Linux `nvidia-cublas-cu12`/
`nvidia-cudnn-cu12` — a multi-GB install. This is only expected to be acceptable
because `stt_whisper_server` and `stt_whisper_client` are meant to run on the
same machine (the server needs the full stack regardless).

## Running the server

First run downloads the selected `model` (e.g. `small`) via faster-whisper/HuggingFace
into `cache_path` (default `~/.cache/whisper-live/`), which needs internet access —
unlike the old Vosk flow, models are not manually placed under `pkg_audio_input/models/`.

```bash
ros2 run pkg_audio_input stt_whisper_server --ros-args -p port:=9090
```

## Running the client

The client always publishes to `/user_speech` (finalized utterances) and
`/user_speech_partial` (live/interim text), same as the previous STT nodes.

Find your microphone's device index from the client's own startup log (it lists all
available input devices), or via:

```bash
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"
```

```bash
ros2 run pkg_audio_input stt_whisper_client --ros-args -p device:=3 -p model:=small
```

`device:=-1` (the default) uses the system's default input device — WhisperLive's
client only exposes a single audio sample rate/channel configuration (16kHz mono),
so unlike the old nodes there are no `sample_rate`/`channels` parameters.

## Installing Speechmatics

The `stt_speechmatics` node wraps [speechmatics-rt](https://github.com/speechmatics/speechmatics-python-sdk),
a hosted (cloud) real-time transcription API — no local model/GPU needed.

```bash
sudo apt update
sudo apt install portaudio19-dev
pip install speechmatics-rt==1.1.0 pyaudio
```

Requires a Speechmatics API key, set via the `SPEECHMATICS_API_KEY` environment
variable (not a ROS parameter, to keep it out of launch files/`ros2 param`). It
publishes to the same `/user_speech` / `/user_speech_partial` topics, and lists
available input devices at startup (also via `device:=-1` for the default input
device, same as `stt_whisper_client`).

```bash
ros2 run pkg_audio_input stt_speechmatics --ros-args -p device:=3 -p language:=en
```
