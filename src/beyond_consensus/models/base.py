from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Generation:
    text: str
    output_tokens: int
    reasoning_tokens: int | None = 0  # Subset of output_tokens, never added again.
    device_seconds: float | None = None


class Backend(Protocol):
    def count_input(self, messages: list[dict[str, str]]) -> int: ...
    def generate(self, messages: list[dict[str, str]], max_new_tokens: int, seed: int) -> Generation: ...
