"""Versioned artifacts and mediated messages with conservative context taint."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from ..schemas import ArtifactVersion, WORKERS
from ..util import BCError, digest, plain


@dataclass
class Context:
    identity: str
    messages: list[dict[str, str]] = field(default_factory=list)
    reads: set[str] = field(default_factory=set)
    contributors: set[str] = field(default_factory=set)
    source_hashes: set[str] = field(default_factory=set)
    complete: bool = True


class ProvenanceStore:
    def __init__(self) -> None:
        self.artifacts: dict[str, ArtifactVersion] = {}
        self.contexts = {w: Context(w, contributors={w}) for w in WORKERS}
        self.snapshots: dict[str, list[Context]] = {w: [] for w in WORKERS}
        self.events: list[dict[str, Any]] = []

    def save_context(self, identity: str) -> None:
        self.snapshots[identity].append(copy.deepcopy(self.contexts[identity]))

    def reset(self, identity: str) -> None:
        # Identity state belongs to the attacker, never to a context.
        self.contexts[identity] = Context(identity, contributors={identity})
        self.events.append({"type": "context_reset", "identity": identity})

    def source(self, identity: str, name: str, content: Any) -> None:
        h = digest(content)
        self.contexts[identity].source_hashes.add(h)
        self.events.append({"type": "source_read", "identity": identity, "name": name, "hash": h})

    def read(self, identity: str, artifact_id: str) -> Any:
        if artifact_id not in self.artifacts:
            raise BCError(f"Missing provenance record for artifact {artifact_id}")
        artifact = self.artifacts[artifact_id]
        if not artifact.valid or not artifact.complete_provenance:
            raise BCError(f"Artifact {artifact_id} is invalid or has incomplete provenance")
        ctx = self.contexts[identity]
        ctx.reads.add(artifact_id)
        ctx.contributors.update(artifact.contributors)
        ctx.source_hashes.update(artifact.source_hashes)
        self.events.append({"type": "artifact_read", "identity": identity, "version": artifact_id})
        return copy.deepcopy(artifact.content)

    def message(self, sender: str, recipient: str, text: str) -> None:
        src, dst = self.contexts[sender], self.contexts[recipient]
        dst.reads.update(src.reads)
        dst.contributors.update(src.contributors | {sender})
        dst.source_hashes.update(src.source_hashes)
        dst.complete = dst.complete and src.complete
        dst.messages.append({"role": "user", "content": f"Message from {sender}: {text}"})
        self.events.append({"type": "message", "sender": sender, "recipient": recipient,
                            "text_hash": digest(text), "reads": sorted(src.reads),
                            "contributors": sorted(src.contributors | {sender})})

    def declared_reads(self, identity: str, versions: tuple[str, ...] | None) -> None:
        if versions is None:
            self.contexts[identity].complete = False
            raise BCError("Opaque tools require a conservative declared read set")
        for version in versions:
            self.read(identity, version)

    def submit(self, identity: str, unit: str, content: Any, kind: str = "implementation") -> ArtifactVersion:
        ctx = self.contexts[identity]
        if not ctx.complete:
            raise BCError("Cannot submit with missing dependency records")
        key = digest({"unit": unit, "author": identity, "content": content,
                      "sequence": len(self.artifacts), "parents": sorted(ctx.reads)})
        artifact = ArtifactVersion(key, unit, identity, copy.deepcopy(content),
                                   tuple(sorted(ctx.reads)), tuple(sorted(ctx.contributors)),
                                   tuple(sorted(ctx.source_hashes)), kind)
        self.artifacts[key] = artifact
        self.events.append({"type": "submit", "version": key, "author": identity, "unit": unit})
        # The submitted action remains in the author's context. Later messages
        # and artifacts therefore inherit this version even without an explicit
        # read-back tool call. The artifact itself does not depend on itself.
        ctx.reads.add(key)
        return artifact

    def invalidate(self, versions: set[str], suspects: set[str] = frozenset()) -> set[str]:
        if versions - self.artifacts.keys():
            raise BCError("Cannot invalidate an unrecorded version")
        invalid = set(versions)
        changed = True
        while changed:
            changed = False
            for key, a in self.artifacts.items():
                if key not in invalid and (set(a.parents) & invalid or set(a.contributors) & suspects):
                    invalid.add(key)
                    changed = True
        for key in invalid:
            self.artifacts[key].valid = False
        for identity, ctx in list(self.contexts.items()):
            if ctx.reads & invalid or (ctx.contributors - {identity}) & suspects:
                restored = next((c for c in reversed(self.snapshots[identity])
                                 if not c.reads & invalid and not (c.contributors - {identity}) & suspects), None)
                if restored is None:
                    self.reset(identity)
                else:
                    self.contexts[identity] = copy.deepcopy(restored)
                    self.events.append({"type": "context_restore", "identity": identity})
        self.events.append({"type": "invalidate", "versions": sorted(invalid), "suspicions": sorted(suspects)})
        return invalid

    def export(self) -> dict[str, Any]:
        return plain({"artifacts": self.artifacts, "contexts": self.contexts,
                      "snapshots": self.snapshots, "events": self.events})

    @classmethod
    def restore(cls, state: dict[str, Any]) -> ProvenanceStore:
        store = cls()
        def context(data: dict[str, Any]) -> Context:
            return Context(data["identity"], data["messages"], set(data["reads"]),
                           set(data["contributors"]), set(data["source_hashes"]), data["complete"])
        store.contexts = {w: context(v) for w, v in state["contexts"].items()}
        store.snapshots = {w: [context(c) for c in values] for w, values in state["snapshots"].items()}
        for key, data in state["artifacts"].items():
            data = dict(data)
            for name in ("parents", "contributors", "source_hashes"):
                data[name] = tuple(data[name])
            store.artifacts[key] = ArtifactVersion(**data)
        store.events = state["events"]
        return store
