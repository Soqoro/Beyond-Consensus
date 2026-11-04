"""Small metadata-only synthetic selector checks; no dataset access."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('screen_select',Path(__file__).resolve().parents[1]/'scripts/prepare_math500_screening_cohort.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def metadata():
    return ([{'source_id':s,'subject':m.SUBJECTS[i//2],'level':1+i%5} for i,s in enumerate(m.ORIGINAL_IDS)] +
            [{'source_id':f'mock:{i}:{level}:{j}','subject':subject,'level':level}
             for i,subject in enumerate(m.SUBJECTS) for level in range(1,6) for j in range(2)])


class Selection(unittest.TestCase):
    def test_deterministic_order_and_coverage(self):
        a=m.select(metadata());self.assertEqual(a,m.select(list(reversed(metadata()))))
        self.assertEqual(len(a),12);self.assertEqual(len({r['source_id'] for r in a}),12)
        self.assertEqual({r['subject'] for r in a},set(m.SUBJECTS))
        self.assertEqual({r['level'] for r in a},set(range(1,6)))
        self.assertFalse(set(r['source_id'] for r in a)&set(m.ORIGINAL_IDS))

    def test_preserves_original_and_blocked_no_rerun(self):
        report=m.cohort(metadata())
        self.assertEqual(report['selected_source_ids'][:14],list(m.ORIGINAL_IDS))
        self.assertEqual(sum(r['source_status']=='diagram_blocked' for r in report['questions']),2)
        self.assertEqual(sum(r['planner_status']=='completed_historical_pilot_no_rerun' for r in report['questions']),3)
        self.assertEqual(report['maximum_new_calls_if_all_remaining_text_eligible'],21)
        self.assertFalse(report['execution_allowed']);self.assertFalse(report['text_eligibility_verified'])

    def test_rejects_protected_fields_duplicates_bad_metadata(self):
        for mutation in ('answer','duplicate','level','original'):
            rows=metadata()
            if mutation=='answer':rows[0]['answer']='forbidden'
            if mutation=='duplicate':rows.append(dict(rows[0]))
            if mutation=='level':rows[0]['level']=True
            if mutation=='original':rows.pop(0)
            with self.assertRaises(m.Invalid):m.select(rows)

    def test_file_integrity_fails_before_selection(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'synthetic.jsonl';path.write_text('{}\n')
            with self.assertRaises(m.Invalid):m.read_metadata(path)

if __name__=='__main__':unittest.main()
