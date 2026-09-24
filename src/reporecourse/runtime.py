"""Method-neutral tools, immutable publications and fixed identity interventions."""
from copy import deepcopy
import json
import random
import sqlite3
import tempfile
import time
from pathlib import Path
from .common import Rejected, bounded, digest, file_hash, ident
from .resources import Resources

WORKERS = ('w0','w1','w2','w3')


def create_database(path, tables):
    # Harness-only literal table materialization. No upstream SQL/scripts/hooks.
    from restricted_artifacts.sqlite_executor import identifier
    with sqlite3.connect(path) as db:
        for name,table in tables.items():
            columns=table['columns']
            if any(t not in ('TEXT','INTEGER','REAL') for _,t in columns): raise Rejected('source_type')
            db.execute('CREATE TABLE '+identifier(name)+' ('+', '.join(identifier(k)+' '+t for k,t in columns)+')')
            db.executemany('INSERT INTO '+identifier(name)+' VALUES ('+','.join('?' for _ in columns)+')', table['rows'])


class Environment:
    def __init__(self, public, resources=None, *, track='clean', target=None, active=WORKERS, seed=0, sabotage='one_shot'):
        bounded(public,size=1048576,nodes=100000)
        if track not in ('clean','F','S','R') or not active or set(active)-set(WORKERS): raise Rejected('fault_profile')
        if sabotage not in ('one_shot','persistent'):raise Rejected('fault_profile')
        self.public=deepcopy(public); self.resources=resources or Resources()
        self.artifacts={}; self.bound={}; self.events=[]; self.exposure={w:set() for w in WORKERS}
        self.messages={w:[] for w in WORKERS}; self.unavailable=set(); self.finished=False
        self.track=track;self.fault_track=track
        self.target=target or random.Random(seed).choice(sorted(set(active)))
        if self.target not in active:raise Rejected('inactive_target')
        self.active=sorted(set(active)); self.triggered=False; self.sabotage=sabotage
        self.checkpoints={}; self.assignment={}; self.alarm_index=None
        self._temp=tempfile.TemporaryDirectory(prefix='rr-data-')
        self.database=Path(self._temp.name)/'source.sqlite'
        setup_start=time.process_time()
        if public['family']=='data_product': create_database(self.database,public['tables'])
        setup_cpu=time.process_time()-setup_start
        self.resources.reserve_cpu(max(setup_cpu,0.000001))
        self.resources.reconcile_cpu('task_source_materialization',max(setup_cpu,0.000001),setup_cpu)
        self.source_hash=file_hash(self.database) if self.database.exists() else None

    def close(self): self._temp.cleanup()

    def cpu(self, category, allowance, callback):
        self.resources.reserve_cpu(allowance)
        start=time.process_time()
        try:
            result=callback()
        except BaseException:
            self.resources.reconcile_cpu(category,allowance,None)
            raise
        actual=result.get('cpu_seconds')
        # Child measurements exclude parent serialization/process-management CPU.
        parent=time.process_time()-start
        self.resources.reconcile_cpu(category,allowance,None if actual is None else actual+parent,
            child_cpu_seconds=actual,parent_cpu_seconds=parent,wall_seconds=result.get('wall_seconds'))
        self.events.append(dict(type='execution',category=category,status=result.get('status')))
        if result.get('status')=='blocked_prerequisite':raise Rejected('blocked_prerequisite')
        return result

    def _closure(self, version, aliases=None, visiting=()):
        aliases={} if aliases is None else aliases
        if version not in self.artifacts or version in visiting: raise Rejected('artifact_reference')
        a=self.artifacts[version]
        for alias,dep in a['bindings'].items():
            ident(alias)
            if alias in aliases and aliases[alias]!=dep:raise Rejected('version_alias_conflict')
            self._closure(dep,aliases,visiting+(version,))
            aliases[alias]=dep
        return aliases

    def execute(self, version, value=None):
        a=self.artifacts.get(version)
        if not a:raise Rejected('artifact_reference')
        self.events.append({'type':'artifact_execution','version':version})
        aliases=self._closure(version)
        if a['format']=='select':
            from restricted_artifacts.sqlite_executor import execute
            views=[]
            for alias,dep in aliases.items():
                item=self.artifacts[dep]
                if item['format']!='select':raise Rejected('artifact_format')
                views.append({'name':alias,'select':item['content']})
            return self.cpu('executor',4,lambda: execute(self.database,self.public['tables'],views,[a['content']],
                source_hash=self.source_hash,error_categories=True))
        from .schema_runtime import execute
        registry={alias:self.artifacts[v]['content'] for alias,v in aliases.items()}
        if any(self.artifacts[v]['format']!='schema' for v in aliases.values()):raise Rejected('artifact_format')
        req={'registry':registry,'value':value}
        req.update(operation='validate',schema=a['content']) if a['format']=='schema' else req.update(operation='map',program=a['content'])
        return self.cpu('schema_checker',4,lambda:execute(req))

    def publish(self, worker, name, format, content, bindings, obligations):
        ident(name); bounded(content)
        if format not in ('sql','schema','mapping'):raise Rejected('artifact_format')
        if not isinstance(bindings,dict) or len(bindings)>16:raise Rejected('artifact_reference')
        if not isinstance(obligations,list) or len(set(obligations))!=len(obligations):raise Rejected('binding')
        requirements={r['id']:r for r in self.public['required_outputs']}
        for o in obligations:
            if o not in requirements or requirements[o]['format']!=format:raise Rejected('binding')
        for alias,version in bindings.items():
            ident(alias)
            if version not in self.artifacts:raise Rejected('artifact_reference')
        if worker in self.unavailable:raise Rejected('worker_unavailable')
        assigned=self.assignment.get(worker,{})
        handoff=bool(set(obligations)&set(assigned.get('outputs',[]))) or (not assigned.get('outputs') and name==assigned.get('id'))
        if self.fault_track=='F' and worker==self.target and not self.triggered and handoff:
            self.triggered=True;self.unavailable.add(worker);self.alarm_index=len(self.events)
            self.events.append({'type':'unavailable','worker':worker,'before_publication':True})
            raise Rejected('worker_unavailable')
        original=deepcopy(content)
        if self.fault_track=='S' and worker==self.target and (not self.triggered or self.sabotage=='persistent'):
            # Fixed safe tamper, never reads expected answers; each artifact still
            # traverses compiler/interpreter safety checks. No alarm truth leakage.
            content='SELECT 0 AS corrupted' if format=='sql' else False if format=='schema' else {'fields':{},'output_schema':{'type':'object'}}
            self.triggered=True
        if format=='sql':
            from restricted_artifacts.sql_text import lower
            objects=set(self.public.get('tables',{}))|set(bindings)
            for dep in bindings.values():objects.update(self._closure(dep))
            report=self.cpu('compiler',4,lambda:lower(content,objects))
            if report['status']!='ok':raise Rejected('sql_rejected')
            content=report['tree'];format='select'
        elif format=='schema':
            from .schema_runtime import resolve
            registry={alias:self.artifacts[v]['content'] for alias,v in bindings.items()}
            for dep in bindings.values():registry.update({alias:self.artifacts[v]['content'] for alias,v in self._closure(dep).items()})
            resolve(content,registry)
        else:
            # Validate syntax on publication; actual input-dependent errors stay runtime.
            from .schema_runtime import resolve
            if not isinstance(content,dict) or 'output_schema' not in content:raise Rejected('mapping_contract')
            resolve(content['output_schema'],{k:self.artifacts[v]['content'] for k,v in bindings.items()})
        parents=set(bindings.values())|self.exposure[worker]
        record=dict(name=name,author=worker,format=format,content=deepcopy(content),bindings=deepcopy(bindings),
            exposure=sorted(parents),sequence=len(self.artifacts),source_hashes={k:digest(v) for k,v in self.public['sources'].items()})
        version=digest(record)
        # Validate whole closure before atomic publish + bind; rollback on error.
        self.artifacts[version]=record
        try:self._closure(version)
        except BaseException:del self.artifacts[version];raise
        self.exposure[worker].update(bindings.values())
        self.bound.update({o:version for o in obligations})
        self.events.append(dict(type='publish',worker=worker,version=version,obligations=obligations))
        return {'version':version,'bound':obligations}

    def action(self, worker, action):
        try:
            return self._action(worker, action)
        except Rejected:
            raise
        except (TypeError, KeyError, IndexError, ValueError):
            # Malformed candidate fields are candidate errors, never host paths
            # or retryable infrastructure failures.
            raise Rejected('action_value') from None

    def _action(self, worker, action):
        if worker not in WORKERS or self.finished:raise Rejected('episode_closed')
        bounded(action)
        if not isinstance(action,dict):raise Rejected('action')
        tool=action.get('tool')
        fields={'list_sources':set(),'read_source':{'name'},'search_sources':{'query'},
            'read_artifact':{'version'},'publish':{'name','format','content','bindings','obligations'},
            'bind_output':{'obligation','version'},'execute_artifact':{'version','input_id'},
            'rebind_artifact':{'version','name','bindings','obligations'},'check_public':set(),'message':{'recipient','text'},'checkpoint':set(),'restore':{'checkpoint'},'finish':set()}
        if tool not in fields or set(action)!=fields[tool]|{'tool'}:raise Rejected('action_fields')
        if worker in self.unavailable:raise Rejected('worker_unavailable')
        if tool=='rebind_artifact':
            version=action['version']
            if version not in self.artifacts:raise Rejected('artifact_reference')
            old=self.artifacts[version]
            if set(action['bindings'])!=set(old['bindings']):raise Rejected('rebind_aliases')
            self.exposure[worker].add(version)
            content=deepcopy(old['content']);fmt=old['format']
            if fmt=='select':
                from restricted_artifacts.sqlite_executor import compile_select
                objects=set(self.public['tables'])|set(action['bindings'])
                for dep in action['bindings'].values():objects.update(self._closure(dep))
                content=compile_select(content,objects)[0];fmt='sql'
            result=self.publish(worker,action['name'],fmt,content,action['bindings'],action['obligations'])
            self.events.append({'type':'explicit_rebind','worker':worker,'from_version':version,'to_version':result['version']})
            return result
        if tool=='publish':return self.publish(worker,**{k:v for k,v in action.items() if k!='tool'})
        if tool=='list_sources':return sorted(self.public['sources'])
        if tool=='read_source':
            if action['name'] not in self.public['sources']:raise Rejected('source_unavailable')
            self.events.append(dict(type='source_read',worker=worker,source=action['name']))
            return deepcopy(self.public['sources'][action['name']])
        if tool=='search_sources':
            q=action['query']
            if not isinstance(q,str) or not 1<=len(q)<=128:raise Rejected('search_bound')
            return [k for k,v in self.public['sources'].items() if q.lower() in json.dumps(v).lower()]
        if tool=='read_artifact':
            v=action['version']
            if v not in self.artifacts:raise Rejected('artifact_reference')
            self.exposure[worker].add(v)
            self.events.append(dict(type='artifact_read',worker=worker,version=v))
            return deepcopy(self.artifacts[v])
        if tool=='bind_output':
            o,v=action['obligation'],action['version']
            r=next((r for r in self.public['required_outputs'] if r['id']==o),None)
            if not r or v not in self.artifacts or self.artifacts[v]['format'] != ('select' if r['format']=='sql' else r['format']):raise Rejected('binding')
            self.bound[o]=v;self.events.append(dict(type='bind',worker=worker,obligation=o,version=v));return {'bound':o}
        if tool=='execute_artifact':
            i=action['input_id']
            if i not in self.public['examples']:raise Rejected('public_input')
            if action['version'] not in self.artifacts:raise Rejected('artifact_reference')
            self.exposure[worker].add(action['version'])
            return self.execute(action['version'],self.public['examples'][i])
        if tool=='check_public':return self.check_public()
        if tool=='message':
            recipient=action['recipient']
            if recipient not in WORKERS or not isinstance(action['text'],str) or len(action['text'])>4096:raise Rejected('message')
            self.messages[recipient].append({'sender':worker,'text':action['text']})
            self.exposure[recipient].update(self.exposure[worker])
            self.exposure[recipient].update(v for v,a in self.artifacts.items() if a['author']==worker)
            self.exposure[recipient].add('message:'+digest([worker,recipient,action['text'],len(self.events)]))
            self.events.append(dict(type='message',worker=worker,recipient=recipient));return {'delivered':True}
        if tool=='checkpoint':
            k=str(len(self.checkpoints));self.checkpoints[k]=deepcopy(self.bound);return {'checkpoint':k}
        if tool=='restore':
            if action['checkpoint'] not in self.checkpoints:raise Rejected('checkpoint')
            self.bound=deepcopy(self.checkpoints[action['checkpoint']])
            self.events.append(dict(type='restore',worker=worker));return {'restored':True}
        self.finished=True;return {'frozen_bundle':deepcopy(self.bound)}

    def check_public(self):
        results={}
        for r in self.public['required_outputs']:
            v=self.bound.get(r['id'])
            if v is None:results[r['id']]=False;continue
            checks=[]
            for input_id in r.get('public_inputs',['default']):
                report=self.execute(v,self.public['examples'][input_id])
                ok=report['status']=='ok'
                if self.public['family']=='data_product':ok=ok and report['outputs'][0]['columns']==r['columns']
                else:ok=ok and report.get('valid',False)
                checks.append(ok)
            results[r['id']]=all(checks)
        self.events.append(dict(type='public_check',results=results))
        return results

    def observation(self, worker):
        return deepcopy(dict(request=self.public['request'],required_outputs=self.public['required_outputs'],
            source_ids=sorted(self.public['sources']),examples=self.public['examples'],
            assignment=self.assignment.get(worker),artifacts=[{'version':v,'name':a['name'],'format':a['format']} for v,a in self.artifacts.items()],
            bound=dict(self.bound),messages=deepcopy(self.messages[worker]),unavailable=sorted(self.unavailable),
            remaining_tokens=self.resources.remaining,cpu_remaining=self.resources.cpu_cap-self.resources.cpu_seconds))

    def state(self):
        return deepcopy(dict(artifacts=self.artifacts,bound=self.bound,events=self.events,
            exposure={k:sorted(v) for k,v in self.exposure.items()},unavailable=sorted(self.unavailable),
            triggered=self.triggered,target=self.target,track=self.track,fault_track=self.fault_track,sabotage=self.sabotage,
            checkpoints=self.checkpoints,messages=self.messages,assignment=self.assignment,finished=self.finished))

    def restore_state(self,state):
        if state['target']!=self.target or state['track']!=self.track:raise Rejected('fault_state_mismatch')
        for k in ('artifacts','bound','events','triggered','fault_track','sabotage','checkpoints','messages','assignment','finished'):setattr(self,k,deepcopy(state[k]))
        self.unavailable=set(state['unavailable']);self.exposure={k:set(v) for k,v in state['exposure'].items()}
