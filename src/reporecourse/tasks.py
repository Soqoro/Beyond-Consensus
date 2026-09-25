"""Frozen public task cards and separately loaded evaluator packages."""
from copy import deepcopy
from pathlib import Path
from .common import Rejected, digest, file_hash, load

ROOT=Path(__file__).resolve().parents[2]/'benchmarks'/'reporecourse'


def catalog(root=ROOT):
    result=load(Path(root)/'catalog.json')
    seen=set(); groups={}
    for card in result['tasks']:
        if card['id'] in seen:raise Rejected('duplicate_task')
        seen.add(card['id'])
        if card['family'] not in ('data_product','api_schema') or card['grounding'] not in ('demo_grounded','repo_grounded_authored','synthetic_diagnostic','historical_change'):
            raise Rejected('task_metadata')
        if card['split']!='development':raise Rejected('unreviewed_split')
        if card['grounding']!='synthetic_diagnostic' and (len(card['revision'])!=40 or set(card['revision'])-set('0123456789abcdef')):
            raise Rejected('unresolved_source')
        for part in ('public','private'):
            p=Path(root)/part/(card['id']+'.json')
            if not p.is_file() or file_hash(p)!=card[part+'_sha256']:raise Rejected('task_integrity')
        previous=groups.setdefault(card['source_group'],card['split'])
        if previous!=card['split']:raise Rejected('split_overlap')
    return result


def load_task(task_id, sources, root=ROOT):
    cat=catalog(root)
    card=next((x for x in cat['tasks'] if x['id']==task_id),None)
    if card is None:raise Rejected('unknown_task')
    public=load(Path(root)/'public'/(task_id+'.json'))
    if set(public) != {'id','family','request','required_outputs','sources','tables','examples','outlines'}:
        raise Rejected('public_fields')
    if len(public['required_outputs']) not in (2,3):raise Rejected('required_outputs')
    registry=load(Path(root)/'source_registry.json')
    if card['grounding']!='synthetic_diagnostic':
        pack=next(x for x in registry['packs'] if x['id']==card['pack'])
        if pack['revision']!=card['revision'] or pack['repository']!=card['source_group']:
            raise Rejected('source_pin_mismatch')
        base=Path(sources)/pack['id']
        for f in pack['retained']:
            path=base/f['path']
            if path.is_symlink() or not path.is_file() or file_hash(path)!=f['sha256']:
                raise Rejected('source_missing_or_changed')
            if f['path']=='tables.json':public['tables']=load(path)
            else:public['sources'][f['source_id']]=path.read_text()
    if public['family']=='data_product':
        public['sources']['tables']=deepcopy(public['tables'])
    public['sources']['request']=public['request']
    public['sources']['tool_contract']=tool_contract()
    return card,public


def private_task(task_id, root=ROOT):
    catalog(root)
    value=load(Path(root)/'private'/(task_id+'.json'))
    if not value.get('witnesses') or not value.get('fixtures') or not value.get('oracle'):
        raise Rejected('evaluator_unavailable')
    return value


def tool_contract():
    return {'version':'rr-artifacts-v1','publish':{'tool':'publish','name':'artifact_name',
        'format':'sql | schema | mapping','content':'SELECT string, schema object or mapping object',
        'bindings':{'helper_alias':'exact existing version'},'obligations':['required_output_id']},
        'other_actions':{'list_sources':[], 'read_source':['name'],'search_sources':['query'],
            'read_artifact':['version'],'execute_artifact':['version','input_id'],'check_public':[],
            'bind_output':['obligation','version'],'rebind_artifact':['version','name','bindings','obligations'],'message':['recipient','text'],'checkpoint':[],
            'restore':['checkpoint'],'finish':[]},
        'sql':'SELECT text lowers to bc-select-tree-v1. Explicit columns/aliases; SELECT subqueries, inner/left/cross joins, searched CASE, group/having/order/limit and allowlisted scalar/aggregate functions. No CTE/window/DDL/DML/wildcard/remote object.',
        'schema':'Draft 2020-12 subset: type, properties, required, additionalProperties, items, min/maxItems, enum, const, minimum/maximum, min/maxLength. $ref only rr:<bound helper alias>. No cycles/regex/formats/loaders/custom keywords.',
        'mapping':{'fields':{'output_name':{'path':['input_field'],'missing':'error|omit|null'}},'output_schema':'inline schema or rr reference'},
        'array_mapping':'Use each: <mapping> instead of fields to map at most 128 items. No expressions or callbacks.',
        'finish':'End only the current assignment, without implying correctness or closing other workers. The orchestrator freezes the final bundle.',
        'publish_and_bind':'atomic explicit; compilation validates safety only; final score uses latest explicitly bound versions',
        'rebind_artifact':'Copy an existing immutable program unchanged with explicitly replaced versions under the SAME helper aliases. Publish-and-bind as a new version. All observed provenance is retained; reexecution/checking is charged separately.',
        'resources':'All generated tokens including reasoning + all input tokens; separate CPU cap; no private score feedback'}


def split_check(rows):
    owners={}
    for row in rows:
        for key in (row['source_group'],row['base_change']):
            prior=owners.setdefault(key,row['split'])
            if prior!=row['split']:raise Rejected('split_overlap')
    return {'status':'passed','effective_source_groups':len({r['source_group'] for r in rows})}
