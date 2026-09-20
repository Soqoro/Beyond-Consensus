"""Opt-in audit commands; existing runner/stager/scheduler remain authoritative."""
from pathlib import Path
from .util import BCError, read_json, atomic_json
COMMANDS = {'competence-compare', 'competence-audit'}
def add_parsers(sub):
    p = sub.add_parser('competence-compare', help='Compare resolved manifests; absent control stays unmatched')
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--control-manifest', type=Path)
    p.add_argument('--control-source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('competence-audit', help='Sanitized per-task and decoder-ledger audit; no model or SQL')
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--control-run', type=Path)
    p.add_argument('--output', type=Path, required=True)
def dispatch(args):
    from .diagnostics.competence import compatibility, audit
    if args.output.exists(): raise BCError('Use a new report path; observations are immutable')
    result = (compatibility(read_json(args.manifest), read_json(args.control_manifest) if args.control_manifest else None,
                            args.control_source) if args.command=='competence-compare' else audit(args.run,args.control_run))
    atomic_json(args.output, result)
    return result
