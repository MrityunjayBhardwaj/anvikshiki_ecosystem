"""
ReasoningLM — dspy.LM wrapper for reasoning models (GLM-5, DeepSeek-R1, etc.).

Reasoning models route JSON output to `reasoning_content` instead of `content`
when `response_format=json_object` is set. This wrapper strips that flag so the
model outputs JSON in `content` naturally (the prompt already asks for JSON).

It also provides a fallback: if `content` is still empty, it copies
`reasoning_content` into `content` so DSPy can parse it.

Usage:
    from anvikshiki_v4.reasoning_lm import ReasoningLM

    lm = ReasoningLM(
        "openai/zai-org/GLM-5",
        api_key=key,
        api_base="https://api.deepinfra.com/v1/openai",
        max_tokens=4096,
    )
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter())
"""

from typing import Any

import dspy


class ReasoningLM(dspy.LM):
    """LM wrapper that handles reasoning models' content/reasoning_content split."""

    def forward(
        self,
        prompt: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        **kwargs,
    ):
        # Strip response_format — it causes reasoning models to put JSON
        # in reasoning_content instead of content.
        kwargs.pop("response_format", None)

        results = super().forward(prompt=prompt, messages=messages, **kwargs)

        # Fallback: if content is empty, copy reasoning_content into content.
        if hasattr(results, "choices"):
            for choice in results.choices:
                if hasattr(choice, "message") and not choice.message.content:
                    extra = getattr(choice.message, "model_extra", {}) or {}
                    rc = extra.get("reasoning_content", "")
                    if rc:
                        choice.message.content = rc

        return results
