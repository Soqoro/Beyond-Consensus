"""Opt-in public interface; no private tasks, corrections, or evaluator access."""
from copy import deepcopy
from .common import digest, Rejected

PROFILE = 'rr-interface-reliability-v1'
FEEDBACK = 'rr-public-validation-v1'
MAX_FINDINGS = 3


def enabled(value):
    if value is None:return False
    if value != PROFILE:raise Rejected('interface_profile')
    return True


def mode(role):
    return f'reporecourse-{role}-reliable-v1-pool-7'


def example_plan():
    return {'schema':'rr-work-plan-v2','id':'neutral_example','units':[
        dict(id='prepare',worker='w0',outputs=[],depends=[],description='Build a reusable public relation.',
             produces={'invented_rows':'sql'},consumes={},sources=[],interfaces={'invented_rows':'A relation with id.'},terminal_bindings={}),
        dict(id='deliver',worker='w1',outputs=['report'],depends=['prepare'],description='Produce the required report.',
             produces={'invented_report':'sql'},consumes={'rows':{'unit':'prepare','artifact':'invented_rows','format':'sql'}},
             sources=[],interfaces={'invented_report':'The required report columns.'},terminal_bindings={'report':'invented_report'})]}


def planner_contract():
    return dict(version=PROFILE,
        rules=['outputs contains ONLY terminal obligation IDs from required_outputs; helper-only units use outputs: [].',
               'produces declares invented intermediate or terminal artifact names and their formats.',
               'terminal_bindings maps each unit output obligation ID to an artifact in that unit produces.',
               'consumes maps local aliases to upstream unit/artifact/format declarations; depends lists those producer unit IDs.',
               'sources contains public source IDs. Other bounded acyclic graphs, grouping and ownership are allowed; this example is syntax, not a topology menu.'],
        syntax_example=example_plan())


def publications():
    return [dict(tool='publish',name='neutral_schema',format='schema',content={'type':'object','properties':{'label':{'type':['string','null']}},'required':['label']},bindings={},obligations=[]),
            dict(tool='publish',name='neutral_mapping',format='mapping',content={'fields':{'label':{'path':['name'],'missing':'error'}},'output_schema':{'type':'object','properties':{'label':{'type':'string'}},'required':['label']}},bindings={},obligations=[]),
            dict(tool='publish',name='neutral_sql',format='sql',content='SELECT id FROM demo WHERE (id = 1 OR id = 3) AND id >= 1 AND id <= 9',bindings={},obligations=[])]


def worker_contract():
    from restricted_artifacts.sql_text import capability
    return dict(version=PROFILE,feedback=FEEDBACK,
        content_types='SQL: string. Schema: object (Boolean schemas also remain valid). Mapping: object with top-level output_schema. Do not JSON-encode objects into strings. No automatic decoding, insertion or repair.',
        examples=publications(),sql_capability=capability())


def finding(code,path,value,expected,correction):
    # Only public submitted values. Never echo arbitrary prose or entire content.
    safe=value if type(value) in (int,float,bool,type(None)) else value[:96] if isinstance(value,str) else None
    return dict(code=code,path=path[:160],supplied_type=type(value).__name__,supplied_value=safe,
                expected=expected,correction=correction)


def feedback(items):
    return dict(feedback_version=FEEDBACK,findings=items[:MAX_FINDINGS],truncated=len(items)>MAX_FINDINGS)


def plan_feedback(plan,public,error):
    items=[];permitted=[r['id'] for r in public['required_outputs']]
    if isinstance(plan,dict) and isinstance(plan.get('units'),list):
        for i,u in enumerate(plan['units']):
            if not isinstance(u,dict):continue
            if len(items)>MAX_FINDINGS:break
            values=u.get('outputs')
            if not isinstance(values,list):
                items.append(finding('terminal_outputs_type',f'units[{i}].outputs',values,'array of public terminal IDs','Use [] for helper-only units.'))
            else:
                for j,v in enumerate(values):
                    if len(items)>MAX_FINDINGS:break
                    if v not in permitted:items.append(finding('terminal_output_id',f'units[{i}].outputs[{j}]',v,
                        {'permitted_terminal_ids':permitted},'Put artifact names in produces; outputs lists terminal obligations only.'))
    if not items and isinstance(plan,dict) and isinstance(plan.get('units'),list):
        units=plan['units'];by={u.get('id'):u for u in units if isinstance(u,dict) and isinstance(u.get('id'),str)}
        if str(error)=='consumer_interface':
            for i,u in enumerate(units):
                if not isinstance(u,dict) or not isinstance(u.get('consumes'),dict):continue
                for alias,item in sorted(u['consumes'].items()):
                    ok=(isinstance(item,dict) and set(item)=={'unit','artifact','format'} and
                        isinstance(item.get('unit'),str) and item['unit'] in (u.get('depends') or []) and
                        isinstance(item.get('artifact'),str) and by.get(item['unit'],{}).get('produces',{}).get(item['artifact'])==item['format'])
                    if not ok:items.append(finding('consumer_interface',f'units[{i}].consumes.{alias}',None,
                        'unit/artifact/format of a declared predecessor','Match the declared producer and add its unit to depends.'))
                    if len(items)>MAX_FINDINGS:break
                if len(items)>MAX_FINDINGS:break
    if not items:items=[finding(str(error),'plan',None,'valid rr-work-plan-v2 public structure','Check dependencies, coverage, owners and producer bindings against the public contract.')]
    return feedback(items)


def publication_feedback(format,content,error):
    if format in ('schema','mapping') and not isinstance(content,dict) and not (format=='schema' and type(content) is bool):
        return feedback([finding('content_type','content',content,'object or Boolean schema' if format=='schema' else 'object','Emit JSON content directly, not an encoded string.')])
    if format=='sql' and not isinstance(content,str):
        return feedback([finding('content_type','content',content,'string','Emit SELECT text as a JSON string.')])
    if format=='mapping' and isinstance(content,dict) and 'output_schema' not in content:
        return feedback([finding('mapping_missing_field','content.output_schema',None,'top-level output_schema','Supply output_schema at the top level of mapping content.')])
    from .schema_runtime import KEYWORDS
    def walk(s,path,depth=0):
        if depth>16 or len(items)>MAX_FINDINGS or not isinstance(s,dict):return
        for k in sorted(set(s)-KEYWORDS):
            if len(items)>MAX_FINDINGS:break
            items.append(finding('unsupported_schema_keyword',path+'.'+k,k,{'supported_keywords':sorted(KEYWORDS)},'Use the documented schema subset.'))
        props=s.get('properties',{})
        if isinstance(props,dict):
            for k,v in sorted(props.items()):walk(v,path+'.properties.'+k,depth+1)
        for k in ('items','additionalProperties'):
            if k in s:walk(s[k],path+'.'+k,depth+1)
    items=[]
    if format=='schema':walk(content,'content')
    elif format=='mapping' and isinstance(content,dict):walk(content.get('output_schema'),'content.output_schema')
    if format=='mapping' and not items and isinstance(content,dict):
        def mapping_shape(p,path,depth=0):
            if depth>8 or len(items)>MAX_FINDINGS:return
            if not isinstance(p,dict):
                items.append(finding('mapping_object',path,p,'object','Use a mapping object.'));return
            for k in sorted(set(p)-{'fields','each','output_schema'}):
                items.append(finding('mapping_unknown_field',path+'.'+k,k,'fields or each, and output_schema','Use the documented mapping fields.'))
            if 'each' in p:
                if 'fields' in p:items.append(finding('mapping_conflict',path+'.fields',None,'each OR fields','Choose one mapping operation.'))
                mapping_shape(p['each'],path+'.each',depth+1)
            elif not isinstance(p.get('fields'),dict):items.append(finding('mapping_fields',path+'.fields',p.get('fields'),'object','Supply fields keyed by output names.'))
            else:
                for k,op in sorted(p['fields'].items()):
                    if not isinstance(op,dict) or set(op)!={'path','missing'}:
                        items.append(finding('mapping_operation',path+'.fields.'+k,op,'object with path and missing','Use the mapping operation envelope.'))
                    elif op['missing'] not in ('error','omit','null'):
                        items.append(finding('mapping_missing_policy',path+'.fields.'+k+'.missing',op['missing'],'error, omit or null','Select a supported policy.'))
                    elif not isinstance(op['path'],list) or not 1<=len(op['path'])<=8:
                        items.append(finding('mapping_path',path+'.fields.'+k+'.path',op['path'],'array of 1..8 field IDs','Supply a bounded field path.'))
                    if len(items)>MAX_FINDINGS:return
        if str(error).startswith('mapping_'):mapping_shape(content,'content')
    return feedback(items or [finding(str(error),'content',None,'public '+str(format)+' contract','Check the submitted structure; no content is repaired.')])


def bindings():
    from .action_schema import schema_v2
    from restricted_artifacts.sql_text import capability
    from .qualification import implementation_hashes
    from .resources import ACCOUNTING
    return dict(profile=PROFILE,accounting=ACCOUNTING,runtime_hashes=implementation_hashes(),planner_prompt=digest(planner_contract()),worker_prompt=digest(worker_contract()),
                examples=digest([example_plan(),publications()]),feedback_schema=digest([FEEDBACK,MAX_FINDINGS,sorted(finding('x','x',None,'x','x'))]),
                generation_grammars={r:digest(schema_v2(mode(r))) for r in ('json','plan')},
                compiler_capability=digest(capability()))
