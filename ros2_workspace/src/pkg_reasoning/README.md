## LLM backends

The `llm_prompter` node selects its backend through the `llm_model` ROS
parameter. Supported values: `test` (default, no API key needed), `openai`,
`anthropic`, `google`. Only install the SDK for the backend(s) you plan to
use; each is imported lazily by `pkg_reasoning/llm_clients.py`.

Example:

`ros2 run pkg_reasoning llm_prompter --ros-args -p llm_model:=anthropic`

### OpenAI

`pip install openai` and set `OPENAI_API_KEY`.

### Anthropic

`pip install anthropic` and set `ANTHROPIC_API_KEY`.

### Google GenAI

Follow [tutorial](https://ai.google.dev/gemini-api/docs/quickstart)

`pip install -q -U google-genai` and set `GEMINI_API_KEY`.
