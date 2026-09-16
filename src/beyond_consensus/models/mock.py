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
        requests = []
        for index, message in enumerate(messages):
            try:
                data = json.loads(message["content"])
            except ValueError:
                continue
            if message["role"] == "user" and isinstance(data, dict) and "assignment" in data:
                requests.append((index, data))
        start, request = requests[-1]
        if request.get("environment") in ("sqlite_fixture", "silo"):
            action = self.data_action(request, messages[start+1:])
            raw = canonical(action)[:max_new_tokens*4]
            return Generation(raw, math.ceil(len(raw.encode())/4))
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

    @staticmethod
    def data_action(request, messages):
        observations = []
        for m in messages:
            if m["role"] == "user":
                try:
                    observations.append(json.loads(m["content"]))
                except ValueError:
                    pass
        unit = request["assignment"]
        sources = {o.get("name"): o["result"] for o in observations if o.get("tool") == "read_source" and "result" in o}
        if unit not in sources:
            return {"tool": "read_source", "name": unit}
        source = sources[unit]
        if request["operation"] == "prepare":
            return {"tool": "submit", "content": {"outline": "Read the assigned original contract and reconstruct all required outputs", "contract": source}}
        if request["environment"] == "sqlite_fixture":
            query = next((o for o in reversed(observations) if o.get("tool") == "run_read_query" and "artifact_id" in o), None)
            if query:
                return {"tool": "submit_required_artifact", "artifact_id": query["artifact_id"]}
            return {"tool": "run_read_query", "permitted_artifact_versions": {}, "select_sql": {
                "columns": [{"expr": {"column": "id"}}, {"expr": {"binary": ["*", {"column": "value"}, {"literal": source["factor"]}]}}],
                "from": {"table": source["table"]}, "order_by": [{"expr": {"column": "id"}}]}}
        # Deterministic test worker only uses its visible tool observations.
        # This is not exposed as a calculator to the real model.
        shards = {o["unit"]: o["result"] for o in observations if o.get("tool") == "read_shard" and "result" in o}
        if unit not in shards:
            return {"tool": "read_shard", "unit": unit}
        previous = source["previous"]
        earlier = next((o["result"]["answer"] for o in reversed(observations) if o.get("tool") == "read_artifact"
            and isinstance(o.get("result"), dict) and "answer" in o["result"]), None)
        if previous and earlier is None:
            if request["operation"] != "replicate":
                prior = next((a for a in request.get("published_artifacts", []) if a["unit"] == previous), None)
                if prior:
                    return {"tool": "read_artifact", "version": prior["version"]}
            for i in range(source["segment"]):
                if f"u{i}" not in shards:
                    return {"tool": "read_shard", "unit": f"u{i}"}
        state = earlier[-1] if earlier else 0
        segments = [shards[unit]] if earlier else [shards[f"u{i}"] for i in range(source["segment"]+1)]
        answer = []
        for segment in segments:
            answer = []
            for value in segment:
                state = state + value if source["family"] == "II-11" else ((sum(ord(c) for c in value)%10000)^state)%10000
                answer.append(state)
        return {"tool": "submit_result", "answer": answer}
