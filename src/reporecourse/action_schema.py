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
