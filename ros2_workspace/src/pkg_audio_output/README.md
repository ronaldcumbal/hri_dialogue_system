## Installing Speechmatics TTS

The `tts_speechmatics` node wraps [speechmatics-tts](https://github.com/speechmatics/speechmatics-python-sdk),
a hosted (cloud) text-to-speech API. It subscribes to `/robo_speech`
(`std_msgs/String`) and streams the synthesized audio straight to an output
device via `sounddevice` — no intermediate audio file.

```bash
pip install speechmatics-tts==0.1.2 sounddevice numpy
```

Requires a Speechmatics API key, set via the `SPEECHMATICS_API_KEY` environment
variable (not a ROS parameter, same reasoning as `stt_speechmatics`).

Find your output device index from the node's own startup log (it lists all
available output devices), then:

```bash
ros2 run pkg_audio_output tts_speechmatics --ros-args -p device:=3 -p voice:=jack
ros2 topic pub /robo_speech std_msgs/String "data: 'hello there'"
```

`device:=-1` (the default) uses the system's default output device. `voice`
accepts one of `sarah`, `theo`, `megan`, `jack` (per Speechmatics' `Voice` enum).
Utterances are queued and played back one at a time, in order, so they never
overlap.
