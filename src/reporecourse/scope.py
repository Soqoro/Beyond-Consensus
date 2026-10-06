"""Assignment-scoped mediation for the opt-in plan_scoped_v1 contract.

The trusted engine admits assignments/overlays. Workers cannot grant permissions.
All public originals remain available. No semantic noninterference claim.
"""
from copy import deepcopy
from .common import Rejected, digest

CONTRACT='plan_scoped_v1'
JIT='rr-common-scoped-jit-v1'


def walk_versions(artifacts,version,with_exposure=False):
    visited=set();visiting=set();pending=[(version,False)]
    while pending:
        v,leaving=pending.pop()
        if leaving:visiting.remove(v);visited.add(v);continue
        if v in visiting or v not in artifacts:raise Rejected('scope_integrity')
        if v in visited:continue
        visiting.add(v);pending.append((v,True))
        a=artifacts[v];deps=set(a['bindings'].values())
        if with_exposure:deps.update(a.get('exposure',[]))
        pending.extend((x,False) for x in sorted(deps))
    return visited


def closure(artifacts,version):
    return walk_versions(artifacts,version)


def influence(artifacts,version):
    return walk_versions(artifacts,version,True)


def validate_bundle(state, roots=None):
    """Validate publication receipts and exact version closure before grading.

    Receipts are trusted runtime records, not cryptographic remote attestation.
    Only explicit publications can be bound; a safe unsubmitted program is absent.
    """
    if state.get('execution_contract')!=CONTRACT:return
    artifacts=state['artifacts'];scope=state.get('scope_state',{})
    receipts=scope.get('receipts',{});scopes=scope.get('records',{})
    for root in (state['bound'].values() if roots is None else roots):
        for v in closure(artifacts,root):
            a=artifacts[v];receipt=receipts.get(v);s=scopes.get(a.get('scope_id'))
            if not receipt or not s or digest(a)!=v or receipt['artifact_hash']!=v or digest({k:x for k,x in s.items() if k!='id'})!=s['id']:
                raise Rejected('scope_integrity')
            own={k for k,b in artifacts.items() if b.get('scope_id')==a['scope_id'] and b['sequence']<a['sequence']}
            allowed=set(s['imports'].values())|set(s.get('recovery_versions',[]))|own
            if not set(a['bindings'].values())<=allowed:raise Rejected('scope_integrity')
            ancestry=set(allowed)
            for p in allowed:ancestry|=influence(artifacts,p)
            # Message/context provenance is mediated and retained separately.
            if not set(a.get('exposure',[]))<=ancestry:raise Rejected('scope_integrity')
    for obligation,v in (state['bound'].items() if roots is None else []):
        a=artifacts[v];s=scopes[a['scope_id']]
        if obligation not in s['outputs'] or a['name']!=s['terminal_bindings'][obligation]:raise Rejected('scope_integrity')


class AssignmentScopes:
    def __init__(self,env,plan):
        self.env=env;self.plan=deepcopy(plan)
        self.data={'coverage':'mediated-v1','plan_hash':digest(plan),'records':{},'active':{},
                   'receipts':{},'messages':[],'checkpoints':{},'overlays':[]}

    def current(self,worker):
        sid=self.data['active'].get(worker)
        if sid is None:raise Rejected('scope_denied')
        return self.data['records'][sid]

    def deny(self,worker,surface):
        s=self.current(worker)
        self.env.events.append(dict(type='scope_denied',worker=worker,unit=s['unit'],stage=s['stage'],scope_id=s['id'],surface=surface))
        raise Rejected('scope_denied')

    def begin(self,unit,worker,stage):
        """Deterministic admission. A changed repair scope gets fresh context."""
        env=self.env
        current=self.data['records'].get(self.data['active'].get(worker),{})
        if current.get('unit')==unit['id'] and current.get('stage')==stage:return False
        imports={}
        for alias,entry in unit.get('consumes',{}).items():
            choices=[(v,a) for v,a in env.artifacts.items() if a.get('producer_unit')==entry['unit'] and a['name']==entry['artifact']]
            if choices:imports[alias]=max(choices,key=lambda x:x[1]['sequence'])[0]
        recover=[];trigger=None
        if stage=='repair':
            triggers=[(i,e) for i,e in enumerate(env.events) if e['type'] in ('unavailable','public_alarm')]
            if not triggers:raise Rejected('recovery_trigger_required')
            index,event=triggers[-1]
            trigger={'event_index':index,'event_type':event['type'],
                     'public_evidence':deepcopy(event.get('announcement',{'obligations':event.get('obligations',[])}))}
            # Same unit revisions plus current explicit predecessors only. No
            # all-artifact escape. Original sources allow direct reconstruction.
            recover=[v for v,a in env.artifacts.items() if a.get('producer_unit')==unit['id']]
        elif stage!='primary':raise Rejected('scoped_stage')
        s=dict(unit=unit['id'],worker=worker,stage=stage,imports=imports,produces=deepcopy(unit['produces']),
               outputs=list(unit['outputs']),terminal_bindings=deepcopy(unit.get('terminal_bindings',{o:o for o in unit['outputs']})),predecessors=list(unit['depends']),sources=sorted(env.public['sources']),
               recovery_versions=sorted(recover),context_imports=[],trigger=trigger,
               resolution='latest-at-admission-v1',sequence=len(self.data['records']))
        sid=digest(s);s['id']=sid
        self.data['records'][sid]=s;self.data['active'][worker]=sid
        env.exposure[worker]=set()
        if trigger:
            overlay={'revision_id':sid,'policy':JIT,**deepcopy(s)}
            self.data['overlays'].append(overlay);env.events.append({'type':'recovery_overlay',**overlay})
        env.events.append(dict(type='context_reset',worker=worker,unit=unit['id'],stage=stage,scope_id=sid,
                               reason='assignment_local_no_history_inheritance',identity_unavailable=worker in env.unavailable))
        return True

    def allowed(self,worker):
        s=self.current(worker)
        own={v for v,a in self.env.artifacts.items() if a.get('scope_id')==s['id']}
        return own|set(s['imports'].values())|set(s['recovery_versions'])

    def version(self,worker,version,surface):
        if version not in self.allowed(worker):self.deny(worker,surface)
        validate_bundle(self.env.state(),roots=[version])

    def delivery(self,worker,versions,surface):
        s=self.current(worker);versions=set(versions)
        if not versions<=self.allowed(worker):self.deny(worker,surface)
        validate_bundle(self.env.state(),roots=versions)
        inherited=set()
        for v in versions:inherited |= influence(self.env.artifacts,v)
        self.env.exposure[worker].update(inherited)
        self.env.events.append(dict(type='scope_delivery',worker=worker,unit=s['unit'],stage=s['stage'],scope_id=s['id'],
                                   surface=surface,direct_versions=sorted(versions),transitive_versions=sorted(inherited-versions)))

    def observation(self,worker,value):
        s=self.current(worker);allowed=self.allowed(worker)
        value['artifacts']=[x for x in value['artifacts'] if x['version'] in allowed]
        value['bound']={k:v for k,v in value['bound'].items() if k in s['outputs'] and v in allowed}
        messages=[]
        for m in self.data['messages']:
            if m['recipient_unit']!=s['unit'] or m['producer_unit'] not in s['predecessors']:continue
            # Do not deliver an unbound producer's free text or unrelated exposure.
            ancestry=set()
            for v in allowed:ancestry |= influence(self.env.artifacts,v)
            if set(m['exposure'])<=ancestry:
                messages.append(deepcopy(m));self.env.exposure[worker].update(m['exposure'])
        value['messages']=messages
        value['execution_scope']={k:deepcopy(s[k]) for k in ('id','unit','stage','imports','produces','outputs','sources')}
        value['execution_scope']['contract']=CONTRACT
        value['execution_scope']['instructions']='Only own and imported versions are accessible. Source focus is a hint. Messages require a declared predecessor. Grouped outputs share this context; other assignments start fresh.'
        # Public loss announcements are fixed trusted coordination facts only.
        value['announcements']=[{k:e[k] for k in ('worker','unavailable','assignment') if k in e} for e in value['announcements']]
        self.delivery(worker,[x['version'] for x in value['artifacts']],'metadata')
        self.env.events.append(dict(type='scope_observation',worker=worker,unit=s['unit'],stage=s['stage'],scope_id=s['id'],
            observation_hash=digest(value),visible_versions=sorted(allowed),message_hashes=[digest(m) for m in messages]))
        return value

    def authorize(self,worker,action):
        """Single entry for all worker-facing tools. Unknown tools fail elsewhere."""
        s=self.current(worker);tool=action.get('tool')
        if tool in ('read_artifact','execute_artifact','rebind_artifact','bind_output'):
            self.version(worker,action.get('version'),tool)
        if tool in ('publish','rebind_artifact'):
            name=action.get('name');obligations=action.get('obligations',[])
            if name not in s['produces'] or not set(obligations)<=set(s['outputs']):self.deny(worker,'publication')
            if any(s['terminal_bindings'][o]!=name for o in obligations):self.deny(worker,'terminal_mapping')
            fmt=action.get('format') if tool=='publish' else self.env.artifacts[action['version']]['format']
            if ('sql' if fmt=='select' else fmt)!=s['produces'][name]:self.deny(worker,'publication')
            bindings=action.get('bindings',{})
            if not isinstance(bindings,dict):self.deny(worker,'bindings')
            for v in bindings.values():self.version(worker,v,'bindings')
        if tool=='bind_output':
            a=self.env.artifacts[action['version']]
            if action.get('obligation') not in s['outputs'] or a.get('producer_unit')!=s['unit'] or a['name']!=s['terminal_bindings'][action['obligation']]:self.deny(worker,'output_binding')
        if tool=='message':
            receiver=action.get('recipient')
            candidates=[u for u in self.plan['units'] if u['worker']==receiver and s['unit'] in u['depends']]
            if not candidates:self.deny(worker,'message')
        if tool=='restore':
            cp=self.data['checkpoints'].get(action.get('checkpoint'))
            if not cp or cp['scope_id']!=s['id']:self.deny(worker,'checkpoint')

    def special(self,worker,action):
        s=self.current(worker);env=self.env;tool=action['tool']
        if tool=='message':
            if not isinstance(action['text'],str) or len(action['text'])>4096:self.deny(worker,'message')
            for u in self.plan['units']:
                if u['worker']==action['recipient'] and s['unit'] in u['depends']:
                    self.data['messages'].append(dict(sender=worker,producer_unit=s['unit'],recipient_unit=u['id'],
                        text=action['text'],scope_id=s['id'],exposure=sorted(env.exposure[worker]|self.allowed(worker))))
            env.events.append(dict(type='message',worker=worker,unit=s['unit'],scope_id=s['id'],recipient=action['recipient']))
            return True,{'delivered':True}
        if tool=='check_public':return True,env.check_public(only=s['outputs'])
        if tool=='checkpoint':
            k=digest([s['id'],len(self.data['checkpoints'])]);self.data['checkpoints'][k]={'scope_id':s['id'],
                'bound':{o:env.bound[o] for o in s['outputs'] if o in env.bound}}
            return True,{'checkpoint':k}
        if tool=='restore':
            cp=self.data['checkpoints'][action['checkpoint']]
            for o in s['outputs']:env.bound.pop(o,None)
            env.bound.update(cp['bound']);return True,{'restored':True}
        return False,None

    def seal(self,worker,record):
        s=self.current(worker)
        record.update(producer_unit=s['unit'],stage=s['stage'],scope_id=s['id'])

    def published(self,version):
        self.data['receipts'][version]={'artifact_hash':version}

    def restore(self,data):
        if data.get('plan_hash')!=digest(self.plan):raise Rejected('scope_resume_mismatch')
        self.data=deepcopy(data)
