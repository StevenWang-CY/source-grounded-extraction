"""Local MLX inference and a small OpenAI-compatible HTTP adapter."""

import json
import os
import time
import urllib.request
from dataclasses import asdict, dataclass


@dataclass
class Call:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    latency_seconds: float
    finish_reason: str
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class ReplayBackend:
    """Return one execution's saved responses in order, without model inference."""

    def __init__(self, result: dict):
        self.calls = result["calls"]
        self.position = 0
        self.settings = {"backend": "replay", "original_model": result["model_settings"]}

    def complete(self, messages: list[dict]) -> Call:
        if self.position >= len(self.calls):
            raise RuntimeError("No saved response for this call")
        saved = self.calls[self.position]
        if messages != saved["messages"]:
            raise RuntimeError("Replay input or prompt differs from the saved call")
        self.position += 1
        # The October development run saved its calls before call errors were recorded.
        return Call(saved["text"], 0, 0, 0.0, "replayed", saved.get("error"))


class MLXBackend:
    def __init__(self, model: str, max_tokens: int = 512, temperature: float = 0.0):
        from mlx_lm import load

        self.model_name = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model, self.tokenizer = load(model)

    @property
    def settings(self) -> dict:
        return {
            "backend": "mlx",
            "model": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "thinking": False,
            "seed": 17,
            "estimated_api_cost_usd": 0.0,
            "cost_basis": "local inference; no billed API calls; hardware and electricity excluded",
        }

    def complete(self, messages: list[dict]) -> Call:
        import mlx.core as mx
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler

        mx.random.seed(17)
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        start = time.perf_counter()
        text = ""
        last = None
        for part in stream_generate(
            self.model,
            self.tokenizer,
            prompt,
            max_tokens=self.max_tokens,
            sampler=make_sampler(temp=self.temperature),
        ):
            text += part.text
            last = part
        if last is None:
            raise RuntimeError("The model generated no output")
        return Call(
            text,
            last.prompt_tokens,
            last.generation_tokens,
            time.perf_counter() - start,
            str(last.finish_reason),
        )


class HTTPBackend:
    """Optional adapter for an existing compatible endpoint; no SDK required."""

    def __init__(self, model: str, base_url: str, max_tokens: int = 512, temperature: float = 0.0):
        self.model_name, self.base_url = model, base_url.rstrip("/")
        self.max_tokens, self.temperature = max_tokens, temperature

    @property
    def settings(self) -> dict:
        return {
            "backend": "http",
            "model": self.model_name,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "estimated_api_cost_usd": None,
            "cost_basis": "not estimated; configure endpoint pricing separately",
        }

    def complete(self, messages: list[dict]) -> Call:
        headers = {"Content-Type": "application/json"}
        if os.environ.get("CRM_MODEL_API_KEY"):
            headers["Authorization"] = "Bearer " + os.environ["CRM_MODEL_API_KEY"]
        body = json.dumps(
            {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        ).encode()
        request = urllib.request.Request(
            self.base_url + "/chat/completions", data=body, headers=headers
        )
        start = time.perf_counter()
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.load(response)
        choice = result["choices"][0]
        text = choice["message"]["content"]
        usage = result.get("usage") or {}
        tokens = [usage.get("prompt_tokens"), usage.get("completion_tokens")]
        if not isinstance(text, str) or not all(t is None or type(t) is int for t in tokens):
            raise ValueError("The endpoint returned no text or invalid token counts")
        latency = time.perf_counter() - start
        return Call(text, *tokens, latency, choice.get("finish_reason", "unknown"))
