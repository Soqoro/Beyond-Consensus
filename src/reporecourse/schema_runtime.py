"""Bounded Draft 2020-12 subset and field mapping, executed in a trusted child.

No automatic retrieval. Reference names resolve ONLY from an explicit versioned
artifact registry. Unknown keywords, regex, formats, code and cycles are rejected.
"""
import json
import subprocess
import sys
import time
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reporecourse.common import Rejected, bounded, ident

VERSIONS = {'jsonschema': '4.25.1', 'referencing': '0.36.2'}
KEYWORDS = {'type','properties','required','additionalProperties','items','minItems','maxItems',
            'enum','const','minimum','maximum','minLength','maxLength','$ref'}
TYPES = {'object','array','string','integer','number','boolean','null'}


def resolve(schema, registry, chain=(), depth=0, counter=None):
    counter = [0] if counter is None else counter
    counter[0] += 1
    if depth > 16 or counter[0] > 400: raise Rejected('schema_complexity')
    if type(schema) is bool: return schema
    if not isinstance(schema, dict) or set(schema)-KEYWORDS: raise Rejected('schema_keyword')
    if '$ref' in schema:
        ref = schema['$ref']
        if set(schema) != {'$ref'} or not isinstance(ref, str) or not ref.startswith('rr:'):
            raise Rejected('schema_reference')
        name = ident(ref[3:])
        if name in chain or name not in registry: raise Rejected('schema_reference')
        return resolve(registry[name], registry, chain+(name,), depth+1, counter)
    result = dict(schema)
    types = schema.get('type', [])
    if isinstance(types, str): types = [types]
    if not isinstance(types, list) or any(x not in TYPES for x in types): raise Rejected('schema_type')
    for k in ('minItems','maxItems','minLength','maxLength'):
        if k in schema and (type(schema[k]) is not int or not 0 <= schema[k] <= 4096):
            raise Rejected('schema_bound')
    if 'properties' in schema:
        props = schema['properties']
        if not isinstance(props, dict) or len(props)>64: raise Rejected('schema_properties')
        result['properties'] = {ident(k):resolve(v, registry, chain, depth+1,counter) for k,v in props.items()}
    if 'required' in schema:
        if not isinstance(schema['required'],list) or len(set(schema['required'])) != len(schema['required']): raise Rejected('schema_required')
        for key in schema['required']: ident(key)
    for k in ('items','additionalProperties'):
        if k in schema: result[k] = resolve(schema[k],registry,chain,depth+1,counter)
    return result


def validate(schema, value, registry):
    # Local expansion audits all refs before the validator. Registry independently
    # denies retrieval, even if later implementation changes pass a ref through.
    from jsonschema import Draft202012Validator
    from referencing import Registry
    from referencing.exceptions import NoSuchResource
    def deny(uri): raise NoSuchResource(ref=uri)
    expanded = resolve(schema, registry)
    Draft202012Validator.check_schema(expanded)
    return Draft202012Validator(expanded, registry=Registry(retrieve=deny)).is_valid(value)


def mapping(program, value, depth=0):
    if depth>8 or not isinstance(program,dict) or set(program)-{'fields','each','output_schema'}:
        raise Rejected('mapping_contract')
    if 'each' in program:
        if 'fields' in program or not isinstance(value,list) or len(value)>128: raise Rejected('mapping_array')
        return [mapping(program['each'],item,depth+1) for item in value]
    if 'fields' not in program or not isinstance(program['fields'],dict) or len(program['fields'])>64:
        raise Rejected('mapping_fields')
    out = {}
    for name,op in program['fields'].items():
        ident(name)
        if not isinstance(op,dict) or set(op) != {'path','missing'} or op['missing'] not in ('error','omit','null'):
            raise Rejected('mapping_operation')
        if not isinstance(op['path'],list) or not 1<=len(op['path'])<=8: raise Rejected('mapping_path')
        current=value; missing=False
        for key in op['path']:
            ident(key)
            if not isinstance(current,dict) or key not in current: missing=True; break
            current=current[key]
        if missing:
            if op['missing']=='error': raise Rejected('mapping_missing')
            if op['missing']=='omit':continue
            current=None
        out[name]=current
    return out


def child(request):
    from importlib.metadata import version
    if any(version(k)!=v for k,v in VERSIONS.items()): raise ImportError('version')
    bounded(request, size=262144)
    registry=request.get('registry',{})
    if len(registry)>32: raise Rejected('registry_size')
    for k,v in registry.items(): ident(k); resolve(v,registry)
    if request['operation']=='validate':
        return {'status':'ok','valid':validate(request['schema'],request['value'],registry)}
    if request['operation']=='map':
        out=mapping(request['program'],request['value'])
        bounded(out, size=65536)
        if not validate(request['program']['output_schema'],out,registry):
            return {'status':'ok','valid':False}
        return {'status':'ok','valid':True,'output':out}
    if request['operation']=='qualify':
        return {'status':'ok','versions':VERSIONS,'dialect':'2020-12','retrieval':False}
    raise Rejected('schema_operation')


def execute(request):
    bounded(request,size=262144)
    start=time.monotonic()
    try:
        proc=subprocess.run([sys.executable,'-I',str(Path(__file__).resolve()),'--child'],
            input=json.dumps(request,allow_nan=False),text=True,capture_output=True,timeout=6,cwd='/tmp',
            env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
        report=json.loads(proc.stdout) if proc.returncode==0 else {'status':'execution_limit','cpu_seconds':None}
    except subprocess.TimeoutExpired:report={'status':'execution_limit','cpu_seconds':None}
    report['wall_seconds']=time.monotonic()-start
    return report


if __name__=='__main__':
    # Direct script execution bootstraps only trusted source; no candidate paths.
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(3,3))
    resource.setrlimit(resource.RLIMIT_AS,(268435456,268435456))
    resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
    start=time.process_time()
    try: report=child(json.loads(sys.stdin.read(262145)))
    except ImportError: report={'status':'blocked_prerequisite','category':'pinned_validator_unavailable'}
    except Exception: report={'status':'rejected','category':'schema_or_mapping_rejected'}
    report['cpu_seconds']=time.process_time()-start
    print(json.dumps(report,allow_nan=False))
