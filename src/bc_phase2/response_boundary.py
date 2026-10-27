"""Offline raw-text bridge to the existing decoded allocation contract.

No model/template/provider imports or dispatch. Inputs are completed response
texts supplied for review, not an instruction to generate or retry. Usage and
termination metadata must be verified by a future execution adapter separately.
"""
import json

from .allocation import llm_reply
from .model import Invalid


# A parser resource bound, not a model token limit or scientific task budget.
MAX_RESPONSE_BYTES = 65536


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Invalid('duplicate JSON object key')
        result[key] = value
    return result


def _constant(value):
    raise Invalid('nonfinite JSON constant')


def decode_response(text):
    """Decode exactly one JSON value without extracting or repairing text."""
    if type(text) is not str:
        raise Invalid('response must be text')
    try:
        if len(text.encode('utf-8')) > MAX_RESPONSE_BYTES:
            raise Invalid('response byte limit')
        value = json.loads(text, object_pairs_hook=_object,
                           parse_constant=_constant)
        # Python's JSON decoder accepts escaped unpaired surrogates. Require
        # decoded strings to be representable as UTF-8, without normalization.
        json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (ValueError, UnicodeError, RecursionError, OverflowError) as exc:
        raise Invalid('invalid JSON response') from exc
    return value


def review_allocation_texts(workflow, n, texts):
    """Review one initial response and at most one supplied correction.

    Parse failures occupy their original attempt slot. The existing validator
    remains authoritative for schemas, partitions and extra corrections. This
    function neither authorizes nor schedules any additional call.
    """
    if type(texts) not in (list, tuple) or not 1 <= len(texts) <= 2:
        raise Invalid('initial response plus at most one correction')
    decoded = []
    parsing = []
    for text in texts:
        if decoded and llm_reply(workflow, n, decoded)['status'] == 'valid':
            # Reject the extra transcript entry without inspecting its content.
            decoded.append(None)
            parsing.append('not_read')
            break
        try:
            decoded.append(decode_response(text))
            parsing.append('decoded')
        except Invalid:
            decoded.append(None)  # An invalid attempt, never removed or repaired.
            parsing.append('invalid')
    result = llm_reply(workflow, n, decoded)
    return {**result, 'parsing': parsing, 'evidence': 'offline_supplied_texts',
            'usage_verified': False, 'model_executed': False,
            'task_execution_allowed': False}
