from typing import NamedTuple, Protocol

import anthropic
import openai

from weekly_summary.models import Trace
from weekly_summary.prompt import render_user_message

DEFAULT_MODELS = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-5.5"}


class Completion(NamedTuple):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    truncated: bool = False  # hit max_tokens: the text may be cut off mid-answer


class LLMClient(Protocol):
    model: str

    def complete(self, system: str, user: str) -> str: ...


class AnthropicClient:
    def __init__(self, model: str, max_tokens: int = 1024) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.Anthropic(max_retries=6)  # ride out rate limits in parallel eval runs

    def complete(self, system: str, user: str) -> str:
        return self.complete_with_usage(system, user).text

    def complete_with_usage(self, system: str, user: str) -> Completion:
        response = self._client.messages.create(
            model=self.model,
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=self.max_tokens,
        )
        usage = getattr(response, "usage", None)
        return Completion(
            "".join(block.text for block in response.content if block.type == "text"),
            getattr(usage, "input_tokens", 0),
            getattr(usage, "output_tokens", 0),
            getattr(response, "stop_reason", None) == "max_tokens",
        )


class OpenAIClient:
    def __init__(self, model: str, max_tokens: int = 1024) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self._client = openai.OpenAI(max_retries=6)

    def complete(self, system: str, user: str) -> str:
        return self.complete_with_usage(system, user).text

    def complete_with_usage(self, system: str, user: str) -> Completion:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=self.max_tokens,
        )
        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return Completion(
            choice.message.content or "",
            getattr(usage, "prompt_tokens", 0),
            getattr(usage, "completion_tokens", 0),
            getattr(choice, "finish_reason", None) == "length",
        )


class ReplayClient:
    """Returns the recorded output for a known input. The system prompt is ignored."""

    model = "replay"

    def __init__(self, traces: list[Trace]) -> None:
        self._outputs = {render_user_message(t.input): t.output for t in traces}

    def complete(self, system: str, user: str) -> str:
        try:
            return self._outputs[user]
        except KeyError:
            raise LookupError(
                "ReplayClient has no recorded output for this input. "
                "It can only replay inputs that appear in its traces."
            ) from None


def make_client(provider: str, model: str | None, traces: list[Trace], max_tokens: int = 1024) -> LLMClient:
    match provider:
        case "anthropic":
            return AnthropicClient(model or DEFAULT_MODELS["anthropic"], max_tokens)
        case "openai":
            return OpenAIClient(model or DEFAULT_MODELS["openai"], max_tokens)
        case "replay":
            return ReplayClient(traces)
    raise ValueError(f"Unknown LLM_PROVIDER {provider!r}. Use anthropic, openai, or replay.")
