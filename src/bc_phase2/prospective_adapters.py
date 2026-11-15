"""Thin public/private source adapters; no network, model or medical adjudication."""
from copy import deepcopy
from itertools import permutations
import re
from .model import digest, Invalid
from .joint_schema import require, decode
from . import d1_natural_screen as natural, medqa_development as medqa
from .prospective_sources import faithful_identity

LABELS=tuple('ABCD')

def integer(raw):
    require(type(raw) is str and re.fullmatch(r'[0-9]{1,3}',raw.strip()) is not None,
            'one ASCII integer string 0..999')
    return int(raw.strip())

def aime(row, year, revision, row_id):
    require(year in (2025,2026) and type(revision) is str and revision and str(row_id), 'year/release/row binding')
    require(type(row.get('problem')) is str and row['problem'].strip(), 'problem text')
    require(type(row.get('problem_idx')) in (int,str), 'actual package problem_idx required')
    sid=f'aime/{year}/{revision}/row/{row_id}'
    public={'id':sid,'problem':row['problem']}
    key=row.get('answer')
    try:value=integer(str(key) if type(key) is int else key);status='known'
    except Invalid:value=None;status='unknown_reference'
    meta={'year':year,'revision':revision,'row_id':str(row_id),'problem_idx':row['problem_idx'],
          'original_contest_id':row.get('contest_id'),'sitting':row.get('sitting'),
          'problem_type':row.get('problem_type'),'identity_hashes':faithful_identity(public)}
    private={'id':sid,'public_digest':digest(public),'status':status,'integer':value}
    return public,private,meta

def medqa_record(row, identity):
    public=medqa.public_record(row,identity)
    require(len(set(' '.join(v.split()) for v in public['options'].values()))==4, 'distinct options')
    return public,medqa.protected_record(row,identity,public)

def gpqa(row, provenance):
    require(provenance.get('configuration')=='gpqa_diamond' and provenance.get('revision')
            and provenance.get('repository')=='Idavidrein/gpqa', 'exact Diamond provenance')
    question=row.get('Question')
    texts=[row.get(k) for k in ('Correct Answer','Incorrect Answer 1','Incorrect Answer 2','Incorrect Answer 3')]
    require(type(question) is str and question.strip(), 'question')
    require(all(type(t) is str and t.strip() for t in texts), 'four nonempty options')
    require(len(set(' '.join(t.split()) for t in texts))==4, 'distinct unambiguous options')
    # Public identity and canonical order never depend on correctness-bearing columns.
    canonical=sorted(texts)
    identity=digest([question,canonical])
    seed=digest(['gpqa-public-option-map-v1',provenance['repository'],provenance['revision'],identity])
    order=list(permutations(range(4)))[int(seed,16)%24]
    options={label:canonical[i] for label,i in zip(LABELS,order)}
    sid='gpqa/diamond/'+identity
    public={'id':sid,'question':question,'options':options}
    private={'id':sid,'public_digest':digest(public),'status':'known',
             'correct_option':next(k for k,v in options.items() if v==row['Correct Answer'])}
    return public,private,{'content_id':identity,'provenance':deepcopy(provenance),
                           'option_map_digest':digest(options),'alias_review':'pending'}

def planner_request(dataset, public):
    if dataset in ('math500','aime2025','aime2026'):return natural.request(public)
    require(dataset in ('medqa','gpqa'), 'known dataset')
    medqa.assert_public(public)
    if dataset=='medqa':return medqa.planner_request(public)
    p=medqa.planner_request(public)['payload']
    p['prompt']=p['prompt'].replace('exam-question work','science-question work')
    return {'payload':p,'payload_digest':digest(p)}

def grade_aime(raw, private, public):
    require(private['id']==public['id'] and private['public_digest']==digest(public), 'private/source binding')
    try:
        v=decode(raw);require(set(v)=={'justification','final_integer'}, 'authoritative terminal fields')
        require(type(v['justification']) is str and v['justification'].strip(), 'finished justification')
        answer=integer(v['final_integer'])
    except (Invalid,TypeError,ValueError):return {'status':'invalid_answer','correct':None}
    if private['status']!='known':return {'status':'unknown_grade','correct':None}
    return {'status':'graded','correct':answer==private['integer'],'integer':answer,
            'meaning':'terminal integer agreement only; intermediate proof not certified'}
