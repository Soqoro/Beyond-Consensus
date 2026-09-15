"""Canonical serialization, strict input handling, and durable local storage."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class BCError(Exception):
    """An actionable user-facing validation or execution error."""


def plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(plain(v) for v in value)
    if isinstance(value, Path):
        return str(value)
    return value


def canonical(value: Any) -> str:
    return json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path: str | Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BCError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique,
                          parse_constant=lambda x: (_ for _ in ()).throw(BCError(f"Invalid {x}")))
    except (OSError, ValueError) as exc:
        raise BCError(f"Cannot read JSON {path}: {exc}") from exc


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(canonical(value) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def directory_lock(path: Path) -> Iterator[None]:
    """Atomic mkdir lock. Never steals a potentially live lock, even after a crash."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise BCError(f"Lock exists: {path}. Check its owner/job before manually removing it.") from exc
    try:
        atomic_json(path / "owner.json", {"pid": os.getpid()})
        yield
    finally:
        (path / "owner.json").unlink(missing_ok=True)
        path.rmdir()


def strict_keys(data: dict[str, Any], allowed: set[str], required: set[str] = frozenset()) -> None:
    if not isinstance(data, dict):
        raise BCError("Expected a JSON object")
    if set(data) - allowed or required - set(data):
        raise BCError(f"Unknown keys {sorted(set(data)-allowed)}; missing keys {sorted(required-set(data))}")


def positive(value: float, name: str, allow_zero: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BCError(f"{name} must be finite numeric")
    if value < 0 or (value == 0 and not allow_zero):
        raise BCError(f"{name} must be {'nonnegative' if allow_zero else 'positive'}")
