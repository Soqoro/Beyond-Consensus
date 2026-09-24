"""Small portable serialization boundary; no optional imports."""
import hashlib
import json
import math
import re
from pathlib import Path


class Rejected(ValueError):
    """Public fixed-category failure; never expose paths or evaluator values."""


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bounded(value, size=131072, depth=24, nodes=8000):
    pending = [(value, 0)]
    count = 0
    while pending:
        v, d = pending.pop(); count += 1
        if d > depth or count > nodes:
            raise Rejected('data_complexity')
        if isinstance(v, dict):
            if any(not isinstance(k, str) for k in v): raise Rejected('data_keys')
            pending.extend((x, d+1) for x in v.values())
        elif isinstance(v, list): pending.extend((x, d+1) for x in v)
        elif v is not None and type(v) not in (str, int, float, bool): raise Rejected('data_type')
        if type(v) is float and not math.isfinite(v): raise Rejected('nonfinite')
    if len(encoded(value)) > size: raise Rejected('data_size')
    return value


def ident(s):
    if not isinstance(s, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', s):
        raise Rejected('identifier')
    return s


def load(path):
    raw = Path(path).read_bytes()
    if len(raw) > 2097152: raise Rejected('file_size')
    def pairs(items):
        result = {}
        for k,v in items:
            if k in result: raise Rejected('duplicate_key')
            result[k] = v
        return result
    return bounded(json.loads(raw, object_pairs_hook=pairs), size=2097152, nodes=100000)


def write_new(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False); f.write('\n')
