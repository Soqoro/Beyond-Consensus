"""Bounded Python audit observations; not an OS process monitor or CPU ledger."""
import os
import sys
from contextlib import contextmanager

_ACTIVE = None
_INSTALLED = False
_EVENTS = {'subprocess.Popen', 'os.posix_spawn', 'os.exec', 'os.fork',
           'os.forkpty', 'os.system'}


def _observe(event, args):
    record = _ACTIVE
    if record is None or event not in _EVENTS:
        return
    try:
        if len(record['events']) >= 64:
            record['truncated'] = True
            return
        # Do not persist argv, shell command strings, cwd, environment or locals.
        executable = None
        if event in {'subprocess.Popen', 'os.posix_spawn', 'os.exec'} and args:
            value = args[0]
            if isinstance(value, (str, bytes)):
                executable = os.path.basename(os.fsdecode(value))[:128]
        frames = []
        frame = sys._getframe(1)
        try:
            for _ in range(12):
                if frame is None:
                    break
                frames.append(dict(file=os.path.basename(frame.f_code.co_filename),
                                   function=frame.f_code.co_name[:128], line=frame.f_lineno))
                frame = frame.f_back
        finally:
            del frame
        record['events'].append(dict(event=event, executable=executable, callers=frames))
    except Exception:
        # Diagnostic failure must not replace a generation error or alter launch.
        record['capture_error'] = True


@contextmanager
def process_launch_trace():
    global _ACTIVE, _INSTALLED
    if _ACTIVE is not None:
        raise RuntimeError('Nested process-launch trace unsupported')
    if not _INSTALLED:
        sys.addaudithook(_observe)
        _INSTALLED = True
    record = dict(schema='rr-python-process-launch-trace-v1', events=[],
                  truncated=False, capture_error=False,
                  coverage='Python audit launch attempts in this interpreter during inference; native launches may be invisible',
                  attribution='launch attempts only; not child PID, exit, or CPU attribution',
                  sensitive_arguments_recorded=False)
    _ACTIVE = record
    try:
        yield record
    finally:
        _ACTIVE = None
