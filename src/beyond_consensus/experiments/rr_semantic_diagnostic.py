"""Synthetic mechanism packet only; no worker execution or historical replay."""
from copy import deepcopy
import time

from reporecourse.common import digest

SCHEMA = 'rr-semantic-diagnostic-design-v1'


def fixtures():
    # Authored independently of repository data and hidden historical witnesses.
    return {
        'customers': [10, 20, 30],
        'orders': [{'id': 101, 'customer': 10}, {'id': 102, 'customer': 10},
                   {'id': 201, 'customer': 20}],
        'payments': [{'order': 101, 'amount': 7}, {'order': 101, 'amount': 7},
                     {'order': 201, 'amount': 0}],
    }


def reference(data):
    """Independent Python aggregation; no joins, SQL, or model answers."""
    rows = []
    for customer in data['customers']:
        orders = [o for o in data['orders'] if o['customer'] == customer]
        ids = {o['id'] for o in orders}
        payments = [p for p in data['payments'] if p['order'] in ids]
        paid = {p['order'] for p in payments}
        rows.append([customer, len(orders), len(payments),
                     sum(p['amount'] for p in payments), len(paid), len(ids-paid)])
    return rows


def controls():
    """Arithmetic counterexamples, not production compiler/monitor qualification."""
    start = time.process_time()
    data = fixtures()
    expected = reference(data)
    # Simulate LEFT JOIN row multiplicity without executing SQL.
    joined_counts = []
    unpaid_null_counts = []
    for customer in data['customers']:
        orders = [o for o in data['orders'] if o['customer'] == customer]
        joined_counts.append(sum(max(1, sum(p['order'] == o['id']
                                for p in data['payments'])) for o in orders))
        unpaid_null_counts.append(sum(not any(p['order'] == o['id']
                                     for p in data['payments']) for o in orders)
                                  if orders else 1)
    checks = {
        'reference_rows': expected == [[10, 2, 2, 14, 1, 1],
                                       [20, 1, 1, 0, 1, 0], [30, 0, 0, 0, 0, 0]],
        'raw_join_order_count_rejected': joined_counts != [r[1] for r in expected],
        'null_customer_unpaid_count_rejected': unpaid_null_counts != [r[5] for r in expected],
        'distinct_amount_workaround_rejected': sum({p['amount'] for p in data['payments']}) != sum(r[3] for r in expected),
        'zero_amount_is_still_paid': expected[1][4] == 1,
    }
    value = {'labels_response': {'names': ['alpha']}, 'sizes_response': {'X': 4}}
    correct = {'labels': value['labels_response']['names'], 'size_bytes': value['sizes_response']}
    wrong = {'errors': value['labels_response']['names'], 'errors_bytes': value['sizes_response']}
    checks['same_values_wrong_keys_rejected'] = correct != wrong
    # Explicitly a shape illustration; do not claim the runtime was executed.
    checks['wrong_keys_can_match_self_declared_shape'] = set(wrong) == {'errors', 'errors_bytes'}
    return dict(status='passed' if all(checks.values()) else 'failed', checks=checks,
                evidence='authored_python_mechanism_controls_only',
                analysis_cpu_seconds=time.process_time()-start,
                model_executed=False, sql_executed=False,
                production_monitor_executed=False, historical_scores_changed=False)


def packet():
    public = [
        dict(id='order_grain', format='sql', tables=fixtures(),
             request='Return one row per customer, including customers without orders: customer_id, order_count, payment_count, amount_cents. Count each order once and every payment separately; amounts are integer cents.'),
        dict(id='unpaid_boundary', format='sql', tables=fixtures(),
             request='Return one row per customer: customer_id, paid_orders, unpaid_orders. A paid order has at least one payment, even if its amount is zero. A customer with no orders has both counts zero.'),
        dict(id='mapping_keys', format='mapping',
             input_contract={'labels_response': {'names': 'array of strings'},
                             'sizes_response': 'object of integer values'},
             request='Produce exactly labels from labels_response.names and size_bytes from sizes_response. Preserve values. Both fields are required and no extra fields are allowed.'),
    ]
    design = dict(schema=SCHEMA, cases=public, controls=controls(),
        intended_model_calls=3, model_planner_calls=0, retries=0,
        context_limit=16384, output_cap=2048, pool=7,
        per_case_token_cap=16384, per_case_cpu_cap=1200,
        physical_gpu_concurrency=1, task_execution_allowed=False,
        source='benchmark_authored_synthetic', selection='post_hoc_mechanism_diagnostic',
        accounting='Separate diagnostic ledger; never historical episode work.',
        feedback='No private expected rows or historical evaluation feedback delivered to workers.',
        blockers=['production_executor_and_monitor_controls_required',
                  'exact_worker_lock_and_tokenizer_footprint_required',
                  'shared_runner_execution_adapter_required',
                  'exact_gpu_scope_approval_required'],
        limitations=['Not a held-out task sample or planner comparison.',
                     'No inference that guarded decoding caused incorrect keys.',
                     'Public monitoring remains unchanged.'])
    # Stable design identity excludes variable CPU observation.
    identity = deepcopy(design)
    identity['controls'].pop('analysis_cpu_seconds')
    design['design_id'] = digest(identity)
    return design


def task(case_id):
    """Public-only synthetic task; reference programs never enter observations."""
    case = next(c for c in packet()['cases'] if c['id'] == case_id)
    columns = (['customer_id', 'order_count', 'payment_count', 'amount_cents']
               if case_id == 'order_grain' else ['customer_id', 'paid_orders', 'unpaid_orders'])
    public = dict(id=case_id, family='api_schema' if case_id == 'mapping_keys' else 'data_product',
                  request=case['request'], sources={'request': case['request']},
                  required_outputs=[dict(id='report', format=case['format'])],
                  examples={'default': {}}, tables={})
    if case_id == 'mapping_keys':
        public['examples']['default'] = {'labels_response': {'names': ['alpha']}, 'sizes_response': {'X': 4}}
        public['sources']['input_contract'] = case['input_contract']
    else:
        data = fixtures()
        public['tables'] = {
            'customers': dict(columns=[['id', 'INTEGER']], rows=[[i] for i in data['customers']]),
            'orders': dict(columns=[['id', 'INTEGER'], ['customer', 'INTEGER']],
                           rows=[[o['id'], o['customer']] for o in data['orders']]),
            'payments': dict(columns=[['order_id', 'INTEGER'], ['amount', 'INTEGER']],
                             rows=[[p['order'], p['amount']] for p in data['payments']]),
        }
        public['sources']['tables'] = public['tables']
        public['required_outputs'][0]['columns'] = columns
    return public


def environment(case_id, resources=None):
    from reporecourse.runtime import Environment
    public = task(case_id)
    fmt = public['required_outputs'][0]['format']
    unit = dict(id='report', worker='w0', outputs=['report'], depends=[], consumes={},
                produces={'report': fmt}, terminal_bindings={'report': 'report'},
                sources=sorted(public['sources']), interfaces={'report': public['request']},
                description='Publish the assigned report once using the public contract.')
    env = Environment(public, resources=resources, workers=tuple('w'+str(i) for i in range(7)),
                      execution_contract='plan_scoped_v1',
                      plan=dict(id='synthetic', schema='rr-work-plan-v2', units=[unit]),
                      interface_profile='rr-interface-reliability-v1')
    env.scopes.begin(unit, 'w0', 'primary')
    env.assignment['w0'] = unit
    return env


def authored_action(case_id, mutation=None):
    """Private CPU control programs only; not prompts or generated responses."""
    if case_id == 'order_grain':
        content = ('SELECT c.id AS customer_id, COUNT(DISTINCT o.id) AS order_count, '
                   'COUNT(p.order_id) AS payment_count, COALESCE(SUM(p.amount),0) AS amount_cents '
                   'FROM customers c LEFT JOIN orders o ON c.id=o.customer '
                   'LEFT JOIN payments p ON o.id=p.order_id GROUP BY c.id ORDER BY c.id')
        if mutation == 'fanout':
            content = content.replace('COUNT(DISTINCT o.id)', 'COUNT(o.id)')
        elif mutation == 'distinct_amount':
            content = content.replace('SUM(p.amount)', 'SUM(DISTINCT p.amount)')
    elif case_id == 'unpaid_boundary':
        content = ('SELECT c.id AS customer_id, '
                   'SUM(CASE WHEN q.n>0 THEN 1 ELSE 0 END) AS paid_orders, '
                   'SUM(CASE WHEN o.id IS NOT NULL AND q.n IS NULL THEN 1 ELSE 0 END) AS unpaid_orders '
                   'FROM customers c LEFT JOIN orders o ON c.id=o.customer '
                   'LEFT JOIN (SELECT order_id, COUNT(*) AS n FROM payments GROUP BY order_id) q '
                   'ON o.id=q.order_id GROUP BY c.id ORDER BY c.id')
        if mutation == 'null_row':
            content = content.replace('o.id IS NOT NULL AND q.n IS NULL', 'q.n IS NULL')
    else:
        keys = ['labels', 'size_bytes'] if mutation is None else ['errors', 'errors_bytes']
        content = dict(fields={keys[0]: dict(path=['labels_response', 'names'], missing='error'),
                               keys[1]: dict(path=['sizes_response'], missing='error')},
                       output_schema=dict(type='object', required=keys, additionalProperties=False,
                           properties={keys[0]: dict(type='array', items=dict(type='string')),
                                       keys[1]: dict(type='object', additionalProperties=dict(type='integer'))}))
    return dict(tool='publish', name='report', format=task(case_id)['required_outputs'][0]['format'],
                content=content, bindings={}, obligations=['report'])


def semantic_check(case_id, execution):
    """Offline independent oracle; never returned as worker feedback."""
    if execution.get('status') != 'ok':
        return False
    if case_id == 'mapping_keys':
        return execution.get('output') == {'labels': ['alpha'], 'size_bytes': {'X': 4}}
    rows = reference(fixtures())
    indexes = [0, 1, 2, 3] if case_id == 'order_grain' else [0, 4, 5]
    output = execution.get('outputs', [{}])[0]
    return (output.get('columns') == task(case_id)['required_outputs'][0]['columns'] and
            output.get('rows') == [[r[i] for i in indexes] for r in rows] and
            all(type(value) is int for row in output.get('rows', []) for value in row))


def inspect_action(env, case_id, action):
    """Same publication/compiler/monitor paths; candidate SQL stays in child."""
    if (action.get('tool') != 'publish' or action.get('name') != 'report' or
            action.get('obligations') != ['report'] or action.get('bindings') != {} or
            action.get('format') != env.public['required_outputs'][0]['format']):
        from reporecourse.common import Rejected
        raise Rejected('diagnostic_action_contract')
    env.action('w0', action)
    public = env.check_public()
    execution = env.execute(env.bound['report'], env.public['examples']['default'])
    return dict(public_monitor_passed=public['report'], execution_status=execution['status'],
                semantic_correct=semantic_check(case_id, execution))


def production_controls():
    from reporecourse.common import Rejected
    from reporecourse.qualification import implementation_hashes, runtime_versions
    from reporecourse.resources import Resources
    from pathlib import Path
    import hashlib
    start = time.process_time()
    rows = []
    cases = [('order_grain', None), ('order_grain', 'fanout'),
             ('order_grain', 'distinct_amount'), ('unpaid_boundary', None),
             ('unpaid_boundary', 'null_row'), ('mapping_keys', None), ('mapping_keys', 'wrong_keys')]
    for case_id, mutation in cases:
        env = environment(case_id, Resources(16384, 1200))
        row = dict(case=case_id, mutation=mutation, status='started')
        try:
            row.update(inspect_action(env, case_id, authored_action(case_id, mutation)))
            row['status'] = 'passed' if (row['public_monitor_passed'] is True and
                                           row['semantic_correct'] is (mutation is None)) else 'failed'
        except Rejected as exc:
            row.update(status='blocked_prerequisite' if str(exc) == 'blocked_prerequisite' else 'failed',
                       error_category=str(exc))
        finally:
            row['resources'] = env.resources.summary()
            row['events'] = deepcopy(env.events)
            env.close()
        rows.append(row)
    status = ('passed' if all(r['status'] == 'passed' for r in rows) else
              'blocked_prerequisite' if any(r['status'] == 'blocked_prerequisite' for r in rows) else 'failed')
    return dict(schema='rr-semantic-production-controls-v1', status=status, cases=rows,
                implementation_hashes=implementation_hashes(), runtime_versions=runtime_versions(),
                diagnostic_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                analysis_cpu_seconds=time.process_time()-start, model_executed=False,
                sql_executed=any(e.get('category') == 'executor' for r in rows for e in r['events']),
                task_execution_allowed=False, historical_scores_changed=False,
                accounting='Separate control ledger; parent analysis CPU includes parent ledger subsets, child CPU separate.')
