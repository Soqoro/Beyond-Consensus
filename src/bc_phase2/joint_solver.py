"""Guarded CP-SAT two-stage joint optimisation. No enumeration fallback."""
import time
from fractions import Fraction
from .joint_constraints import build,decode_solution,input_bits
from .joint_bounds import checked_partial,mandatory_bound
from .joint_certificates import Ledger,certified_status,safe_api_lower
from .joint_schema import canonical_domain,require
from .model import Invalid,digest


def solve(domain,seed=None,seconds=5.0,threads=1,random_seed=0,partial=None,
          use_bounds=True,absolute_gap=0.0,relative_gap=0.0):
    import math
    require(type(seconds) in (int,float) and math.isfinite(seconds) and 0<=seconds<=3600,'bounded offline seconds')
    require(type(threads) is int and 1<=threads<=4,'thread limit')
    require(type(random_seed) is int and 0<=random_seed<2**31,'solver seed')
    for gap in (absolute_gap,relative_gap):require(type(gap) in (int,float) and math.isfinite(gap) and gap>=0,'gap parameter')
    start=time.monotonic();cpu=time.process_time();d=canonical_domain(domain);p=checked_partial(d,partial)
    ledger=Ledger(d,seed)
    if seed is not None:
        for axis,key in (('A','A'),('C','C'),('P','ownership')):
            require(all(seed[key].get(k)==v for k,v in p[axis].items()),'common seed outside declared fixed-block restriction')
    root=mandatory_bound(d)
    if use_bounds:ledger.bound(root['sum' if d['objective']=='mean_first' else 'worst'],'forced exposure root')
    full=not any(p.values());stages=[];primary=None;secondary=False;status='UNRESOLVED'
    config={'seconds':seconds,'threads':threads,'random_seed':random_seed,'absolute_gap':absolute_gap,'relative_gap':relative_gap,'use_bounds':use_bounds,'partial':p}
    for phase in ('primary','secondary'):
        remaining=seconds-(time.monotonic()-start)
        if remaining<=0:status='TIME_LIMIT';break
        compile_start=time.monotonic()
        encoded=build(d,p,use_bounds)
        try:cp,model,variables=encoded['circuit'].cpsat()
        except Invalid as exc:
            if 'SOLVER_DEPENDENCY_BLOCKED' not in str(exc):raise
            status='SOLVER_DEPENDENCY_BLOCKED';stages.append({'phase':phase,'status':status,'reason':str(exc)});break
        first,second=(encoded['S'],encoded['W']) if d['objective']=='mean_first' else (encoded['W'],encoded['S'])
        if phase=='secondary':
            # Fresh original model; no strict incumbent cut or primary search exclusions.
            model.Add(variables[first]==int(primary*encoded['scale']))
        model.Minimize(variables[first if phase=='primary' else second])
        if ledger.candidate is not None:
            s=ledger.candidate;bits=input_bits(encoded,s['A'],s['C'],s['ownership'])
            feasible,_=encoded['circuit'].evaluate(bits)
            if feasible:
                for key,node in encoded['circuit'].inputs.items():model.AddHint(variables[node],bits[key])
        solver=cp.CpSolver();solver.parameters.num_search_workers=threads;solver.parameters.random_seed=random_seed
        solver.parameters.absolute_gap_limit=absolute_gap;solver.parameters.relative_gap_limit=relative_gap
        remaining=seconds-(time.monotonic()-start)
        if remaining<=0:status='TIME_LIMIT';break
        solver.parameters.max_time_in_seconds=remaining
        compilation=time.monotonic()-compile_start;solve_start=time.monotonic();code=solver.Solve(model);name=solver.StatusName(code)
        stage={'phase':phase,'status':name,'compilation_wall_seconds':compilation,'solve_wall_seconds':time.monotonic()-solve_start,
               'restored_original_domain':True,'coverage':'full declared restriction','validated':False}
        if code in (cp.OPTIMAL,cp.FEASIBLE):
            values=[solver.Value(v) for v in variables];candidate,score=decode_solution(encoded,values)
            ledger.offer(candidate,'CP-SAT '+phase+' independently decoded')
            stage.update(validated=True,pair=score['objective_pair'],vector=score['vector'],groups=score['groups'])
            proved=certified_status(name,absolute_gap,relative_gap,True)
            lb=safe_api_lower(solver.BestObjectiveBound(),encoded['scale']);stage['outward_lower']=lb
            if phase=='primary':
                if proved:primary=score['objective_pair'][0];lb=primary
                if full:ledger.bound(lb,'CP-SAT full-domain primary '+('zero-gap proof' if proved else 'conservative float API bound'))
                if not proved:status='PRIMARY_UNCERTIFIED';stages.append(stage);break
            else:
                secondary=proved;status='LEX_OPTIMAL' if proved else 'PRIMARY_CERTIFIED_SECONDARY_UNRESOLVED'
        elif code==cp.INFEASIBLE:
            if phase=='primary' and (ledger.candidate is None or not full):status='PROVEN_INFEASIBLE_RESTRICTION' if not full else 'PROVEN_INFEASIBLE'
            else:raise Invalid('infeasible backend conflicts with retained feasible evidence')
            stages.append(stage);break
        else:
            status='PRIMARY_CERTIFIED_SECONDARY_UNRESOLVED' if primary is not None else 'UNRESOLVED'
            stages.append(stage);break
        stages.append(stage)
    report=ledger.report();report.update(status=status,configuration=config,stages=stages,
        certificate_binding=digest({'domain':ledger.binding,'configuration':config,'incumbent':ledger.candidate,'objective':d['objective'],'unit':d['unit']}),
        primary_certified=primary is not None,lexicographic_certified=secondary,
        certificate_scope='full domain' if full else 'explicit fixed-block restriction only',
        wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
        model_executed=False,production_backend='OR-Tools CP-SAT',historical_binding='SOURCE_BINDING_UNAVAILABLE')
    return report
