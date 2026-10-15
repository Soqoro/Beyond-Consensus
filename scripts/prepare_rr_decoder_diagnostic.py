"""Prepare/review the exact four-call synthetic decoder diagnostic; never submit."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from beyond_consensus.experiments import rr_decoder_diagnostic as probe
from beyond_consensus.util import read_json
from reporecourse.common import write_new


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    build=sub.add_parser('proposal')
    for name in ('model-lock','native-lock','controls','parent-manifest','parent-report','output'):
        build.add_argument('--'+name,type=Path,required=True)
    build.add_argument('--approval-template',type=Path,required=True)
    normal=sub.add_parser('normal-proposal')
    for name in ('manifest','report','review','model-lock','controls','evidence-output','approval-template'):
        normal.add_argument('--'+name,type=Path,required=True)
    approve=sub.add_parser('approve')
    for name in ('proposal','approval','output'):approve.add_argument('--'+name,type=Path,required=True)
    review=sub.add_parser('review')
    for name in ('manifest','report','output'):review.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if args.command=='proposal':
        result=probe.build(ROOT,read_json(args.model_lock),read_json(args.native_lock),read_json(args.controls),read_json(args.parent_manifest),read_json(args.parent_report))
        write_new(args.output,result)
        write_new(args.approval_template,probe.approval_template(result))
    elif args.command=='normal-proposal':
        from beyond_consensus.util import digest
        from beyond_consensus.experiments.manifest import source_revision
        evidence={k:read_json(getattr(args,k)) for k in ('manifest','report','review')}
        template=probe.review_template(evidence['manifest'],evidence['report'])
        reviewed=evidence['review']
        probe.require(template['observed_both_arms_completed'] and all(reviewed.get(k)==v for k,v in template.items() if k not in ('decision','reviewer','reviewed_at','normal_qualification_allowed')) and reviewed.get('decision')=='approved' and reviewed.get('normal_qualification_allowed') is True and reviewed.get('reviewer') and reviewed.get('reviewed_at'),'Diagnostic review unresolved')
        controls=read_json(args.controls);probe.unique.check_controls(ROOT,controls)
        write_new(args.evidence_output,evidence)
        write_new(args.approval_template,dict(schema='rr-unique-normal-approval-v1',evidence_hash=digest(evidence),maximum_calls=3,source_revision=source_revision(ROOT),model_lock_sha256=digest(read_json(args.model_lock)),controls_hash=digest(controls),task_execution_allowed=False,launch_blocking=False,decision='pending',reviewer=None,reviewed_at=None))
        print('Written:',args.evidence_output,args.approval_template)
        return
    elif args.command=='approve':
        write_new(args.output,probe.approve(read_json(args.proposal),read_json(args.approval)))
    else:write_new(args.output,probe.review_template(read_json(args.manifest),read_json(args.report)))
    print('Written:',args.output)

if __name__=='__main__':main()
