"""Opt-in audit commands; existing runner/stager/scheduler remain authoritative."""
from pathlib import Path
from .util import BCError, read_json, atomic_json
COMMANDS = {'competence-compare', 'competence-audit', 'native-failure-audit', 'correction-audit'}
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
    p = sub.add_parser('native-failure-audit', help='CPU-only private native failure replay; no model or score changes')
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('correction-audit', help='Compare matched synthetic correction runs; no model or SQL')
    p.add_argument('--generic-run', type=Path, required=True)
    p.add_argument('--feedback-run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
def dispatch(args):
    from .diagnostics.competence import compatibility, audit
    if args.output.exists(): raise BCError('Use a new report path; observations are immutable')
    if args.command == 'correction-audit':
        if any(args.output.resolve().is_relative_to(root.resolve()) for root in (args.generic_run, args.feedback_run)):
            raise BCError('Write correction reports outside both historical runs')
        from .diagnostics.sqlite_correction import compare
        result = compare(args.generic_run, args.feedback_run)
        atomic_json(args.output, result)
        return result
    if args.command == 'native-failure-audit':
        if args.output.resolve().is_relative_to(args.run.resolve()):
            raise BCError('Write offline audit reports outside the historical run directory')
        from .diagnostics.sqlite_failure import audit as replay
        result = replay(args.run)
        atomic_json(args.output, result)
        return result
    result = (compatibility(read_json(args.manifest), read_json(args.control_manifest) if args.control_manifest else None,
                            args.control_source) if args.command=='competence-compare' else audit(args.run,args.control_run))
    atomic_json(args.output, result)
    return result
