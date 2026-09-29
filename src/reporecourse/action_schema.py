"""Task-independent RepoRecourse JSON envelope. Semantic safety stays runtime."""
MODE='reporecourse-json-v1'


def schema():
    def obj(props):return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
    string={'type':'string'}
    value={'$ref':'#/$defs/value'}
    defs={'value':{'anyOf':[{'type':'null'},{'type':'boolean'},{'type':'number'},string,
        {'type':'array','items':value}, {'type':'object','additionalProperties':value}]}}
    actions=[]
    fields={'list_sources':{},'read_source':{'name':string},'search_sources':{'query':string},
        'read_artifact':{'version':string},'publish':{'name':string,'format':{'enum':['sql','schema','mapping']},
            'content':value,'bindings':{'type':'object','additionalProperties':string},'obligations':{'type':'array','items':string}},
        'rebind_artifact':{'version':string,'name':string,'bindings':{'type':'object','additionalProperties':string},'obligations':{'type':'array','items':string}},
        'bind_output':{'obligation':string,'version':string},'execute_artifact':{'version':string,'input_id':string},
        'check_public':{},'message':{'recipient':{'enum':['w0','w1','w2','w3']},'text':string},
        'checkpoint':{},'restore':{'checkpoint':string},'finish':{},
        'plan_catalog':{'plans':{'type':'array','items':value,'minItems':1,'maxItems':3}}}
    for name,args in fields.items():actions.append(obj({'tool':{'enum':[name]},**args}))
    return {'anyOf':actions,'$defs':defs}


def controls():
    good=[{'tool':'list_sources'},{'tool':'read_source','name':'public-demo'},
        {'tool':'publish','name':'demo','format':'sql','content':'SELECT "id" FROM "demo"','bindings':{},'obligations':['report']},
        {'tool':'publish','name':'demo','format':'schema','content':{'type':'object','properties':{'x':{'type':['string','null']}}},'bindings':{},'obligations':['validator']},
        {'tool':'publish','name':'demo','format':'mapping','content':{'fields':{'x':{'path':['id'],'missing':'error'}},'output_schema':{'type':'object'}},'bindings':{},'obligations':[]},
        {'tool':'rebind_artifact','version':'demo-version','name':'consumer','bindings':{'helper':'other-version'},'obligations':['report']},
        {'tool':'plan_catalog','plans':[{'id':'example','units':[]}]}, {'tool':'finish'}]
    bad=['{}','{"tool":"shell","command":"true"}','{"tool":"publish","content":0}',
         '{"tool":"read_source","tool":"finish","name":"demo"}']
    return good,bad

V2_MODES=tuple(f'reporecourse-{kind}-v2-pool-{n}' for kind in ('json','plan') for n in range(2,9))


def schema_v2(mode):
    from .v2 import worker_registry
    if mode not in V2_MODES:raise ValueError('v2 mode')
    workers=list(worker_registry(int(mode.rsplit('-',1)[1])))
    if '-json-' in mode:
        result=schema()
        for action in result['anyOf']:
            if action['properties']['tool']['enum']==['message']:
                action['properties']['recipient']={'enum':workers}
        # Execution identities cannot invoke planning tools.
        result['anyOf']=[a for a in result['anyOf'] if a['properties']['tool']['enum']!=['plan_catalog']]
        return result
    def obj(props):return {'type':'object','properties':props,'required':list(props),'additionalProperties':False}
    string={'type':'string','maxLength':2048}
    names={'type':'array','items':string,'maxItems':24}
    fmt={'enum':['sql','schema','mapping']}
    unit=obj(dict(id=string,worker={'enum':workers},outputs=names,depends=names,description=string,
        produces={'type':'object','additionalProperties':fmt},
        consumes={'type':'object','additionalProperties':obj(dict(unit=string,artifact=string,format=fmt))},sources=names))
    plan=obj({'schema':{'enum':['rr-work-plan-v2']},'id':string,'units':{'type':'array','items':unit,'minItems':1,'maxItems':24}})
    return {'anyOf':[obj({'tool':{'enum':['read_source']},'name':string}),
        obj({'tool':{'enum':['submit_plan']},'plan':plan})]}


def controls_v2(mode):
    if '-json-' in mode:
        good,bad=controls();good=[a for a in good if a['tool']!='plan_catalog']
        good.append({'tool':'message','recipient':f'w{int(mode.rsplit("-",1)[1])-1}','text':'synthetic'})
    else:
        good=[{'tool':'read_source','name':'synthetic'}, {'tool':'submit_plan','plan':{
            'schema':'rr-work-plan-v2','id':'demo','units':[{'id':'result','worker':f'w{int(mode.rsplit("-",1)[1])-1}',
            'outputs':['result'],'depends':[],'description':'Implement public requirement.',
            'produces':{'result':'sql'},'consumes':{},'sources':[]}]}}]
        bad=['{}','{"tool":"publish"}']
    bad.append('{"tool":"message","recipient":"w8","text":"invalid"}')
    return good,bad
