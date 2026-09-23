"""Frozen synthetic aggregation probes; terminal expectations use Python only."""
from pathlib import Path
import sqlite3
from ..schemas import TaskInstance
from ..util import BCError, canonical, digest
from ..runtime.sqlite_executor import DEFAULT_LIMITS, POLICY

SUITE = 'aggregation_v1'
SCHEMA = {'teams': ['id', 'name'], 'payments': ['id', 'team_id', 'amount'],
          'notices': ['id', 'team_id', 'severity']}
TEAMS = ((1, 'Amber'), (2, 'Blue'), (3, 'Cedar'), (4, 'Dune'))
# Repeated amounts distinguish correct aggregation from SUM(DISTINCT amount).
PAYMENTS = ((1, 1, 10), (2, 1, 10), (3, 1, 5), (4, 2, 7), (5, 2, 2), (6, 3, 4))
NOTICES = ((1, 1, 'critical'), (2, 1, 'normal'), (3, 2, 'normal'),
           (4, 2, 'critical'), (5, 2, 'normal'), (6, 4, 'normal'))
RELATIONSHIPS = ['payments.team_id = teams.id', 'notices.team_id = teams.id']
REQUIREMENTS = {
    'payments': 'For every team return team_id and total_amount, the sum of its payment amounts. Include teams without payments with total_amount 0. Order by team_id ascending.',
    'independent_details': 'For every team return team_id, total_amount (sum of its payment amounts), notice_count (number of its notices), and critical_count (number of its notices whose severity is critical). Include teams with no payments or notices, using 0 for missing totals/counts. Order by team_id ascending.',
}


def tasks():
    result = []
    for probe, requirement in REQUIREMENTS.items():
        unit = 'sqlite-aggregation-' + probe
        contract = dict(kind='query', requirement=requirement, schema=SCHEMA, relationships=RELATIONSHIPS)
        result.append(TaskInstance(unit, 'sqlite_fixture', 'sqlite-aggregation-source-v1',
            'Synthetic schema-supplied aggregation diagnostic, not a native benchmark. '
            'Read the assigned contract, create the requested query artifact, and submit its returned artifact ID. '
            'Schema: ' + canonical(SCHEMA) + '. Relationships: ' + canonical(RELATIONSHIPS) +
            '. Requirement: ' + requirement, {unit: contract}, (unit,), (), {
                'adaptation': 'bc_sqlite_aggregation_v1', 'scorer': 'bc-sqlite-aggregation-v1',
                'tool_policy': POLICY, 'access_regime': 'synthetic_schema_supplied',
                'diagnostic_mode': 'aggregation', 'sqlite_fixture_suite': SUITE,
                'probe': probe, 'synthetic': True, 'readiness': 'fixture',
                'base_hash': digest([SCHEMA, TEAMS, PAYMENTS, NOTICES]),
                'source_ids': ['sqlite-aggregation-v1'],
                'harness': {'tables': list(SCHEMA), 'schema': SCHEMA, 'documents': {},
                            'limits': dict(DEFAULT_LIMITS)}}))
    return result


def database(path):
    path = Path(path)
    if not path.exists():
        con = sqlite3.connect(path)
        try:
            con.execute('CREATE TABLE teams(id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
            con.execute('CREATE TABLE payments(id INTEGER PRIMARY KEY, team_id INTEGER NOT NULL, amount INTEGER NOT NULL)')
            con.execute('CREATE TABLE notices(id INTEGER PRIMARY KEY, team_id INTEGER NOT NULL, severity TEXT NOT NULL)')
            con.executemany('INSERT INTO teams VALUES (?,?)', TEAMS)
            con.executemany('INSERT INTO payments VALUES (?,?,?)', PAYMENTS)
            con.executemany('INSERT INTO notices VALUES (?,?,?)', NOTICES)
            con.commit()
        finally:
            con.close()
    return path


def expected(probe):
    if probe not in REQUIREMENTS:
        raise BCError('Unknown aggregation probe')
    columns = ['team_id', 'total_amount']
    if probe == 'independent_details':
        columns += ['notice_count', 'critical_count']
    rows = []
    for team, _ in TEAMS:
        row = [team, sum(amount for _, owner, amount in PAYMENTS if owner == team)]
        if probe == 'independent_details':
            row += [sum(owner == team for _, owner, _ in NOTICES),
                    sum(owner == team and severity == 'critical' for _, owner, severity in NOTICES)]
        rows.append(row)
    return columns, rows


def score(probe, output):
    columns, rows = expected(probe)
    return output['columns'] == columns and output['rows'] == rows
