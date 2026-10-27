"""Read the supplied restricted YAML template without third-party imports.

Only indentation mappings, scalar lists and scalar values used by the supplied
file are supported. This is not a general YAML loader; tags/anchors fail closed.
"""
from pathlib import Path
import json
from .model import Invalid


def load(path):
    text=Path(path).read_text()
    if str(path).endswith('.json'):return json.loads(text)
    rows=[]
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'):continue
        if '\t' in raw or any(x in raw for x in ('!!','&','*')) and '2*n' not in raw:raise Invalid('unsupported YAML syntax')
        rows.append((len(raw)-len(raw.lstrip()),raw.strip()))
    def scalar(v):
        if v in ('true','false','null','{}','[]'):return json.loads(v)
        if v[:1] in ('"',"'"):
            if len(v)<2 or v[-1]!=v[0]:raise Invalid('quoted scalar')
            return v[1:-1]
        if v.lstrip('-').isdigit():return int(v)
        return v
    def block(pos,indent):
        islist=rows[pos][1].startswith('- ');result=[] if islist else {}
        while pos<len(rows) and rows[pos][0]==indent:
            value=rows[pos][1]
            if islist:
                if not value.startswith('- '):break
                result.append(scalar(value[2:]));pos+=1
            else:
                if value.startswith('- ') or ':' not in value:raise Invalid('mapping expected')
                key,tail=value.split(':',1);tail=tail.strip()
                if key in result:raise Invalid('duplicate template key')
                pos+=1
                if tail:result[key]=scalar(tail)
                elif pos<len(rows) and (rows[pos][0]>indent or rows[pos][0]==indent and rows[pos][1].startswith('- ')):
                    result[key],pos=block(pos,rows[pos][0])
                else:result[key]=None
        return result,pos
    value,end=block(0,rows[0][0])
    if end!=len(rows):raise Invalid('template trailing syntax')
    return value
