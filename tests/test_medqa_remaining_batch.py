import importlib.util,json,tempfile,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from bc_phase2.model import digest,Invalid
from bc_phase2.prospective_sources import faithful_identity

spec=importlib.util.spec_from_file_location('remaining_medqa',Path(__file__).resolve().parents[1]/'scripts/prepare_medqa_remaining_batch.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class RemainingBatch(unittest.TestCase):
    def fixture(self):
        c=deepcopy(p.planner.cohort())
        public=[dict(id=f'test/row/{i}',question=f'Synthetic question {i}',options=dict(A='one',B='two',C='three',D='four')) for i in range(1,1274)]
        historical=[dict(id=f'dev/row/{i}',question=f'Historical fixture {i}',options=dict(A='one',B='two',C='three',D='four')) for i in range(1,13)]
        by={r['id']:r for r in public}
        for b in c['blocks']:
            for r in b['records']:r['exact_hash'],r['normalized_hash']=faithful_identity(by[r['source_id']])
        exposure=[dict(dataset='medqa',source_id=r['id'],exact_hash=faithful_identity(r)[0],normalized_hash=faithful_identity(r)[1]) for r in historical]
        return c,public,historical,exposure
    def test_review_is_cost_blind_public_only_and_fixed_block(self):
        c,pub,hist,exp=self.fixture()
        with tempfile.TemporaryDirectory() as td:
            cfg=Path(td)/p.planner.CONFIG;cfg.parent.mkdir(parents=True);cfg.write_text(json.dumps({'exposure':{'records':exp}}))
            with patch.object(p,'ROOT',Path(td)):
                r=p.review_packet(pub,{'records':hist},c)
                self.assertEqual(r['source_ids'],[x['source_id'] for x in c['blocks'][2]['records']])
                self.assertEqual(len(r['cards']),8);self.assertFalse(r['execution_allowed'])
                self.assertEqual(sum(len(v) for row in r['comparisons'] for v in row['nearest'].values()),40)
                bad=deepcopy(pub);bad[0]['answer_idx']='A'
                with self.assertRaises(Invalid):p.review_packet(bad,hist,c)
                bad=deepcopy(pub);bad[1266]['question']='changed'
                with self.assertRaises(Invalid):p.review_packet(bad,hist,c)
    def test_proposal_disabled_and_stage_caps_sum_to_campaign_ceiling(self):
        c=p.planner.cohort()
        review=dict(source_ids=[r['source_id'] for r in c['blocks'][2]['records']],cohort_digest=c['cohort_digest'])
        review['packet_digest']=digest(review)
        s=dict(model={},source_package={},wave=p.worker.packet()['wave'])
        m=dict(scope_digest='synthetic',blockers=[])
        with patch.object(p.worker,'validate_manifest',return_value=s):
            result=p.proposal(m,review)
            limits=result['total_limits'];stages=result['stages']
            self.assertEqual(sum(x['maximum_calls'] for x in stages),limits['maximum_calls'])
            self.assertEqual(sum(x['token_cap'] for x in stages),limits['token_cap'])
            self.assertEqual(sum(x['wall_seconds'] for x in stages),limits['allocated_wall_seconds'])
            self.assertEqual(limits['maximum_calls'],134)
            self.assertFalse(result['execution_allowed']);self.assertFalse(result['submitted'])
            self.assertEqual(stages[2]['maximum_calls'],88)
            bad=deepcopy(review);bad['source_ids'][0]='test/row/988';bad['packet_digest']=digest({k:v for k,v in bad.items() if k!='packet_digest'})
            with self.assertRaises(Invalid):p.proposal(m,bad)
    def test_public_hash_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'public.json';path.write_text('[]')
            with self.assertRaises(Invalid):p.read_public(path,'0'*64)

if __name__=='__main__':unittest.main()
