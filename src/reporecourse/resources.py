"""Logical token totals and independent CPU caps, not BC surrogate units."""
from dataclasses import dataclass, field
import time
from .common import Rejected

PROFILE = 'rr-logical-tokens-cpu-v1'


@dataclass
class Resources:
    token_cap: int = 100000
    cpu_cap: float = 120
    actual_tokens: int = 0
    cpu_seconds: float = 0
    reservations: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    uncertain_tokens: int = 0
    cpu_reserved: float = 0

    def __post_init__(self):
        if type(self.token_cap) is not int or self.token_cap < 1 or self.cpu_cap <= 0:
            raise Rejected('resource_profile')

    @property
    def remaining(self):
        return self.token_cap-self.actual_tokens-self.uncertain_tokens-sum(a+b for a,b in self.reservations.values())

    def reserve(self, input_tokens, output_cap):
        if any(type(x) is not int or x < 0 for x in (input_tokens,output_cap)):
            raise Rejected('usage')
        if input_tokens+output_cap > self.remaining: raise Rejected('token_cap')
        key = str(len(self.events)); self.reservations[key] = (input_tokens,output_cap)
        self.events.append(dict(kind='reservation', id=key, input=input_tokens, output_cap=output_cap))
        return key

    def reconcile(self, key, output_tokens=None, reasoning_tokens=None, **measurements):
        inp,cap = self.reservations[key]
        if output_tokens is None:
            self.uncertain_tokens += inp+cap
            self.events.append(dict(kind='uncertain_interruption', reserved=inp+cap, actual_tokens=None))
        else:
            if type(output_tokens) is not int or not 0 <= output_tokens <= cap: raise Rejected('usage')
            if reasoning_tokens is not None and not 0 <= reasoning_tokens <= output_tokens: raise Rejected('reasoning_subset')
            self.actual_tokens += inp+output_tokens
            self.events.append(dict(kind='model_usage', input_tokens=inp, output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens, released=cap-output_tokens, **measurements))
        del self.reservations[key]

    def reserve_cpu(self, allowance):
        if allowance <= 0 or self.cpu_seconds+self.cpu_reserved+allowance > self.cpu_cap:
            raise Rejected('cpu_cap')
        self.cpu_reserved += allowance

    def reconcile_cpu(self, category, allowance, actual, **measurements):
        self.cpu_reserved -= allowance
        # Unknown child usage consumes the allowance conservatively, but remains unknown.
        self.cpu_seconds += allowance if actual is None else actual
        self.events.append(dict(kind='cpu', category=category, actual_cpu_seconds=actual,
            allowance=allowance, cap_debit=allowance if actual is None else actual, **measurements))
        if self.cpu_seconds > self.cpu_cap: raise Rejected('cpu_cap')

    def summary(self):
        return dict(profile=PROFILE, token_cap=self.token_cap, actual_tokens=self.actual_tokens,
            uncertain_tokens=self.uncertain_tokens, reserved_tokens=sum(a+b for a,b in self.reservations.values()),
            remaining_tokens=self.remaining, cpu_cap=self.cpu_cap, cpu_cap_debit=self.cpu_seconds,
            cpu_reserved=self.cpu_reserved, events=self.events,
            scope='task model/planner input+output; task compiler/decoder/tool/public-check CPU; terminal evaluator separate',
            overlap='child CPU and parent exclusive process CPU; device/wall are observations, not added to CPU',
            static_setup='separate, never reported as task tokens')

    def parent_overhead(self, category, started, event_index):
        """Account trusted orchestration outside nested measured operations.

        This is an observation at an operation boundary, not a subprocess limit.
        Child CPU is not subtracted from this process's clock.
        """
        accounted=sum(max(0,(e.get('actual_cpu_seconds') or 0)-(e.get('child_cpu_seconds') or 0))
                      for e in self.events[event_index:] if e['kind']=='cpu')
        elapsed=max(0,time.process_time()-started-accounted)
        self.reconcile_cpu(category,0,elapsed)
