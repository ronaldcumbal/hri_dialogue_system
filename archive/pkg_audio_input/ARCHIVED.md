`stt_google.py` and `stt_vosk.py` were moved here out of `pkg_audio_input` while the
speech-to-text service is being replaced. They were the active STT nodes
(publishing to `/user_speech` / `/user_speech_partial`), fixed for correctness
in the Phase 1 cleanup (see `DEVELOPMENT_PLAN.md`), but are no longer wired
into `pkg_launch/launch/system_launch.py` or `pkg_audio_input/setup.py`'s
entry points. Kept here for reference.
