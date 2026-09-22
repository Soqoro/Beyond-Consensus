"""Fixed invalid drafts for a labelled synthetic correction diagnostic.

Drafts are experiment inputs, not model generations or native reference answers.
"""
from copy import deepcopy
from dataclasses import replace

from .sqlite_compatibility import tasks as compatibility_tasks
from ..util import digest

SUITE = 'tool_correction_v1'


def tasks():
    result = []
    for index, task in enumerate(compatibility_tasks()[:2]):
        unit = f'sqlite-correction-{index}'
        col = lambda name: {'column': name}
        if index == 0:
            tree = {'columns': [
                {'expr': col('department_id')},
                {'expr': {'call': {'name': 'sum', 'args': [col('amount'), {'literal': 0}]}}, 'as': 'total_amount'},
                {'expr': {'call': {'name': 'count', 'args': [col('id')]}}, 'as': 'entry_count'}],
                'from': {'table': 'entries'}, 'group_by': [col('department_id')],
                'order_by': [{'expr': col('department_id'), 'direction': 'asc'}]}
        else:
            tree = {'columns': [{'expr': col('e.id'), 'as': 'entry_id'},
                {'expr': col('d.name'), 'as': 'department_name'},
                {'expr': col('e.amount'), 'as': 'amount'}],
                'from': {'table': 'entries', 'as': 'e'},
                'joins': [{'kind': 'inner', 'source': {'table': 'departments', 'as': 'dept'},
                           'on': {'binary': ['=', col('e.department_id'), col('dept.id')]}}],
                'order_by': [{'expr': col('e.id'), 'direction': 'asc'}]}
        draft = {'tool': 'run_read_query', 'permitted_artifact_versions': {}, 'select_sql': tree}
        metadata = deepcopy(task.metadata)
        metadata.update(adaptation='bc_sqlite_tool_correction_v1', diagnostic_mode='tool_correction',
                        sqlite_fixture_suite=SUITE, initial_invalid_action=draft,
                        initial_action_hash=digest(draft), source_ids=['sqlite-correction-v1'])
        spec = task.specification.replace('tool-compatibility', 'tool-correction')
        spec += (' Before your first model turn the harness executes a supplied draft action. '
                 'It is an experiment input, not your prior output. Use its observation and the public '
                 'contract to construct and submit a correct artifact. You may rewrite the draft.')
        result.append(replace(task, id=unit, group='sqlite-tool-correction-source-v1',
            specification=spec, sources={unit: deepcopy(task.sources[task.id])},
            required_outputs=(unit,), metadata=metadata))
    return result
