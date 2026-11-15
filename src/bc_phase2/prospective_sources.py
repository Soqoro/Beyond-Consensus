"""Source-disjoint fixed-block preparation. Offline, public-only, no dispatch."""
from copy import deepcopy
from itertools import combinations
import hashlib
import re
from .model import digest, Invalid
from .joint_schema import require
from . import composite_scaling as spec

SEED = 'bc-prospective-source-disjoint-v1'
SIZES = {'math500': (24, 8), 'medqa': (24, 8), 'aime2025': (12, 6),
         'aime2026': (12, 6), 'gpqa': (6, 6)}
ORDER = tuple(SIZES)

def text_hash(text):
    require(type(text) is str and bool(text.strip()), 'nonempty source text')
    return hashlib.sha256(text.encode('utf8')).hexdigest()

def faithful_identity(public):
    """Ignore record IDs and option order; never remove numbers/operators/case."""
    require(type(public) is dict, 'public object')
    if set(public) == {'id', 'problem'}:
        content = [public['problem']]
    else:
        require(set(public) == {'id', 'question', 'options'}, 'public allowlist')
        require(set(public['options']) == set('ABCD'), 'four labels')
        content = [public['question'], sorted(public['options'].values())]
    def normal(x):
        if type(x) is list: return [normal(v) for v in x]
        require(type(x) is str and bool(x.strip()), 'nonempty text')
        return ' '.join(x.split())  # whitespace only; no Unicode/math rewrite
    normalized=normal(content)
    if 'options' in public:normalized[1]=sorted(normalized[1])
    return digest(content), digest(normalized)

def freeze(records, dataset, revision, exposure, procedure, family_review):
    """Input records are metadata, not statements or keys. Never auto-refill a slot."""
    require(dataset in SIZES and type(revision) is str and revision, 'dataset binding')
    require(exposure.get('cutoff') and procedure.get('procedure_digest') ==
            digest({k:v for k,v in procedure.items() if k != 'procedure_digest'}), 'frozen policy')
    require(family_review.get('dataset') == dataset and family_review.get('revision') == revision,
            'family review dataset binding')
    require(family_review.get('inventory_digest') == digest(records), 'review inventory binding')
    require(family_review.get('reviewer') and family_review.get('reviewed_at'), 'review provenance')
    require(len(records) <= 10000, 'bounded source inventory')
    keys = {'source_id', 'canonical_id', 'exact_hash', 'normalized_hash', 'family_id', 'status'}
    require(all(set(r) == keys and all(type(r[k]) is str for k in keys) for r in records), 'metadata allowlist')
    require(len({r['source_id'] for r in records}) == len(records), 'duplicate record ID')
    for r in records:
        require(all(re.fullmatch('[0-9a-f]{64}', r[k]) for k in ('exact_hash','normalized_hash')), 'text identities')
        require(r['source_id'] and r['canonical_id'] and r['status'] in ('eligible','blocked'), 'source status')
    excluded = set()
    for r in exposure['records']:
        if r['dataset'] == dataset and r['phase'] in ('historical','qualification'):
            excluded.add(r['source_id'])
    historical = [r for r in exposure['records'] if r['phase'] in ('historical','qualification')]
    prior = family_review.get('prior_selected', [])
    # Earlier cohorts must be supplied in the fixed dataset order, not job order.
    require(all(ORDER.index(r['dataset']) < ORDER.index(dataset) for r in prior), 'cross-cohort priority')
    identities = {k:{r[k] for r in historical + prior if r.get(k)}
                  for k in ('canonical_id','exact_hash','normalized_hash','family_id')}
    aliases = {tuple(a) for a in exposure.get('aliases', [])}
    decisions = family_review.get('decisions', {})
    ranked = sorted(records, key=lambda r:(digest([SEED,dataset,revision,r['canonical_id']]),r['source_id']))
    pool=[]; rejected=[]
    for r in ranked:
        reasons=[]
        if r['source_id'] in excluded: reasons.append('historical_record')
        if any(r[k] and r[k] in identities[k] for k in identities): reasons.append('duplicate_or_family')
        if any((dataset,r['source_id'],h['dataset'],h['source_id']) in aliases or
               (h['dataset'],h['source_id'],dataset,r['source_id']) in aliases for h in historical):
            reasons.append('historical_alias')
        if reasons:
            rejected.append(dict(r,reasons=reasons));continue
        # Unresolved selected records occupy their frozen slots. No replacement.
        disposition=decisions.get(r['source_id'],'pending')
        require(disposition in ('clear','pending','conflict'), 'family decision')
        pool.append(dict(r,status='eligible' if r['status']=='eligible' and disposition=='clear' else 'blocked',
                         family_review=disposition))
        for k in identities:
            if r[k]:identities[k].add(r[k])
    ceiling,size=SIZES[dataset];selected=pool[:ceiling]
    blocks=[dict(slot=i+1,records=selected[i*size:(i+1)*size],status='frozen_pending_planning',
                 composite=None) for i in range((ceiling+size-1)//size)]
    out=dict(schema=SEED,dataset=dataset,revision=revision,exposure_digest=digest(exposure),
             procedure_digest=procedure['procedure_digest'],inventory_digest=digest(records),
             family_review_digest=digest(family_review),blocks=blocks,excluded=rejected,
             reserved_ids=[r['source_id'] for r in pool[ceiling:]],execution_allowed=False,
             limitations=['project source separation only; no pretraining or independence claim'])
    out['cohort_digest']=digest(out);return out

def select_block(cohort, slot, dispositions, feasibility=spec.neutral):
    require(cohort['cohort_digest']==digest({k:v for k,v in cohort.items() if k!='cohort_digest'}), 'cohort integrity')
    block=next(b for b in cohort['blocks'] if b['slot']==slot)
    ids=[r['source_id'] for r in block['records']]
    require(set(dispositions)==set(ids), 'all fixed block dispositions; no cross-block refill')
    allowed=('admitted','unsupported','invalid','unrun','blocked','outside_capacity','pending')
    require(all(d['status'] in allowed for d in dispositions.values()), 'disposition vocabulary')
    if any(d['status']=='pending' for d in dispositions.values()):
        return dict(status='pending_block_review',slot=slot,bundle=None)
    cs=[]
    for r in block['records']:
        d=dispositions[r['source_id']]
        if d['status']!='admitted':continue
        require(r['status']=='eligible', 'blocked source cannot be admitted')
        c=d['component'];spec.validate_component(c)
        require(c['source_id']==r['source_id'], 'component source')
        require(c.get('prospective_cohort')==cohort['cohort_digest'], 'current recipe plan only')
        cs.append(c)
    candidates=[]
    for q in range(2,len(cs)+1):
        for subset in combinations(cs,q):
            m=sum(len(c['tasks']) for c in subset)
            if 5<=m<=8:candidates.append((abs(m-6),m,tuple(ids.index(c['source_id']) for c in subset),subset))
    rejected=[]
    for _,_,_,subset in sorted(candidates,key=lambda x:x[:3]):
        try:b=feasibility(list(subset),4)
        except TimeoutError:
            return dict(status='unresolved_feasibility',slot=slot,bundle=None,rejected=rejected)
        except Invalid as e:
            rejected.append(dict(sources=[c['source_id'] for c in subset],reason=str(e)));continue
        b.update(slot=slot,status='supported_frozen',components=list(subset),sources=[c['source_id'] for c in subset],
                 call_bounds=spec.call_bounds(list(subset),4))
        return dict(status='supported_frozen',slot=slot,bundle=b,rejected=rejected,
                    dispositions=deepcopy(dispositions),cohort_digest=cohort['cohort_digest'])
    return dict(status='no_supported_bundle',slot=slot,bundle=None,rejected=rejected,dispositions=deepcopy(dispositions))
