"""Read existing project selection METADATA only; never open MATH data/cards."""
import hashlib
import json
from pathlib import Path
from .joint_schema import require
from .planner_first import ORIGINAL_IDS,DIAGRAM_IDS


def source_binding(root):
    root=Path(root)
    paths={
        'ordered_manifest':'outputs/phase2-planner-first-v2-2026-10-28/bundle/manifest.disabled.json',
        'prior_review':'outputs/phase2-math500-content-review-2026-10-27/review.json',
        'smoke':'outputs/phase2-planner-smoke-preparation-2026-10-28/proposal.disabled.json'}
    loaded={};files={};gaps=[]
    for k,p in paths.items():
        path=root/p
        if not path.is_file():gaps.append('SOURCE_BINDING_UNAVAILABLE:'+k);continue
        raw=path.read_bytes();loaded[k]=json.loads(raw)
        files[k]=dict(path=p,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    ordered=loaded.get('ordered_manifest',{}).get('rows',[])
    ids=[r['source_id'] for r in ordered]
    require(not ids or ids==list(ORIGINAL_IDS),'original selection/order changed')
    smoke=loaded.get('smoke',{}).get('source_ids',[])
    require(all(s in ids and s not in DIAGRAM_IDS for s in smoke),'frozen smoke eligibility')
    review=loaded.get('prior_review',{})
    return dict(schema='joint-source-bindings-v1',files=files,original_ids=ids,
                selection_order_verified=ids==list(ORIGINAL_IDS),frozen_smoke_ids=smoke,
                diagram_blocked=sorted(DIAGRAM_IDS),proposal_digest=review.get('proposal_digest'),
                previous_admissions=sum(r.get('admitted') is True for r in review.get('dispositions',[])),
                source_family_status='unresolved',historical_ABC='SOURCE_BINDING_UNAVAILABLE',
                source_statements_accessed=False,dataset_accessed=False,source_replaced=False,
                blockers=gaps+['actual_statement_binding_not_checked_in_this_offline_stage',
                    'diagram_representation_review_pending','source_family_review_pending',
                    'live_source_rights_and_workflow_admission_pending'],execution_allowed=False)
