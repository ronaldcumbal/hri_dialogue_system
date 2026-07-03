# Development Plan

This document tracks the plan to take the HRI dialogue system from its current
skeleton/draft state to a working conversational system for a gaze-only
(camera pan/tilt) robot, capable of handling conversations with multiple
people.

## Current status (as of this plan)

- Working pipeline: `usb_cam` -> `hri_face_detect` (locally patched PAL
  Robotics package), launched via
  `ros2_workspace/src/pkg_launch/launch/system_launch.py`. Everything else in
  that launch file is commented out.
- `pkg_reasoning` contains two parallel, incompatible dialogue
  implementations: a pub/sub pair (`dialogue_manager.py` + `llm_prompter.py`,
  wired into `setup.py` entry points) and a service-based pair
  (`dialogue_client.py` + `llm_service.py`, not registered as entry points).
- `pkg_audio_input`'s `stt_vosk.py` has a crash bug: the Vosk `Model` is never
  instantiated but is referenced in `start_listening`.
- `woz_reception` is built specifically for a Furhat robot (ZMQ camera/mic
  bridges, `furhat_remote_api`) with hardcoded paths to a different
  machine/user. Confirmed legacy from a prior project; not part of the
  current gaze robot.
- The README describes `pkg_visual_input`, `pkg_sensor_input`,
  `pkg_embodiment`, `pkg_output`, `pkg_interfaces` as planned packages; none
  of these exist yet. There is no code anywhere that actuates the gaze
  motors.
- Only ament boilerplate tests (copyright/flake8/pep257) exist; no
  functional test coverage.

## Decisions made

- `woz_reception`: legacy, will be removed from the active build (not fixed).
- Canonical dialogue architecture: pub/sub (`dialogue_manager` +
  `llm_prompter`). Service-based files are dead code to be deleted.
- Gaze actuation hardware/firmware: not built yet. Treated as a future
  design task — start with a defined ROS interface + stub driver.
- LLM backend: support OpenAI, Anthropic, and Google Gemini, selectable via
  a pluggable provider interface (existing `llm_model` parameter).

## Phase 1 — Fix & stabilize existing packages

1. **`pkg_reasoning` — consolidate the dialogue architecture**
   - Delete `dialogue_client.py` and `llm_service.py` (dead code, not in
     entry points).
   - Make `llm_prompter.py` provider-pluggable: a small `LLMClient`
     interface with `openai`/`anthropic`/`google` implementations, selected
     via the `llm_model` parameter.
   - `dialogue_manager.py` has half-built debounce logic (`timer_running`
     / `lock` / `timer` fields exist but nothing ever starts `self.timer`) —
     finish the debounce (wait for a pause before sending to the LLM) or
     strip the dead fields.
   - `pkg_commons`'s `DialogueTurn.srv` only existed for the service code
     being deleted — remove it.

2. **`pkg_audio_input` — fix the real bug + reduce duplication**
   - Fix `stt_vosk.py`: instantiate the Vosk `Model`, fix the undefined
     `self._listenning` reference.
   - Remove the hardcoded `/home/roncu858/...` path; use
     `get_package_share_directory` or a ROS parameter/env var.
   - Move magic numbers (0.4 confidence, 0.75s length threshold) to ROS
     parameters.
   - Longer term: share a base node between `stt_google.py`/`stt_vosk.py`
     to remove duplicated setup code.

3. **Remove `woz_reception` from the active build**
   - `COLCON_IGNORE` it or move it to an `archive/` folder rather than
     fixing its bugs. Keep it in git history for reference.

4. **`pkg_launch` cleanup**
   - Replace the large commented-out blocks in `system_launch.py` with
     launch arguments (`use_audio:=`, `use_reasoning:=`, etc.).
   - Wire in `camera_config.py`'s `CameraConfig` class or delete it (it's
     currently defined but unused).
   - Fix the `READM.md` typo.

5. **Testing/CI**
   - Add a smoke-test launch that brings up the
     camera -> face_detect -> dialogue chain and asserts expected topics
     appear.
   - Add a basic CI workflow (colcon build + lint).

## Phase 2 — Completing the system

Priority order, since multi-person conversation is the stated end goal:

1. **Attention/person-tracking node** (new package, e.g. `pkg_sensor_input`
   or `pkg_attention`): consume the per-face IDs already published by
   `hri_face_detect` (`/faces/tracked`, `/faces/{id}/roi`,
   `/faces/{id}/landmarks`) and decide who the robot is engaging with, e.g.
   expose `/attention/target_face_id`.
2. **`pkg_embodiment` gaze interface** — define the ROS interface (topic or
   action for gaze target) with a stub/simulated driver first, so the rest
   of the system can be built without waiting on hardware.
3. **`pkg_output`** — a generic dispatcher that maps `robot_action` strings
   (`say_`, `attend_`, `gesture_`) to the embodiment/TTS drivers, plus an
   actual TTS node (nothing currently turns `/llm_response` into speech).
4. **Multi-party dialogue state** — extend `dialogue_manager` to key state
   per speaker using the face IDs from step 1, instead of one global
   utterance buffer/state.
5. **`pkg_visual_input`** — formalize `local_modifications/hri_face_detect`
   as a tracked fork/subtree (instead of an ad hoc patched copy) so
   upstream changes aren't silently lost.
6. **`pkg_interfaces`** — scope only once the single-person loop
   (STT -> dialogue -> LLM -> TTS/gaze) works end-to-end.
