"""Explicit arithmetic compatibility fixtures, never historical experiment records."""
from copy import deepcopy


def artifact(a, type='rational', version='v1'):return {'artifact':a,'version':version,'type':type}
def ref(event=None,source=None):return {'source':source,'event':event,'port':'out'}
def mode(id, reads, operator='sum', when=None, initial='1', replay='1'):
    return dict(id=id,when=when or {},reads=reads,initial=initial,replay=replay,operator=operator)
def event(id,host,inputs,output,modes,kind='compute',when=None,sources=None):
    return dict(id=id,host=host,kind=kind,when=when or {},inputs=inputs,output=output,
                allowed_sources=sources or [],modes=modes)
def route(id,producer,when=None,path=None,owner_pairs=None):
    return dict(id=id,producer=producer,transform='identity',cost_accounting='included_in_consumer_mode',path=path or ['origin','endpoint'],when=when or {},owner_pairs=owner_pairs)
def variant(id,events,producer,when=None):
    return dict(id=id,when=when or {},required_events=events,deliverables={'result':ref(event=producer)})


def graph_fixture(n=2,m=4,K=2,parents=None,prices=None):
    parents=parents if parents is not None else {i:[i-1] if i else [] for i in range(m)}
    owners=[f'o{i}' for i in range(n)]
    d={'schema':'joint-domain-v1','source':{'id':'synthetic-fixed-graph','kind':'synthetic_fixture',
       'provenance':'Formula-derived compatibility control, not a historical rerun'},
       'n':n,'m':m,'K':K,'objective':'mean_first','unit':'synthetic-rational-work',
       'tasks':[],'owners':[{'id':o,'max_operations':None,'max_initial':None} for o in owners],
       'sources':[],'choices':[],'events':[],'routes':[],
       'schedule':{'template':'serial-event-order-v1','order':[f'e{i}' for i in range(m)]},
       'network':{'nodes':['origin','endpoint','middle'],'edges':[['origin','endpoint'],['origin','middle'],['middle','endpoint']]},
       'exclusive':[],'forbidden':[],'obligations':[],'budgets':{'initial':None,'incident':None}}
    for i in range(m):
        t=f't{i}';e=f'e{i}';s=f's{i}';out=artifact(f'value{i}')
        d['sources'].append({'id':s,'artifact':artifact(f'input{i}'),'origin':'synthetic_fixture','value':i+1})
        reads={'own':f'r_source{i}'};inputs={'own':artifact(f'input{i}')}
        d['routes'].append(route(f'r_source{i}',ref(source=s)))
        for j in parents[i]:
            reads[f'p{j}']=f'r_e{j}';inputs[f'p{j}']=artifact(f'value{j}')
        d['routes'].append(route(f'r_e{i}',ref(event=e)))
        d['tasks'].append(dict(id=t,instruction=f'Produce the specified arithmetic intermediate {i}.',
            deliverables={'result':out},eligible_owners=list(owners),variants=[variant('base',[e],e)]))
        d['events'].append(event(e,t,inputs,out,[mode('base',reads,replay=str(prices[i]) if prices else '1')],sources=[f's{j}' for j in range(m)]))
    terminals=[i for i in range(m) if not any(i in ps for ps in parents.values())]
    d['obligations']=[{'id':f'q{i}','artifact':artifact(f'value{i}'),'producers':[{'when':{},'ref':ref(event=f'e{i}') }]} for i in terminals]
    return d


def square_domain():
    """Compute x²+y; square vs multiply, protected routes vs relay/state."""
    d=graph_fixture();d['source']['id']='synthetic-square-plus-offset'
    d['source']['provenance']='Exact synthetic arithmetic x^2+y; no planner or benchmark output'
    d['choices']=[dict(id='calculation',axis='A',options=['square','multiply']),
        dict(id='delivery',axis='C',options=['direct','relay','state']),
        dict(id='drawing',axis='C',options=['direct','via']),dict(id='diagnostic',axis='C',options=['off','on'])]
    x,y,sq,sv,total,answer=[artifact(a) for a in ('x','y','squared','saved-square','total','answer')]
    sv['type']='state.rational'
    d['sources']=[dict(id='x',artifact=x,origin='synthetic_fixture',value='3'),
                  dict(id='y',artifact=y,origin='synthetic_fixture',value='5')]
    d['routes']=[route('x_direct',ref(source='x'),{'drawing':'direct'}),
        route('x_via',ref(source='x'),{'drawing':'via'},['origin','middle','endpoint']),
        route('y_read',ref(source='y')),route('square_read',ref(event='squared'),{'calculation':'square'}),
        route('multiply_read',ref(event='multiplied'),{'calculation':'multiply'}),
        route('relay_read',ref(event='relayed'),{'delivery':'relay'}),
        route('state_read',ref(event='retained'),{'delivery':'state'}),
        route('offset_read',ref(event='offset')),route('sum_read',ref(event='added')),
        route('state_sum_read',ref(event='state_added'))]
    square_modes=[mode(draw,{'x':f'x_{draw}'},'square',{'drawing':draw},'2','3/2') for draw in ('direct','via')]
    mul_modes=[mode(draw,{'left':f'x_{draw}','right':f'x_{draw}'},'product',{'drawing':draw},'3','5/2') for draw in ('direct','via')]
    forward=[mode(calc,{'square':f'{calc}_read'},'identity',{'calculation':calc},'1','1/2') for calc in ('square','multiply')]
    add_modes=[mode(calc,{'x':f'{calc}_read','y':'offset_read'},'sum',{'calculation':calc,'delivery':'direct'},'2','2') for calc in ('square','multiply')]
    add_modes.append(mode('relay',{'x':'relay_read','y':'offset_read'},'sum',{'delivery':'relay'},'3','3'))
    d['events']=[event('squared','t0',{'x':x},sq,square_modes,when={'calculation':'square'},sources=['x']),
        event('multiplied','t0',{'left':x,'right':x},sq,mul_modes,when={'calculation':'multiply'},sources=['x']),
        event('offset','t1',{'y':y},y,[mode('base',{'y':'y_read'},'identity')],sources=['y']),
        event('relayed','t1',{'square':sq},sq,deepcopy(forward),'relay',{'delivery':'relay'},['x']),
        event('retained','t1',{'square':sq},sv,deepcopy(forward),'state',{'delivery':'state'},['x']),
        event('added','t2',{'x':sq,'y':y},total,add_modes,sources=['x','y']),
        event('state_added','t2',{'x':sv,'y':y},total,[mode('state',{'x':'state_read','y':'offset_read'},'sum',initial='4',replay='7/2')],when={'delivery':'state'},sources=['x','y']),
        event('finished','t3',{'total':total},answer,[mode(c,{'total':'state_sum_read' if c=='state' else 'sum_read'},'identity',{'delivery':c}) for c in ('direct','relay','state')],kind='synthesis',sources=['x','y']),
        event('debug','t3',{'x':x},artifact('debug'),[mode(draw,{'x':f'x_{draw}'},'identity',{'drawing':draw},'5','7') for draw in ('direct','via')],kind='diagnostic',when={'diagnostic':'on'},sources=['x'])]
    # Activity predicates use equality conjunctions; direct/relay share the same
    # add event, so separate direct and relay activation is represented by two
    # explicit event identities rather than an implicit OR control flow.
    base=d['events'][5];base['when']={'delivery':'direct'};base['modes']=add_modes[:2]
    relay_add=deepcopy(base);relay_add['id']='relay_added';relay_add['when']={'delivery':'relay'};relay_add['modes']=[add_modes[2]]
    d['events'].insert(6,relay_add)
    d['routes'].append(route('relay_sum_read',ref(event='relay_added'),{'delivery':'relay'}))
    for e in d['events']:
        if e['id']=='finished':e['modes'][1]['reads']['total']='relay_sum_read'
    d['schedule']['order']=[e['id'] for e in d['events']]
    for t,out,variants in zip(d['tasks'],(sq,y,total,answer),(
        [variant('square',['squared'],'squared',{'calculation':'square'}),variant('multiply',['multiplied'],'multiplied',{'calculation':'multiply'})],
        [variant('base',['offset'],'offset')],
        [variant('direct',['added'],'added',{'delivery':'direct'}),variant('relay',['relay_added'],'relay_added',{'delivery':'relay'}),variant('state',['state_added'],'state_added',{'delivery':'state'})],
        [variant('base',['finished'],'finished')])):
        t['deliverables']={'result':out};t['variants']=variants
    d['tasks'][1]['instruction']='Produce offset y and, when selected, relay or retain the squared term for combination.'
    d['exclusive']=[['squared','multiplied'],['added','relay_added','state_added']]
    d['obligations']=[dict(id='answer',artifact=answer,producers=[dict(when={},ref=ref(event='finished'))])]
    return d


def communication_control(n=3,edges=((0,1),(1,2)),rounds=2):
    """Explicit persistent all-neighbour synchronous compatibility fixture only."""
    d=graph_fixture(n,n,1,parents={i:[] for i in range(n)})
    d['source']['id']='formula-C-persistent-round-control';d['events']=[];d['routes']=[]
    for tick in range(rounds+1):
        for i in range(n):
            eid=f'u{i}_{tick}';inputs={};reads={}
            if tick==0:
                inputs['own']=artifact(f'input{i}');reads['own']=f'source{i}'
                d['routes'].append(route(f'source{i}',ref(source=f's{i}')))
            else:
                neighbors=sorted({i}|{b for a,b in edges if a==i}|{a for a,b in edges if b==i})
                for j in neighbors:
                    inputs[f'p{j}']=artifact(f'value{j}_{tick-1}')
                    rid=f'r_{j}_{tick-1}';reads[f'p{j}']=rid
            d['events'].append(event(eid,f't{i}',inputs,artifact(f'value{i}_{tick}'),[mode('base',reads)],
                                    kind='state' if tick else 'compute',sources=[f's{j}' for j in range(n)]))
            d['routes'].append(route(f'r_{i}_{tick}',ref(event=eid)))
    for i,t in enumerate(d['tasks']):
        last=f'u{i}_{rounds}';t['eligible_owners']=[f'o{i}'];t['deliverables']={'result':artifact(f'value{i}_{rounds}')}
        t['variants']=[variant('base',[f'u{i}_{r}' for r in range(rounds+1)],last)]
    d['schedule']['order']=[e['id'] for e in d['events']]
    d['obligations']=[dict(id=f'q{i}',artifact=artifact(f'value{i}_{rounds}'),producers=[dict(when={},ref=ref(event=f'u{i}_{rounds}'))]) for i in range(n)]
    return d
