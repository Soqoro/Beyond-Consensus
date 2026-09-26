"""Read-only resolution from an actual successful manifest and verified snapshot."""
import ast
from pathlib import Path
from ..util import BCError, read_json, digest, file_hash
from .snapshot import verify_snapshot
from reporecourse.experiments import validate


def resolve(run, snapshot):
    run=Path(run);snapshot=Path(snapshot)
    m=read_json(run/'manifest.json');validate(m)
    marker=verify_snapshot(snapshot)
    if (read_json(snapshot/'resolved/manifest.json')!=m or marker['manifest_hash']!=digest(m)
        or marker['source_revision']!=m['source_revision'] or len(m['episodes'])!=1):
        raise BCError('Historical snapshot/manifest mismatch')
    e=m['episodes'][0];r=read_json(run/'episodes'/e['episode_id']/'result.json')
    if (r.get('experiment_id')!=m['experiment_id'] or r.get('episode_id')!=e['episode_id']
        or r.get('provenance')!={'manifest_hash':digest(e)} or r.get('success') is not True
        or r.get('status')!='completed' or r.get('plan')!=e['plan']):
        raise BCError('Require the actual successful clean result and bindings')
    required={'customer_summary','method_summary'}
    state=r.get('state',{});bound=state.get('bound',{})
    if set(bound)!=required or set(r.get('evaluation',{}).get('obligations',{}))!=required or not all(r['evaluation']['obligations'].values()):
        raise BCError('Historical complete evaluated bindings required')
    for name,owner in [('customer_summary','w0'),('method_summary','w1')]:
        if state.get('artifacts',{}).get(bound[name],{}).get('author')!=owner:
            raise BCError('Historical primary ownership mismatch')
    # Old manifests did not serialize the Engine action limit. Resolve the
    # literal default from the verified implementation and reject overrides.
    engine=snapshot/'src/reporecourse/engine.py'
    tree=ast.parse(engine.read_text())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Engine')
    init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    defaults=dict(zip([a.arg for a in init.args.kwonlyargs],init.args.kw_defaults))
    actions=ast.literal_eval(defaults['max_actions'])
    adapter=snapshot/'src/beyond_consensus/experiments/reporecourse.py'
    calls=[n for n in ast.walk(ast.parse(adapter.read_text())) if isinstance(n,ast.Call)
           and isinstance(n.func,ast.Name) and n.func.id=='Engine']
    if len(calls)!=1 or any(k.arg in (None,'max_actions') for k in calls[0].keywords):
        raise BCError('Historical Engine action settings need explicit audit; refusing inference')
    if 'max_actions' in m and m['max_actions']!=actions:raise BCError('Historical action setting mismatch')
    return dict(manifest=m,manifest_hash=digest(m),snapshot_hash=digest(marker),result_hash=digest(r),
                max_actions=actions,action_resolution='verified literal Engine default; adapter supplies no override',
                implementation_hashes={str(p.relative_to(snapshot)):file_hash(p) for p in (engine,adapter)},
                historical_bound_versions=bound)
