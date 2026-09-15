"""Append-only events, atomic results, provenance-pinned logical IDs and attempts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..util import BCError, atomic_json, canonical, digest, read_json


class EpisodeJournal:
    def __init__(self, root: Path, episode_id: str) -> None:
        self.path = root / "episodes" / episode_id
        self.path.mkdir(parents=True, exist_ok=True)

    def event(self, kind: str, **data: Any) -> None:
        with (self.path / "events.jsonl").open("a", encoding="utf-8", newline="\n") as f:
            f.write(canonical({"type": kind, **data}) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def begin(self, manifest_hash: str) -> str:
        attempts = self.path / "attempts"
        attempts.mkdir(exist_ok=True)
        sequence = len(list(attempts.glob("*.json")))
        attempt = digest([self.path.name, manifest_hash, sequence])
        atomic_json(attempts / f"{attempt}.json", {"attempt_id": attempt, "sequence": sequence,
                                                  "manifest_hash": manifest_hash})
        self.event("attempt_started", attempt_id=attempt)
        return attempt

    def checkpoint(self, state: dict[str, Any]) -> None:
        atomic_json(self.path / "checkpoint.json", state)

    def previous(self, manifest_hash: str) -> dict[str, Any] | None:
        path = self.path / "checkpoint.json"
        if not path.exists():
            return None
        state = read_json(path)
        if state["manifest_hash"] != manifest_hash:
            raise BCError("Checkpoint provenance mismatch; create a new run")
        return state

    def result(self, value: Any) -> None:
        atomic_json(self.path / "result.json", value)
        self.event("attempt_finished", attempt_id=value.attempt_id, status=value.status)
