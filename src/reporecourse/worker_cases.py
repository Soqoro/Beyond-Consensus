"""Prospectively authored synthetic single-obligation cases; private controls separate.

Screen and confirmation combinations are frozen together, never mined from model output.
"""
from copy import deepcopy
from .common import digest


def table(columns, rows):
    return {'columns': [[c, 'INTEGER' if c not in ('kind', 'name', 'state') else 'TEXT'] for c in columns], 'rows': rows}


def sql_case(split, name, family, request, tables, columns, reference, expected, mutant):
    return dict(id=f'{split}-sql-{name}', split=split, domain='sql', family=family,
        provenance='benchmark_authored_synthetic', template=f'{split}/{name}',
        public=dict(id=f'{split}-sql-{name}', family='data_product', request=request,
            sources={'tables': tables}, tables=tables, examples={'default': {}},
            required_outputs=[dict(id='report', format='sql', columns=columns)]),
        private=dict(reference=reference, expected=dict(columns=columns, rows=expected), mutant=mutant))


def schema_case(split, name, family, request, schema, checks, negative):
    return dict(id=f'{split}-api-{name}', split=split, domain='api', family=family,
        provenance='benchmark_authored_synthetic', template=f'{split}/{name}',
        public=dict(id=f'{split}-api-{name}', family='api_schema', request=request, sources={'contract': request},
            tables={}, examples={'default': checks[0][0]}, required_outputs=[dict(id='report',format='schema')]),
        private=dict(reference=schema, checks=checks, mutant=negative))


def mapping_case(split, name, family, request, inputs, fields, outputs, schema):
    program={'fields':fields,'output_schema':schema}
    wrong=deepcopy(program); key=next(iter(fields)); wrong['fields']['wrong_field']=wrong['fields'].pop(key)
    # Wrong-but-valid own-schema artifact remains possible.
    wrong['output_schema']={'type':'object'}
    return dict(id=f'{split}-api-{name}',split=split,domain='api',family=family,
        provenance='benchmark_authored_synthetic',template=f'{split}/{name}',
        public=dict(id=f'{split}-api-{name}',family='api_schema',request=request,
            sources={'contract':request},tables={},examples={'default':inputs[0]},
            allowed_inputs=inputs, required_outputs=[dict(id='report',format='mapping')]),
        private=dict(reference=program,checks=list(zip(inputs,outputs)),mutant=wrong))


def obj(props, required):
    return dict(type='object',properties=props,required=required,additionalProperties=False)


def path(*parts, missing='error'):
    return dict(path=list(parts),missing=missing)


def cases():
    s=[]
    def add(split,name,family,request,tables,cols,sql,rows,mutant=None):
        # Constant-output negative deliberately obeys column shape but not semantics.
        mutant=mutant or 'SELECT '+', '.join('0 AS '+c for c in cols)
        s.append(sql_case(split,name,family,request,tables,cols,sql,rows,mutant))
    add('screen','ticket-details','entity_grain','For each queue including empty queues return queue_id and ticket_count. Count tickets once regardless of tag records.',
        {'queues':table(['id'],[[1],[2],[3]]),'tickets':table(['id','queue_id'],[[10,1],[11,1],[20,2]]),'tags':table(['ticket_id'],[[10],[10],[20]])},
        ['queue_id','ticket_count'],'SELECT q.id AS queue_id, COUNT(DISTINCT t.id) AS ticket_count FROM queues q LEFT JOIN tickets t ON q.id=t.queue_id LEFT JOIN tags g ON t.id=g.ticket_id GROUP BY q.id',[[1,2],[2,1],[3,0]],
        'SELECT q.id AS queue_id, COUNT(t.id) AS ticket_count FROM queues q LEFT JOIN tickets t ON q.id=t.queue_id LEFT JOIN tags g ON t.id=g.ticket_id GROUP BY q.id')
    add('screen','zero-checks','missing_boundary','For each device return device_id and check_count. A zero reading is a recorded check; devices without checks have zero checks.',
        {'devices':table(['id'],[[1],[2],[3]]),'checks':table(['id','device_id','reading'],[[1,1,0],[2,1,4],[3,2,0]])},['device_id','check_count'],
        'SELECT d.id AS device_id, COUNT(c.id) AS check_count FROM devices d LEFT JOIN checks c ON d.id=c.device_id GROUP BY d.id',[[1,2],[2,1],[3,0]])
    add('screen','signed-stock','aggregation','Return item_id and net_units for each item including those without movement. Movement quantities are signed and repeated quantities each count.',
        {'items':table(['id'],[[1],[2]]),'moves':table(['item_id','qty'],[[1,5],[1,5],[1,-3]])},['item_id','net_units'],
        'SELECT i.id AS item_id, COALESCE(SUM(m.qty),0) AS net_units FROM items i LEFT JOIN moves m ON i.id=m.item_id GROUP BY i.id',[[1,7],[2,0]])
    add('screen','balance','reconciliation','Return account_id, expected, actual, gap for every account; actual is the sum of recorded credits, absent credits total zero, gap is expected minus actual.',
        {'accounts':table(['id','expected'],[[1,12],[2,4],[3,0]]),'credits':table(['account_id','amount'],[[1,5],[1,7],[2,1]])},['account_id','expected','actual','gap'],
        'SELECT a.id AS account_id,a.expected AS expected,COALESCE(SUM(c.amount),0) AS actual,a.expected-COALESCE(SUM(c.amount),0) AS gap FROM accounts a LEFT JOIN credits c ON a.id=c.account_id GROUP BY a.id,a.expected',[[1,12,12,0],[2,4,1,3],[3,0,0,0]])
    add('screen','threshold','conditional','Return group_id and high_count for each group. Count observations whose value is at least 5; missing observations count zero.',
        {'groups':table(['id'],[[1],[2]]),'observations':table(['group_id','value'],[[1,5],[1,4],[1,9]])},['group_id','high_count'],
        'SELECT g.id AS group_id,SUM(CASE WHEN o.value >= 5 THEN 1 ELSE 0 END) AS high_count FROM groups g LEFT JOIN observations o ON g.id=o.group_id GROUP BY g.id',[[1,2],[2,0]])
    add('screen','maximum','aggregate_boundary','For each route return route_id and longest, the maximum duration. Return -1 only for routes with no duration records. Zero duration is valid.',
        {'routes':table(['id'],[[1],[2],[3]]),'trips':table(['route_id','duration'],[[1,3],[1,8],[2,0]])},['route_id','longest'],
        'SELECT r.id AS route_id,COALESCE(MAX(t.duration),-1) AS longest FROM routes r LEFT JOIN trips t ON r.id=t.route_id GROUP BY r.id',[[1,8],[2,0],[3,-1]])
    # Fresh combinations: multiple detail domains, absence versus partial fulfillment,
    # category groups, distinct qualification, weighted values, and reconciliation.
    add('confirm','two-details','entity_grain','For every project return project_id, hours, issue_count. Hours sum work records; issue_count counts issue records. Work and issues are independent detail tables.',
        {'projects':table(['id'],[[1],[2],[3]]),'work':table(['project_id','hours'],[[1,2],[1,3],[2,4]]),'issues':table(['id','project_id'],[[10,1],[11,1],[12,1],[13,3]])},['project_id','hours','issue_count'],
        'SELECT p.id AS project_id,COALESCE((SELECT SUM(w.hours) AS total FROM work w WHERE w.project_id=p.id),0) AS hours,(SELECT COUNT(i.id) AS n FROM issues i WHERE i.project_id=p.id) AS issue_count FROM projects p',[[1,5,3],[2,4,0],[3,0,1]])
    add('confirm','fulfillment','missing_boundary','For every request return request_id, remaining, delivery_count. Remaining is requested units minus sum of delivered units (absent delivery is zero); zero-unit deliveries still count.',
        {'requests':table(['id','units'],[[1,8],[2,3],[3,0]]),'deliveries':table(['id','request_id','units'],[[1,1,2],[2,1,2],[3,2,0]])},['request_id','remaining','delivery_count'],
        'SELECT r.id AS request_id,r.units-COALESCE(SUM(d.units),0) AS remaining,COUNT(d.id) AS delivery_count FROM requests r LEFT JOIN deliveries d ON r.id=d.request_id GROUP BY r.id,r.units',[[1,4,2],[2,3,1],[3,0,0]])
    add('confirm','category-net','aggregation','Return kind, net, records grouped by ledger kind. Signed amounts and duplicates count individually; include zero-net kinds.',
        {'ledger':table(['kind','amount'],[['sale',8],['sale',-3],['sale',-3],['refund',2],['refund',-2]])},['kind','net','records'],
        'SELECT kind,SUM(amount) AS net,COUNT(*) AS records FROM ledger GROUP BY kind',[['refund',0,2],['sale',2,3]])
    add('confirm','regional-gap','reconciliation','For every region return region_id, target, delivered, gap. Target sums site quotas; delivered sums shipment quantities for those sites; gap is target minus delivered. Sites may have several shipments.',
        {'regions':table(['id'],[[1],[2]]),'sites':table(['id','region_id','quota'],[[10,1,7],[11,1,5]]),'shipments':table(['site_id','qty'],[[10,2],[10,3],[11,4]])},['region_id','target','delivered','gap'],
        'SELECT r.id AS region_id,COALESCE((SELECT SUM(s.quota) AS n FROM sites s WHERE s.region_id=r.id),0) AS target,COALESCE((SELECT SUM(h.qty) AS n FROM sites s INNER JOIN shipments h ON s.id=h.site_id WHERE s.region_id=r.id),0) AS delivered,COALESCE((SELECT SUM(s.quota) AS n FROM sites s WHERE s.region_id=r.id),0)-COALESCE((SELECT SUM(h.qty) AS n FROM sites s INNER JOIN shipments h ON s.id=h.site_id WHERE s.region_id=r.id),0) AS gap FROM regions r',[[1,12,9,3],[2,0,0,0]])
    add('confirm','qualified-members','conditional','For every club return club_id and qualified_members: number of distinct members having at least one score >= 10. Repeated qualifying scores do not duplicate members.',
        {'clubs':table(['id'],[[1],[2]]),'members':table(['id','club_id'],[[10,1],[11,1]]),'scores':table(['member_id','value'],[[10,10],[10,12],[11,9]])},['club_id','qualified_members'],
        'SELECT c.id AS club_id,COUNT(DISTINCT CASE WHEN s.value >= 10 THEN m.id ELSE NULL END) AS qualified_members FROM clubs c LEFT JOIN members m ON c.id=m.club_id LEFT JOIN scores s ON m.id=s.member_id GROUP BY c.id',[[1,1],[2,0]])
    add('confirm','weighted-value','aggregate_boundary','For each bin return bin_id, units, value. Units sum quantities; value sums quantity times unit_price per lot. Empty bins return zeros; zero quantity contributes no value.',
        {'bins':table(['id'],[[1],[2]]),'lots':table(['bin_id','qty','unit_price'],[[1,2,7],[1,3,4],[1,0,99]])},['bin_id','units','value'],
        'SELECT b.id AS bin_id,COALESCE(SUM(l.qty),0) AS units,COALESCE(SUM(l.qty*l.unit_price),0) AS value FROM bins b LEFT JOIN lots l ON b.id=l.bin_id GROUP BY b.id',[[1,5,26],[2,0,0]])
    s += [schema_case('screen','nullable','presence','Schema for an object with required code (string or null), optional note (string only), and no other fields.',obj({'code':{'type':['string','null']},'note':{'type':'string'}},['code']),[[{'code':None},True],[{'code':'x','note':'n'},True],[{},False],[{'code':'x','note':None},False],[{'code':'x','extra':1},False]],{'type':'object'}),
          schema_case('screen','bounded-array','composition','Schema for an array of 1 to 3 integers, each from 0 through 9 inclusive.',{'type':'array','minItems':1,'maxItems':3,'items':{'type':'integer','minimum':0,'maximum':9}},[[[0,9],True],[[],False],[[10],False],[[1,2,3,4],False],[['1'],False]],{'type':'array'}),
          schema_case('screen','exact-record','exact_keys','Schema for exactly required fields ok (boolean) and count (integer >=0). No extra keys.',obj({'ok':{'type':'boolean'},'count':{'type':'integer','minimum':0}},['ok','count']),[[{'ok':True,'count':0},True],[{'ok':False,'count':2},True],[{'ok':True},False],[{'ok':True,'count':-1},False],[{'ok':True,'count':0,'x':1},False]],{'type':'object'})]
    s += [schema_case('confirm','nested-null','presence','Schema for an object with required meta object and optional tag string. meta has required revision integer >=1 and required comment string or null; neither object permits extra keys.',obj({'meta':obj({'revision':{'type':'integer','minimum':1},'comment':{'type':['string','null']}},['revision','comment']),'tag':{'type':'string'}},['meta']),[[{'meta':{'revision':1,'comment':None}},True],[{'meta':{'revision':2,'comment':'x'},'tag':'a'},True],[{'meta':{'revision':1}},False],[{'meta':{'revision':0,'comment':None}},False],[{'meta':{'revision':1,'comment':None,'x':2}},False]],{'type':'object'}),
          schema_case('confirm','array-records','composition','Schema for an array of at most 2 objects. Each object has exactly required id integer and state equal to open or closed. Empty array is valid.',{'type':'array','maxItems':2,'items':obj({'id':{'type':'integer'},'state':{'enum':['open','closed']}},['id','state'])},[[[],True],[[{'id':1,'state':'open'}],True],[[{'id':1,'state':'other'}],False],[[{'id':1}],False],[[{'id':1,'state':'open'}]*3,False]],{'type':'array'}),
          schema_case('confirm','optional-range','exact_keys','Schema for an object with required version exactly 2 and optional score integer from -2 to 2. No extras; missing score is allowed, null is not.',obj({'version':{'const':2},'score':{'type':'integer','minimum':-2,'maximum':2}},['version']),[[{'version':2},True],[{'version':2,'score':-2},True],[{'version':2,'score':None},False],[{'version':1},False],[{'version':2,'score':3},False]],{'type':'object'})]
    s += [mapping_case('screen','nested-fields','exact_keys','Map payload.ident to required item_id and payload.caption to required title. Preserve values; exactly those keys. Both paths always exist.',[{'payload':{'ident':7,'caption':'A'}}],{'item_id':path('payload','ident'),'title':path('payload','caption')},[{'item_id':7,'title':'A'}],obj({'item_id':{'type':'integer'},'title':{'type':'string'}},['item_id','title'])),
          mapping_case('screen','omit','presence','Map required id to id; map optional note to annotation, omitting annotation when note is absent. Preserve present null. No other output keys.',[{'id':1},{'id':2,'note':None},{'id':3,'note':'z'}],{'id':path('id'),'annotation':path('note',missing='omit')},[{'id':1},{'id':2,'annotation':None},{'id':3,'annotation':'z'}],obj({'id':{'type':'integer'},'annotation':{'type':['string','null']}},['id'])),
          mapping_case('screen','preserve','composition','Copy required flags object to options and required tags array to names, preserving all contents; exactly these output keys.',[{'flags':{'on':False},'tags':['a','a']},{'flags':{},'tags':[]}],{'options':path('flags'),'names':path('tags')},[{'options':{'on':False},'names':['a','a']},{'options':{},'names':[]}],obj({'options':{'type':'object'},'names':{'type':'array'}},['options','names']))]
    s += [mapping_case('confirm','nested-optional','presence','Copy source.key to required record_id; source.detail to description, omitted if absent but preserved when null. Copy source.values to required samples unchanged. No extra output keys.',[{'source':{'key':1,'values':[0,0]}},{'source':{'key':2,'values':[],'detail':None}}],{'record_id':path('source','key'),'description':path('source','detail',missing='omit'),'samples':path('source','values')},[{'record_id':1,'samples':[0,0]},{'record_id':2,'samples':[],'description':None}],obj({'record_id':{'type':'integer'},'description':{'type':['string','null']},'samples':{'type':'array'}},['record_id','samples'])),
          mapping_case('confirm','null-default','exact_keys','Copy required key to key. Copy nested info.text to required summary; if the path is missing emit null. Preserve present strings. Exactly key and summary.',[{'key':1},{'key':2,'info':{}},{'key':3,'info':{'text':'x'}}],{'key':path('key'),'summary':path('info','text',missing='null')},[{'key':1,'summary':None},{'key':2,'summary':None},{'key':3,'summary':'x'}],obj({'key':{'type':'integer'},'summary':{'type':['string','null']}},['key','summary'])),
          mapping_case('confirm','array-projection','composition','Map every input array item to exactly code from item_id and payload from data. Preserve data objects including null members, preserve item order; empty input yields empty array.',[[{'item_id':2,'data':{'x':None}},{'item_id':1,'data':{}}],[]],{'code':path('item_id'),'payload':path('data')},[[{'code':2,'payload':{'x':None}},{'code':1,'payload':{}}],[]],obj({'code':{'type':'integer'},'payload':{'type':'object'}},['code','payload']))]
    last=s[-1]
    for field in ('reference','mutant'):
        p=last['private'][field]; last['private'][field]={'each':{'fields':p['fields']},'output_schema':{'type':'array','items':p['output_schema']}}
    # Prospective semantic mutants preserve the requested column shape and exercise
    # the intended error, rather than relying only on a constant/wrong-row-count test.
    replacements={
        'screen-sql-zero-checks':('COUNT(c.id)','COUNT(*)'),
        'screen-sql-signed-stock':('SUM(m.qty)','SUM(DISTINCT m.qty)'),
        'screen-sql-balance':('SUM(c.amount)','MAX(c.amount)'),
        'screen-sql-threshold':('o.value >= 5','o.value > 5'),
        'screen-sql-maximum':('MAX(t.duration),-1','MAX(t.duration),0'),
        'confirm-sql-fulfillment':('COUNT(d.id)','COUNT(*)'),
        'confirm-sql-category-net':('SUM(amount)','SUM(DISTINCT amount)'),
        'confirm-sql-qualified-members':('COUNT(DISTINCT CASE','COUNT(CASE'),
        'confirm-sql-weighted-value':('SUM(l.qty*l.unit_price)','SUM(l.unit_price)'),
        'confirm-sql-regional-gap':('SUM(s.quota)','MAX(s.quota)'),
    }
    for c in s:
        if c['id'] in replacements:
            old,new=replacements[c['id']]
            c['private']['mutant']=c['private']['reference'].replace(old,new)
    combined=next(c for c in s if c['id']=='confirm-sql-two-details')
    combined['private']['mutant']='SELECT p.id AS project_id,COALESCE(SUM(w.hours),0) AS hours,COUNT(i.id) AS issue_count FROM projects p LEFT JOIN work w ON p.id=w.project_id LEFT JOIN issues i ON p.id=i.project_id GROUP BY p.id'
    # Negative inputs exercise each public schema boundary (root and nested).
    for c in s:
        if c['id']=='confirm-api-nested-null':c['private']['checks'].append([{'meta':{'revision':1,'comment':None},'extra':0},False])
        if c['id']=='confirm-api-array-records':c['private']['checks'].append([[{'id':1,'state':'open','extra':0}],False])
        if c['id']=='confirm-api-optional-range':c['private']['checks'].append([{'version':2,'extra':0},False])
    return s


def inventory():
    rows=cases()
    return dict(schema='rr-worker-cases-v1', cases=rows, case_set_id=digest(rows),
        evidence='authored_synthetic_not_model_results', membership_frozen_before_A=True,
        confirmation='held_back_for_selection_not_final_benchmark', model_executed=False)


def action(case, negative=False):
    return dict(tool='publish',name='report',format=case['public']['required_outputs'][0]['format'],
        content=deepcopy(case['private']['mutant' if negative else 'reference']),bindings={},obligations=['report'])


def environment(case, resources):
    from .runtime import Environment
    p=deepcopy(case['public']);fmt=p['required_outputs'][0]['format']
    u=dict(id='report',worker='w0',outputs=['report'],depends=[],consumes={},produces={'report':fmt},
        terminal_bindings={'report':'report'},sources=sorted(p['sources']),interfaces={'report':p['request']},description='Publish one assigned artifact.')
    env=Environment(p,resources=resources,workers=tuple('w'+str(i) for i in range(7)),
        execution_contract='plan_scoped_v1',plan=dict(id='synthetic',schema='rr-work-plan-v2',units=[u]),
        interface_profile='rr-interface-reliability-v1')
    env.scopes.begin(u,'w0','primary');env.assignment['w0']=u
    return env


def evaluate(case, env):
    """Isolated-obligation projection; never the complete multi-output scorer."""
    from .common import Rejected
    fmt=case['public']['required_outputs'][0]['format']; checks=[]
    inputs=case['private'].get('checks', [[{},case['private'].get('expected')]])
    for value,expected in inputs:
        result=env.execute(env.bound['report'],value)
        if result['status']=='blocked_prerequisite':raise Rejected('blocked_prerequisite')
        if fmt=='sql':
            outputs=result.get('outputs',[])
            correct=(result['status']=='ok' and len(outputs)==1 and outputs[0]['columns']==expected['columns'] and
                sorted(outputs[0]['rows'],key=repr)==sorted(expected['rows'],key=repr))
        elif fmt=='schema':correct=result.get('status')=='ok' and result.get('valid') is expected
        else:correct=result.get('status')=='ok' and 'output' in result and digest(result['output'])==digest(expected)
        checks.append(dict(execution_status=result['status'],correct=correct))
    return dict(projection='single_artifact_obligation_v1',correct=all(x['correct'] for x in checks),checks=checks)
