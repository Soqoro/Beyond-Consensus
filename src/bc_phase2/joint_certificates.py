"""Exact conservative reporting, separate from solver Boolean variables."""
from fractions import Fraction
from copy import deepcopy
import math
from .joint_core import compile_organisation,evaluate
from .joint_schema import canonical_domain,price,require
from .model import digest,Invalid


def safe_api_lower(value,scale):
    # Step a full representable double downward before flooring: subtracting one
    # integer is insufficient above 2**53. Zero-gap proof is handled separately.
    require(type(value) in (int,float) and math.isfinite(value),'finite API bound')
    return Fraction(max(0,math.floor(math.nextafter(float(value),-math.inf))),scale)


def certified_status(status,absolute_gap,relative_gap,validated,coverage=True):
    return status=='OPTIMAL' and absolute_gap==0 and relative_gap==0 and validated and coverage


def covering_bound(root,incumbent,regions,coverage):
    require(root>=0 and (incumbent is None or root<=incumbent),'root lower bound exceeds incumbent')
    if not coverage:return root
    if not regions:return root  # No search partition proof supplied, no closure inferred.
    require(all(isinstance(v,(int,Fraction)) and v>=0 for v in regions),'exact region bounds')
    union=min(regions)
    if incumbent is not None:union=min(incumbent,union)
    result=max(root,union)
    require(incumbent is None or result<=incumbent,'lower bound exceeds incumbent')
    return result


def envelope(execution,record=None):
    if record is None:return {'status':'ENCODED_CERTIFICATE_ONLY','target_cost_guarantee':False}
    require(type(record) is dict and set(record)=={'domain','organisation','provenance','scope','same_recovery_sets','errors'},'envelope fields')
    require(record['domain']==execution.domain_id and record['organisation']==execution.organisation_id,'envelope binding')
    require(type(record['provenance']) is str and record['provenance'].strip(),'labelled envelope provenance')
    require(record['scope'] in ('single_design','two_design','simultaneous_domain'),'explicit envelope scope')
    require(record['same_recovery_sets'] is True,'structural mismatch not covered')
    require(set(record['errors'])=={o.id for o in execution.operations},'complete event envelopes')
    errors={k:price(v,zero=True) for k,v in record['errors'].items()};score=evaluate(execution)
    E=tuple(sum((errors[v] for v in vs),Fraction()) for vs in score['recovery_sets'])
    return {'status':'SUPPLIED_ENVELOPE_ARITHMETIC','E':E,'mean':sum(E,Fraction())/execution.n,'worst':max(E),
            'scope':record['scope'],'provenance':record['provenance'],
            'domain_wide_coverage_verified':False,'target_cost_guarantee':False}


class Ledger:
    def __init__(self,domain,seed=None,provenance='caller supplied neutral seed'):
        self.domain=canonical_domain(domain);self.binding=digest(self.domain)
        self.candidate=None;self.score=None;self.lower=Fraction();self.events=[]
        if seed is not None:self.offer(seed,provenance)
    def offer(self,candidate,provenance):
        score=evaluate(compile_organisation(self.domain,candidate))
        if self.lower>score['objective_pair'][0]:raise Invalid('lower bound exceeds independently checked incumbent')
        better=self.score is None or score['objective_pair']<self.score['objective_pair']
        if better:self.candidate=deepcopy(candidate);self.score=deepcopy(score)
        self.events.append({'kind':'candidate','provenance':provenance,'accepted':better,'pair':score['objective_pair']})
        return better
    def bound(self,value,provenance,full_domain=True):
        require(full_domain,'conditional/neighborhood bound is not a global bound')
        require(isinstance(value,(int,Fraction)) and value>=0,'exact nonnegative bound')
        require(self.score is None or value<=self.score['objective_pair'][0],'lower bound exceeds incumbent')
        self.lower=max(self.lower,value);self.events.append({'kind':'bound','value':value,'provenance':provenance})
    def report(self):
        factor=self.domain['n'] if self.domain['objective']=='mean_first' else 1
        upper=None if self.score is None else self.score['objective_pair'][0]
        return {'domain':self.binding,'unit':self.domain['unit'],'objective':self.domain['objective'],
            'candidate':self.candidate,'score':self.score,'lower':self.lower,'upper':upper,
            'reported_primary_lower':self.lower/factor,'reported_primary_upper':None if upper is None else upper/factor,
            'reported_primary_gap':None if upper is None else (upper-self.lower)/factor,
            'events':self.events,'certificate':'ENCODED_CERTIFICATE_ONLY','target_cost_guarantee':False}
