"""Internal fresh-process arm entry; invoked by the approved preflight adapter."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from beyond_consensus.experiments import rr_decoder_diagnostic as probe
from beyond_consensus.util import read_json, digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','model-lock','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--arm',choices=probe.ARMS,required=True);args=parser.parse_args()
    m=read_json(args.manifest);probe.validate(m)
    probe.require(m['source_revision']==probe.source_revision(ROOT),'Frozen diagnostic source changed')
    probe.require(m.get('approval') is not None,'Exact diagnostic approval pending')
    marker=read_json(args.output.parent/'decoder-diagnostic-started.json')
    probe.require(marker.get('experiment_id')==m['experiment_id'],'Parent dispatch marker missing')
    lock=read_json(args.model_lock)
    expected=m['model_lock_sha256'] if args.arm=='guarded' else digest(m['native_lock'])
    probe.require(digest(lock)==expected,'Arm lock changed')
    report=probe.arm_run(m,args.arm,args.model_lock,ROOT,args.output)
    return 1 if report['command_failed'] else 0

if __name__=='__main__':raise SystemExit(main())
