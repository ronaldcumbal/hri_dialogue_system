from abc import ABC, abstractmethod

SYSTEM_PROMPT = "You are a helpful assistant."


class LLMClient(ABC):

    @abstractmethod
    def generate(self, user_input: str) -> str:
        ...


class TestClient(LLMClient):
    """Echoes a canned response, used to test the dialogue pipeline without any API keys."""

    def generate(self, user_input: str) -> str:
        import time
        return f"Response from test model {time.time()}"


class OpenAIClient(LLMClient):

    def __init__(self, model: str = "gpt-4o", max_tokens: int = 200):
        import openai
        self._client = openai.OpenAI()
        self._model = model
        self._max_tokens = max_tokens

    def generate(self, user_input: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input},
            ],
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content


class AnthropicClient(LLMClient):

    def __init__(self, model: str = "claude-sonnet-4-5", max_tokens: int = 200):
        import anthropic
        self._client = anthropic.Anthropic()
        self._model = model
        self._max_tokens = max_tokens

    def generate(self, user_input: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_input}],
        )
        return response.content[0].text


class GoogleClient(LLMClient):

    def __init__(self, model: str = "gemini-2.5-flash", max_tokens: int = 200):
        from google import genai
        from google.genai import types
        self._client = genai.Client()
        self._model = model
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT, max_output_tokens=max_tokens)

    def generate(self, user_input: str) -> str:
        response = self._client.models.generate_content(
            model=self._model, contents=user_input, config=self._config)
        return response.text


_CLIENTS = {
    "test": TestClient,
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "google": GoogleClient,
}


def create_llm_client(name: str) -> LLMClient:
    if name not in _CLIENTS:
        raise ValueError(f"Unsupported LLM model '{name}', expected one of {list(_CLIENTS)}")
    return _CLIENTS[name]()
