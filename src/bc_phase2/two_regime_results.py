"""Obligation-level reporting for the two-regime experiment. CPU only."""
from fractions import Fraction
from . import two_regime as grid
from .joint_schema import require
from .model import digest


def session(row, components, grade):
    if not row or row.get('status')=='no_clean_snapshot':
        return dict(status='unrun',accuracy=None,correct=None,denominator=None,fully_correct=None)
    answers=[]
    for c in components:
        eid=c['namespace']+'_e'+c['outputs'][0][1:]
        item=row['store'].get(eid)
        sid=c['source_id']
        if item is None:
            outcome,origin=False,'missing'
        else:
            require(item['organisation']==row['organisation'],'foreign answer')
            outcome=grade(sid,item)
            origin='clean' if row['snapshot_role']=='initial' else 'regenerated' if eid in row['reconstruction'] else 'retained'
            require(origin!='regenerated' or item['invocation'] in row['invocations'],'stale reconstructed answer')
        answers.append(dict(source_id=sid,correct=outcome,origin=origin))
    resolved=all(a['correct'] is not None for a in answers)
    count=sum(a['correct'] is True for a in answers)
    return dict(status=row['status'],complete=row['complete'],answers=answers,known_correct=count,
                denominator=len(answers),correct=count if resolved else None,
                fully_correct=count==len(answers) if resolved else False if any(a['correct'] is False for a in answers) else None,
                accuracy=100*count/len(answers) if resolved else None,full_cost=row['full_cost'],
                attempted_spend=row['known_attempted_spend'])


def summarize(s,r,grade=lambda sid,item:None):
    w=s['wave']
    require(r['wave_id']==w['wave_id'] and len(r['conditions'])==1,'one frozen pair')
    c=r['conditions'][0]
    require(c['preprice_id']==w['bundles'][0]['preprice_id'],'cell binding')
    n=c['n']
    q=c['q']
    methods={}
    for name,m in c['methods'].items():
        clean=session(m.get('clean'),w['components'],grade)
        repairs=m.get('repairs',[])
        incidents=[session(repairs[i] if i<len(repairs) else None,w['components'],grade) for i in range(n)]
        complete=all(x['correct'] is not None for x in incidents)
        correct=sum(x['known_correct'] for x in incidents) if complete else None
        methods[name]=dict(clean=clean,incidents=incidents,repair_correct=correct,
                           repair_denominator=n*q if complete else None,repair_obligations=n*q,
                           repair_accuracy=100*correct/(n*q) if complete else None,
                           **{k:m.get(k) for k in ('status','full_cost_coverage','clean_calls','repair_calls',
                               'replay_sum','replay_mean','largest_observed_incident','shared_with')})
    slot=next(x for x in grid.frozen()['slots'] if x['id']==s['cell'])
    cert=c.get('certificate',{})
    totals=r['totals']
    planning=s['planning_overhead']
    return dict(cell=s['cell'],dataset=slot['dataset'],regime=slot['regime'],revision=slot['revision'],
                scope_digest=digest(s),wave_id=w['wave_id'],n=n,q=q,m=c['m'],K=2,status=c['status'],
                task_count=c['m'],operation_count=sum(len(comp['tasks']) for comp in w['components']),
                dependency_count=sum(len(t['parents']) for comp in w['components'] for t in comp['tasks']),
                alternate_kind='implementation' if any(len(comp['A_modes'])>1 for comp in w['components']) else None,
                encoded_axes=c.get('searched_axes'),alternative_review=w['alternative_review'],
                source_ids=c['source_ids'],available_axes=(['A'] if any(len(k['A_modes'])>1 for k in w['components']) else [])+(['B'] if c['m']>n else []),
                solver_status=cert.get('status'),primary_gap=cert.get('reported_primary_gap'),
                selected=c.get('designs'),changed=c.get('changed'),structure=c.get('execution_structure'),
                shared_observations=c.get('shared_observations'),methods=methods,
                paired_saving_pct=float(100*Fraction(c['paired_saving'])) if c.get('paired_saving') is not None else None,
                profile_calls=sum(len(x['invocations']) for x in r['profile_records']),
                failed_profile_calls=sum(len(x['invocations']) for x in r['profile_records'] if not x['complete']),
                profile_tokens=sum(x['known_attempted_spend'] for x in r['profile_records']),
                failed_profile_tokens=sum(x['known_attempted_spend'] for x in r['profile_records'] if not x['complete']),
                failed_evaluation_tokens=sum(row['known_attempted_spend'] for m in c['methods'].values()
                    if not m.get('shared_with') for row in [m.get('clean'),*m.get('repairs',[])]
                    if row and not row['complete']),
                stage_resources=r.get('stage_resources'),planning=planning,worker=totals,total_calls=totals['calls']+planning['calls'],
                total_tokens=totals['actual_tokens']+planning['actual_tokens'])


def pending():
    return {s['id']:dict(cell=s['id'],dataset=s['dataset'],revision=s['revision'],regime=s['regime'],
                         n=s['n'],K=2,target_m=s['target_m'],status='reserved_unrun')
            for s in grid.frozen()['slots']}


def table(rows):
    lines=['# Two-regime scaling results','','| Cell | Status | Questions | Tasks | Mean NEUTRAL repair tokens | Mean JOINT repair tokens | Saving |',
           '|---|---|---:|---:|---:|---:|---:|']
    for row in rows:
        m=row.get('methods',{})
        values=[row['cell'],row['status'],row.get('q'),row.get('m'),
                m.get('NEUTRAL',{}).get('replay_mean'),m.get('JOINT',{}).get('replay_mean'),row.get('paired_saving_pct')]
        lines.append('| '+' | '.join('—' if x is None else str(x) for x in values)+' |')
    lines+=['','Savings are percentages. Each owner incident starts from its own organisation’s clean snapshot.','',
            '| Dataset | Regime | Paired complete costs | Mean NEUTRAL | Mean JOINT | Mean paired saving | Matched clean and repair accuracy cells | NEUTRAL clean / repair % | JOINT clean / repair % | Cells offering A¹ |',
            '|---|---|---:|---:|---:|---:|---:|---|---|---:|']
    for ds in grid.LABELS:
        for regime in ('extra','equal'):
            group=[x for x in rows if x['dataset']==ds and x['regime']==regime]
            costs=[x for x in group if x.get('paired_saving_pct') is not None]
            quality=[x for x in group if x.get('methods') and all(v['clean']['accuracy'] is not None and
                     v['repair_accuracy'] is not None for v in x['methods'].values())]
            def avg(values):
                return f'{sum(values)/len(values):.2f}' if values else '—'
            names=('NEUTRAL','JOINT')
            means=[avg([float(Fraction(x['methods'][m]['replay_mean'])) for x in costs]) for m in names]
            accuracies=[avg([x['methods'][m]['clean']['accuracy'] for x in quality])+' / '+
                        avg([x['methods'][m]['repair_accuracy'] for x in quality]) for m in names]
            values=[ds,regime,f'{len(costs)}/{len(group)}',*means,avg([x['paired_saving_pct'] for x in costs]),
                    f'{len(quality)}/{len(group)}',*accuracies,sum('A' in x.get('available_axes',[]) for x in group)]
            lines.append('| '+' | '.join(map(str,values))+' |')
    lines+=['','| Dataset | Regime | Metric | Matched cells / planned | NEUTRAL % | JOINT % |',
            '|---|---|---|---:|---:|---:|']
    for ds in grid.LABELS:
        for regime in ('extra','equal'):
            group=[x for x in rows if x['dataset']==ds and x['regime']==regime]
            for metric in ('clean','repair'):
                def accuracy(method):
                    return method['clean']['accuracy'] if metric=='clean' else method['repair_accuracy']
                matched=[x for x in group if x.get('methods') and all(accuracy(m) is not None for m in x['methods'].values())]
                percentages=[f'{sum(accuracy(x["methods"][name]) for x in matched)/len(matched):.2f}' if matched else '—'
                             for name in ('NEUTRAL','JOINT')]
                lines.append('| '+' | '.join([ds,regime,metric,f'{len(matched)}/{len(group)}',*percentages])+' |')
    return '\n'.join(lines)+'\n\n¹ Among reported cells. Each cell has equal weight.\n'
