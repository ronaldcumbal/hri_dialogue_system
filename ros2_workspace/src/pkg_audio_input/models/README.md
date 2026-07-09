The following models are stored in this location:
- yunet

WhisperLive models (used by stt_whisper_server/stt_whisper_client) are not placed
here — they're downloaded and cached under `~/.cache/whisper-live/` (or wherever
the `cache_path`/`faster_whisper_custom_model_path` ROS parameters point) on first run.
