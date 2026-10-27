#!/usr/bin/env python3
"""Bounded offline exactness/binding/timing report. No model execution."""
import argparse,hashlib,json,platform,sys,time,socket
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from bc_phase2.model import Workflow,Task,fixture,plain,Invalid,digest
from bc_phase2.allocation import solve,reference
from bc_phase2.runtime import Executor,Budget,execute,corrupt_and_restore
from bc_phase2.model import Allocation


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=Path(args.output);out.mkdir(exist_ok=False)
    start=time.monotonic();cpu=time.process_time()
    def blocked(*a,**k):raise RuntimeError('network disabled for offline verification')
    socket.socket.connect=blocked;socket.create_connection=blocked
    report={'kind':'synthetic_CPU_mock_only','model_executed':False,'source_bindings':[],'unbound':[], 'timings':[], 'synthetic_comparisons':0,'source_bound_comparisons':0}
    def check_limit():
        if time.monotonic()-start>120:raise RuntimeError('bounded verification elapsed limit')
    try:
        import networkx as nx
        report['dependencies']={'python':platform.python_version(),'networkx':nx.__version__,'matching_module':str(Path(nx.__file__).resolve())}
        # Genuine matching n4..10, one sparse synthetic chain at m=n+1 and m=2n.
        for n in range(4,11):
            for m in (n+1,2*n):
                for objective in ('mean','worst'):
                    check_limit();w=fixture(m,source=f'timing:{n}:{m}');costs={t.id:f'{i+1}/7' for i,t in enumerate(w.tasks)}
                    v=solve(w,n,costs,objective)
                    report['timings'].append({'n':n,'m':m,'objective':objective,'status':v['status'],
                        'sum':v['sum'],'max':v['max'],'preprocessing_cpu_seconds':v['preprocessing_cpu_seconds'],
                        'solve_cpu_seconds':v['solve_cpu_seconds'],'matching_calls':v['matching_calls']})
        for m in range(2,9):
            w=fixture(m);costs={t.id:str(t.synthetic_cost) for t in w.tasks}
            for n in range((m+1)//2,m+1):
                for objective in ('mean','worst'):
                    check_limit();v=solve(w,n,costs,objective);ref=reference(w,n,costs,objective)
                    pair=(v['sum'],v['max']) if objective=='mean' else (v['max'],v['sum'])
                    if pair!=ref['pair']:raise AssertionError('independent oracle disagreement')
                    report['synthetic_comparisons']+=1
        root=ROOT/'outputs/phase1-exhaustive-v2-bootstrap-2026-10-23'
        cp=root/'small-release-final-01/certificate.json';qp=root/'small-release-01/queries.json'
        if not cp.exists() or not qp.exists():report['unbound'].append('Phase I raw query/certificate missing')
        else:
            cert=json.loads(cp.read_text());raw=qp.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=cert['evidence_sha256']['small-release-01/queries.json']:raise Invalid('historical query hash changed')
            release_raw=(root/'small-release-01/results.json').read_bytes()
            if hashlib.sha256(release_raw).hexdigest()!=cert['evidence_sha256']['small-release-01/results.json']:raise Invalid('historical release hash changed')
            report['expected_input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (cp,qp,root/'small-release-01/results.json')}
            queries=json.loads(raw);release=json.loads(release_raw)
            manifests={}
            for path in sorted((root/'integrated-topfive-01').glob('slice-*/manifest.json')):
                value=json.loads(path.read_text());manifests[value['manifest_id']]=(path,value)
            for q in queries:
                if q['dimension']!='B' or q['query']['cap']!=2:continue
                check_limit();bound=manifests.get(q['manifest_id'])
                if bound is None:report['unbound'].append(q['manifest_id']);continue
                path,m=bound;sha=hashlib.sha256(path.read_bytes()).hexdigest()
                if sha!=release['input_sha256'][str(path.relative_to(root))]:raise Invalid('raw graph binding changed')
                inputs=m['input'];tasks=tuple(Task(str(i),tuple(str(a) for a,b in inputs['edges'] if b==i)) for i in range(2*m['n']))
                w=Workflow('phase1:'+m['manifest_id'],tasks,tuple(map(str,inputs['outputs'])))
                costs={str(i):v for i,v in enumerate(m['prices'])}
                condition=digest({'n':m['n'],'edges':sorted(inputs['edges']),'outputs':sorted(inputs['outputs']),'prices':m['prices']})
                expected=q['ranking']['best']
                result=solve(w,m['n'],costs,q['query']['objective'])
                metric=[result['sum'],result['max']] if q['query']['objective']=='mean' else [result['max'],result['sum']]
                if metric!=expected:raise AssertionError('source-bound K2 metric disagreement')
                report['source_bound_comparisons']+=1
                report['source_bindings'].append({'query_id':q['query_id'],'manifest':str(path.relative_to(ROOT)),
                        'manifest_sha256':sha,'query_file_sha256':hashlib.sha256(raw).hexdigest(),
                        'n':m['n'],'workload':m['workload'],'map':m['map'],'objective':q['query']['objective'],
                        'graph_cost_condition':condition,'ordering':'sum,max' if q['query']['objective']=='mean' else 'max,sum',
                        'expected_pair':expected,'observed_pair':metric,'metric_pair':metric,'status':'passed'})
            report['source_binding_counts']={'objective_rows':len(report['source_bindings']),
                'manifest_slices':len({v['manifest'] for v in report['source_bindings']}),
                'distinct_labelled_graph_cost_conditions':len({v['graph_cost_condition'] for v in report['source_bindings']}),
                'note':'labelled raw edges/output/cost identities; aliases are not independent cases, no isomorphism quotient'}
        # Concrete taint and aborted-completion report, separate from worker experiment.
        w=Workflow('synthetic:aborted-corruption',tuple(Task(f't{i}') for i in range(4)),tuple(f't{i}' for i in range(4)))
        e=Executor();a=Allocation(w.key,2,(('t0','t1'),('t2','t3')),'supplied','fixed-control',0)
        clean=execute(w,e,0,Budget(100));report['corruption_abort_control']=corrupt_and_restore(w,e,0,Budget(100),clean,a,('t0','t1'),abort_after=1)
        report['status']='passed'
    except Exception as exc:
        report['status']='failed';report['error']={'type':type(exc).__name__,'message':str(exc)}
    report['wall_seconds']=time.monotonic()-start;report['cpu_seconds']=time.process_time()-cpu
    report['implementation_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/bc_phase2').glob('*.py'))}
    (out/'results.json').write_text(json.dumps(plain(report),indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k in ('status','error','synthetic_comparisons','source_bound_comparisons','unbound','wall_seconds')},indent=2))
    return report['status']!='passed'
if __name__=='__main__':raise SystemExit(main())
