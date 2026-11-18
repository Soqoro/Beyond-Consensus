"""Price-free reservations and whole-component construction for two-regime scaling."""
from copy import deepcopy
from itertools import combinations
import sys
from pathlib import Path
import json

from . import composite_scaling as spec, prospective_pipeline as pipeline
from .joint_schema import require
from .model import Invalid, digest

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = 'two-regime-scaling-v1'
SEED = 'bc-two-regime-scaling-v1'
CONFIG = 'configs/phase2/two_regime_slots_v1.json'
LABELS = {'math500': 'math', 'medqa': 'medqa'}


def reserve():
    """Use the screened remainder of each prior release, including unused reserved IDs."""
    sources = {}
    pools = {}
    revisions = {}
    excluded = {}
    known_hashes = set()
    # The final AIME review also carries the identities of previous primary candidates.
    aime = json.loads((ROOT/'configs/phase2/prospective_aime2026_block2_source_review_v1.json').read_bytes())
    require(aime['review_bundle_digest']==digest({k:v for k,v in aime.items() if k!='review_bundle_digest'}),'exposure cutoff receipt')
    for row in aime['family_review']['prior_selected'] + [r for b in aime['cohort']['blocks'] for r in b['records']]:
        known_hashes.add(row['normalized_hash'])
    for dataset, label in LABELS.items():
        path = f'configs/phase2/prospective_{label}_block3_source_review_v1.json'
        review = json.loads((ROOT / path).read_bytes())
        require(review['review_bundle_digest'] == digest({
            k: v for k, v in review.items() if k != 'review_bundle_digest'}), 'historical receipt')
        cohort = review['cohort']
        known_hashes.update(r['normalized_hash'] for r in review['exposure']['records'] if r.get('normalized_hash'))
        revisions[dataset] = cohort['revision']
        sources[dataset] = review['review_bundle_digest']
        seen = set(review['family_review']['source_review_exposure_ids'])
        seen.update(r['source_id'] for b in cohort['blocks'] for r in b['records'])
        seen.update(r['source_id'] for r in cohort['excluded'])
        seen.update(r['source_id'] for r in review['exposure']['records'] if r['dataset'] == dataset)
        excluded[dataset] = sorted(seen)
        pools[dataset] = sorted(set(cohort['reserved_ids']) - seen, key=lambda sid: (
            digest([SEED, dataset, cohort['revision'], dataset + ':' + sid]), sid))
    # The pinned complete MATH inventory comparison found zero additional IDs in the
    # retained pool. Recheck each local public identity against both cohorts at binding.
    slots = []
    for n in (4, 6, 8, 2, 3, 5, 7):
        for regime in ('extra', 'equal'):
            target = (3*n+1)//2 if regime == 'extra' else n
            for ds in LABELS:
                size = max(8, target)
                slots.append(dict(id=f'{ds}-n{n}-{regime}', dataset=ds, n=n, K=2, regime=regime,
                                  target_m=target, revision=revisions[ds], candidates=pools[ds][:size]))
                del pools[ds][:size]
    return dict(campaign=CAMPAIGN, cutoff='through-job-1124341', historical_reviews=sources,
                historical_ids=excluded, known_historical_normalized_hashes=sorted(known_hashes),
                final_exposure_receipt=aime['review_bundle_digest'], seed=SEED, slots=slots,
                protocol=dict(methods=['NEUTRAL','JOINT'],K=2,objective='mean_first',C='direct_parent_artifacts',
                              review='one statement-grounded review per candidate; one optional selected-component pass',
                              alternate='one binary implementation choice with fixed typed parents and final obligations',
                              order='earliest feasible exact prefix; relaxed extra total only at exhaustion',
                              failed_profile='block frozen cell; no restart',interleaving=list(spec.METHODS),
                              sweep='own original clean, o0 through o(n-1), one sweep per exact design',
                              grades={'math500':'blinded final-answer judgments','medqa':'private exact option_label'}),

                procedures={ds:pipeline.procedure(ds)['procedure_digest'] for ds in LABELS},
                equal_fixed_policy='one shared clean and all-owner sweep', family_review='pending per candidate')


def frozen():
    value=json.loads((ROOT / CONFIG).read_bytes())
    require(digest(value)=='2957e85a50318ea745e69860936e3d6b112c13246b00b4d91ef65199a78d2b93','campaign reservations changed')
    return value


def mode_task(c,t,mode):
    require(mode in c['A_modes'],'admitted component configuration')
    value=deepcopy(t)
    if mode=='A1':
        value['responsibility']=c['alternative_procedures'][t['id']]
    return value


def descriptor(c,t,mode):
    baseline=dict(c,A_modes=['base'],reference_mode='base')
    d=pipeline.descriptor(baseline,t,'base')
    d.update(adapter=CAMPAIGN,task=mode_task(c,t,mode),ancestor_mode=mode,
             procedures={x['id']:mode_task(c,x,mode)['responsibility'] for x in c['tasks']})
    return d


def key(c,t,mode):
    return digest(descriptor(c,t,mode))


def coverage(cs):
    return [dict(key=key(c,t,a),descriptor=descriptor(c,t,a),component=c['namespace'],
                 source_id=c['source_id'],task=t['id'],mode=a) for c in cs for a in c['A_modes'] for t in c['tasks']]


def domain(cs,n,prices=None):
    """Compile the existing base domain and encode one complete component choice."""
    d=spec.domain([dict(c,A_modes=['base'],reference_mode='base') for c in cs],n)
    if prices is not None:
        d['unit']='profile_input_plus_generated_tokens'
    tasks={t['id']:t for t in d['tasks']}
    events={e['host']:e for e in d['events']}
    for c in cs:
        choice=c['namespace']+'_proof'
        if len(c['A_modes'])>1:
            require(c['A_modes']==['A0','A1'] and not d['choices'],'one binary mode')
            d['choices'].append(dict(id=choice,axis='A',options=c['A_modes']))
        for t in c['tasks']:
            tid=c['namespace']+'_'+t['id']
            event=events[tid]
            variant=tasks[tid]['variants'][0]
            base_mode=event['modes'][0]
            tasks[tid]['variants']=[]
            event['modes']=[]
            for mode in c['A_modes']:
                when={choice:mode} if mode!='base' else {}
                cost=prices[key(c,t,mode)] if prices is not None else 1
                require(type(cost) is int and cost>0,'complete profile price')
                tasks[tid]['variants'].append(dict(variant,id=mode,when=when))
                event['modes'].append(dict(base_mode,id=mode,when=when,initial=str(cost),replay=str(cost)))
    return spec.canonical_domain(d)


def worker_request(c,t,mode,sources,parents):
    baseline=dict(c,A_modes=['base'],reference_mode='base')
    original=next(x for x in c['tasks'] if x['id']==t['id'])
    req=pipeline.worker_request(baseline,original,sources,parents)
    chosen=mode_task(c,original,mode)
    require(all(t[k]==v for k,v in chosen.items()),'selected worker instruction and parent contract')
    req['payload']['responsibility']=chosen['responsibility']
    req['payload_digest']=digest(req['payload'])
    return req


class Engine(pipeline.Engine):
    def task_for_operation(self,op):
        ns,tid=op.host.split('_',1)
        c=self.components[ns]
        selected=mode_task(c,next(t for t in c['tasks'] if t['id']==tid),op.mode)
        return dict(selected,_component=ns,_proof=op.mode)

    def make_request(self,t,store):
        c=self.components[t['_component']]
        parents={p:json.loads(store[c['namespace']+'_e'+p[1:]].value) for p in t['parents']}
        return worker_request(c,t,t['_proof'],self.sources,parents)


check_profile=pipeline.check_profile


def run_wave(journal,sources,out,w,solver=None):
    require(w['wave_id']==digest({k:v for k,v in w.items() if k!='wave_id'}),'frozen pair')
    return pipeline.runtime.run_wave(journal,sources,out,w,solver,interface=sys.modules[__name__])


def neutral(components, n):
    compiled = domain(components, n)
    baseline = sorted([dict(source_id=c['source_id'], tasks=c['tasks'], outputs=c['outputs'])
                       for c in components], key=lambda row: row['source_id'])
    seed = digest([SEED, baseline, n, 2])
    # Shuffle canonical task identities. Bind implementation-specific names only afterwards.
    labels = {(c['source_id'], t['id']): c['namespace']+'_'+t['id']
              for c in components for t in c['tasks']}
    ranked = sorted(labels, key=lambda label: (digest([seed, *label]), label))
    pairs = len(ranked)-n
    groups = [ranked[2*i:2*i+2] for i in range(pairs)] + [[t] for t in ranked[2*pairs:]]
    ownership = {labels[t]:f'o{i}' for i, group in enumerate(sorted(sorted(g) for g in groups)) for t in group}
    choices = {c['namespace']+'_proof':c['reference_mode'] for c in components if len(c['A_modes']) > 1}
    require(len(choices) <= 1, 'one binary component choice')
    for mode in ([None] if not choices else ['A0', 'A1']):
        a = dict.fromkeys(choices, mode)
        spec.compile_organisation(compiled, spec.explicit_selection(compiled, a, {}, ownership))
    structure = digest(spec.structural(compiled))
    return dict(neutral=dict(A=choices,C={},ownership=ownership), neutral_seed=seed,
                preprice_id=digest([CAMPAIGN, structure, seed, ownership]), domain_structure_id=structure,
                q=len(components), m=len(ranked), n=n, K=2)


def select(slot, dispositions):
    """Reproduce the earliest feasible prefix even when replaying a completed intake."""
    ids = slot['candidates']
    require(list(dispositions) == ids[:len(dispositions)], 'contiguous prefix in source rank order')
    admitted = []
    for index, (sid, outcome) in enumerate(dispositions.items()):
        status = outcome['status']
        require(status in ('admitted','outside_capacity','blocked','invalid','unsupported','review_unresolved'), 'review status')
        if status == 'admitted':
            c = outcome['component']
            require(c['source_id'] == sid and c['dataset'] == slot['dataset'] and c['A_modes']==['base'], 'original source contract')
            spec.validate_component(c)
            admitted.append((index,c))
        exhausted = index+1 == len(ids)
        candidates = []
        for q in range(2,len(admitted)+1):
            for subset in combinations(admitted,q):
                m = sum(len(c['tasks']) for _,c in subset)
                exact = m == slot['target_m']
                if exact or (exhausted and slot['regime']=='extra' and slot['n'] < m <= 2*slot['n']):
                    candidates.append((abs(m-slot['target_m']), m, tuple(i for i,_ in subset), [c for _,c in subset]))
        for _,_,_,cs in sorted(candidates):
            try:
                b = neutral(cs, slot['n'])
            except TimeoutError:
                return dict(status='construction_unresolved')
            except Invalid:
                continue
            require(index+1 == len(dispositions), 'intake continued after first feasible prefix')
            return dict(status='bundle_frozen', components=cs, sources=[c['source_id'] for c in cs], **b)
    if len(dispositions)==len(ids):
        return dict(status='construction_gap')
    return dict(status='next_candidate',source_id=ids[len(dispositions)])


def wave(slot, selected, alternatives):
    """One bounded review of selected components in rank order; profile the entire domain."""
    cs = deepcopy(selected['components'])
    used = []
    for c in cs:
        require(len(used)<len(alternatives),'selected component requires one alternative review')
        review = alternatives[len(used)]
        require(review['source_id']==c['source_id'] and review['rationale'].strip() and review['reviewer'].strip(),
                'ordered alternative review')
        used.append(review)
        if review['decision']=='outside_domain':
            continue
        require(review['decision']=='admit_procedure' and review['provenance'] in ('planner-proposed','reviewer-authored')
                and review['preserves_responsibilities'] is True and review['solution_free'] is True,
                'supported, reviewed implementation alternative')
        procedures=review['procedures']
        original={t['id']:t['responsibility'] for t in c['tasks']}
        require(procedures.keys()==original.keys() and procedures!=original
                and all(isinstance(v,str) and v.strip() for v in procedures.values()),'complete A1 configuration')
        c.update(A_modes=['A0','A1'], reference_mode='A0', alternative_procedures=procedures)
        break
    require(used==alternatives, 'end review at first supported alternative')
    b=neutral(cs,slot['n'])
    require(b['neutral_seed']==selected['neutral_seed'], 'A0 ownership seed changed')
    b.update(components=cs,sources=selected['sources'],call_bounds=spec.call_bounds(selected['components'],slot['n']),slot=1)
    entries=coverage(cs)
    b['preprice_id']=digest([b['preprice_id'],entries])
    schedule=pipeline.runtime.schedule_profiles(cs,{})
    calls=b['call_bounds']['evaluation_calls']+sum(s['calls'] for s in schedule)
    w=dict(condition=CAMPAIGN,cell=slot['id'],alternative_review=used,components=cs,bundles=[b],
           profile_coverage=entries,profile_schedule=schedule,reused_profiles={},
           profile_consumers={e['key']:[b['preprice_id']] for e in entries},planned_slots=1,
           matrix=[dict(n=slot['n'],slot=1,status='supported_frozen')],
           limits=dict(pipeline.LIMITS,maximum_calls=calls,token_cap=calls*16384,wall_seconds=14400),
           execution_allowed=False)
    w['wave_id']=digest(w)
    return w
