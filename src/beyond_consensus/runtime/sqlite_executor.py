"""Compatibility module alias for the shared restricted SQLite executor.

Keep one implementation and one module state (including qualification versions),
so existing callers and instrumentation see the same trusted executor.
"""
import sys
from restricted_artifacts import sqlite_executor as _implementation
sys.modules[__name__] = _implementation
