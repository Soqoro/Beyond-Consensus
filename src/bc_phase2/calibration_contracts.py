"""Offline development-data and token-observation contracts.

No dataset loading, model dispatch, price conversion or campaign authorization.
Source identities and counts are supplied evidence, not independently verified.
The existing synthetic runtime/Usage representation remains unchanged.
"""
from dataclasses import dataclass

from .data import adapt, source_split
from .model import Invalid, digest


def _name(value):
    if type(value) is not str or not value.strip():
        raise Invalid('explicit nonempty identity required')


@dataclass(frozen=True)
class SourceBinding:
    dataset: str
    revision: str
    problem_id: str
    source_family: str
    split: str

    def __post_init__(self):
        for value in (self.dataset, self.revision, self.problem_id, self.source_family):
            _name(value)
        if self.split not in ('development', 'test'):
            raise Invalid('development or test binding required')


def validate_split(bindings):
    """Check declared identities/families; not semantic duplicate detection.

    Revision is deliberately excluded from the source identity used for overlap:
    a new release does not turn the same problem into an independent source.
    Family identifiers must use a common namespace across datasets/releases.
    """
    if type(bindings) is not tuple or not bindings or any(type(b) is not SourceBinding for b in bindings):
        raise Invalid('immutable source bindings required')
    ids = {'development': [], 'test': []}
    families = {'development': set(), 'test': set()}
    for b in bindings:
        ids[b.split].append(digest([b.dataset, b.problem_id]))
        families[b.split].add(b.source_family)
    if not all(ids.values()):
        raise Invalid('explicit nonempty development and held-out sets required')
    source_split(ids['development'], ids['test'])
    if families['development'] & families['test']:
        raise Invalid('source-family leakage')
    return {'binding_digest': digest(sorted(bindings, key=lambda b: (b.dataset, b.problem_id, b.revision))),
            'declared_overlap_checks_passed': True,
            'semantic_deduplication_verified': False, 'task_execution_allowed': False}


def math_development_views(binding, row):
    """Strict wrapper around the existing public/private synthetic adapter.

    Normalized records are injected; this does not implement the official dataset
    loader or evaluator. Metadata, solutions and raw extras are never forwarded.
    """
    if type(binding) is not SourceBinding or binding.dataset != 'HuggingFaceH4/MATH-500':
        raise Invalid('MATH-500 binding required')
    if binding.split != 'development':
        raise Invalid('held-out records forbidden in calibration')
    if type(row) is not dict or row.get('id') != binding.problem_id:
        raise Invalid('record source mismatch')
    _name(row.get('problem'))
    if row.get('answer') is not None:
        _name(row['answer'])
    return adapt('math500', row)


@dataclass(frozen=True)
class TokenObservation:
    """Input includes cached tokens; output includes reasoning tokens.

    Providers with other conventions need an explicitly reviewed normalization.
    No synthetic-work or monetary conversion is implied by these observations.
    """
    physical_attempt_id: str
    logical_slot_id: str
    model_binding: str
    tokenizer_binding: str
    status: str
    input_tokens: object = None
    output_tokens: object = None
    cached_input_tokens: object = None
    reasoning_output_tokens: object = None

    def __post_init__(self):
        for value in (self.physical_attempt_id, self.logical_slot_id,
                      self.model_binding, self.tokenizer_binding):
            _name(value)
        if self.status not in ('complete', 'incomplete', 'unknown'):
            raise Invalid('usage status')
        for value in (self.input_tokens, self.output_tokens,
                      self.cached_input_tokens, self.reasoning_output_tokens):
            if value is not None and (type(value) is not int or value < 0):
                raise Invalid('nonnegative integer counts or unknown required')
        if self.status == 'complete' and (self.input_tokens is None or self.output_tokens is None):
            raise Invalid('complete usage requires both counts')
        for subset, total in ((self.cached_input_tokens, self.input_tokens),
                              (self.reasoning_output_tokens, self.output_tokens)):
            if subset is not None and total is not None and subset > total:
                raise Invalid('subset exceeds inclusive token count')

    @property
    def total_tokens(self):
        if self.status != 'complete':
            return None
        return self.input_tokens + self.output_tokens

    @property
    def retain_reservation(self):
        return self.status != 'complete'
