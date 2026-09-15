"""Deterministic fixture compiler. Knows no policy, attack, or hidden test results."""

from __future__ import annotations

import json
import math

from .base import Generation
from ..util import canonical


class MockBackend:
    def count_input(self, messages: list[dict[str, str]]) -> int:
        return math.ceil(len(canonical(messages).encode()) / 4)

    def generate(self, messages: list[dict[str, str]], max_new_tokens: int, seed: int) -> Generation:
        request = next(json.loads(m["content"]) for m in reversed(messages)
                       if m["role"] == "user" and m["content"].startswith('{"assignment":'))
        unit = request["assignment"]
        source = None
        for message in messages:
            if message["role"] != "user":
                continue
            try:
                observation = json.loads(message["content"])
            except ValueError:
                continue
            if observation.get("tool") == "read_source" and observation.get("name") == unit:
                source = observation["result"]
        if source is None:
            action = {"tool": "read_source", "name": unit}
        elif request["operation"] == "prepare":
            action = {"tool": "submit", "content": {"outline": "multiply, add, clamp", "contract": source}}
        else:
            action = {"tool": "submit", "content": {"steps": [
                {"op": "mul", "value": source["scale"]},
                {"op": "add", "value": source["offset"]},
                {"op": "max", "value": source["lower_bound"]}]}}
        raw = canonical(action)
        # Truncation here models a hard generation cap; parser then charges/retries.
        raw = raw[:max_new_tokens * 4]
        return Generation(raw, math.ceil(len(raw.encode()) / 4))
