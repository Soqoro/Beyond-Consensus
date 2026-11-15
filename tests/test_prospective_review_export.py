"""Synthetic controls for the read-only block-one review export."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from bc_phase2.model import digest,Invalid
from bc_phase2.prospective_sources import faithful_identity,freeze

spec=importlib.util.spec_from_file_location('review_export',Path(__file__).resolve().parents[1]/'scripts/export_prospective_math_review.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class ReviewExport(unittest.TestCase):
    def data(self):
        public=[dict(id=f'test/synthetic/{i}.json',problem=f'Synthetic x + {i} = 5') for i in range(500)]
        meta=[dict(source_id=r['id'],canonical_id='math500:'+r['id'],exact_hash=faithful_identity(r)[0],normalized_hash=faithful_identity(r)[1],family_id='',status='eligible') for r in public]
        proc={'kind':'synthetic'};proc['procedure_digest']=digest(proc)
        raw=json.dumps(public).encode();h=e.hashlib.sha256(raw).hexdigest()
        inv=dict(dataset='math500',revision=e.REVISION,records=meta,procedure=proc,access_receipt=dict(read_authorized=True,sha256=h))
        exp=dict(cutoff='synthetic',aliases=[],records=[dict(dataset='math500',source_id=r['id'],phase='historical') for r in public[:64]])
        enriched=json.loads(json.dumps(exp));by={r['source_id']:r for r in meta}
        for r in enriched['records']:
            for k in ('canonical_id','exact_hash','normalized_hash'):r[k]=by[r['source_id']][k]
        review=dict(dataset='math500',revision=e.REVISION,inventory_digest=digest(meta),reviewer='Codex metadata audit; not semantic family clearance',reviewed_at='2026-11-15',decisions={},prior_selected=[])
        cohort=freeze(meta,'math500',e.REVISION,enriched,proc,review)
        return inv,raw,exp,dict(INVENTORY=digest(meta),PUBLIC=h,PROCEDURE=proc['procedure_digest'],COHORT=cohort['cohort_digest'])
    def test_exact_blocks_bounded_export_and_digest(self):
        inv,raw,exp,bindings=self.data()
        with patch.multiple(e,**bindings):
            out=e.export(inv,raw,exp)
            self.assertEqual(len(out['cards']),8)
            self.assertLessEqual(len(out['comparison_cards']),40)
            self.assertEqual(out['unique_pairs_compared'],668)
            self.assertEqual(len({sid for b in out['frozen_blocks'] for sid in b['source_ids']}),24)
            self.assertEqual(out['packet_digest'],digest({k:v for k,v in out.items() if k!='packet_digest'}))
            self.assertFalse(out['execution_allowed']);self.assertEqual(out['decisions'],[])
            self.assertEqual(out,e.export(inv,raw,exp))
    def test_changed_bytes_or_inventory_rejected(self):
        inv,raw,exp,bindings=self.data()
        with patch.multiple(e,**bindings):
            with self.assertRaises(Invalid):e.export(inv,raw+b' ',exp)
            inv['records'][0]['normalized_hash']='0'*64
            with self.assertRaises(Invalid):e.export(inv,raw,exp)
    def test_protected_fields_rejected_even_with_rebound_byte_receipt(self):
        inv,raw,exp,bindings=self.data();records=json.loads(raw);records[0]['answer']='private'
        raw=json.dumps(records).encode();bindings['PUBLIC']=e.hashlib.sha256(raw).hexdigest();inv['access_receipt']['sha256']=bindings['PUBLIC']
        with patch.multiple(e,**bindings):
            with self.assertRaises(Invalid):e.export(inv,raw,exp)
    def test_no_numeric_masking(self):
        self.assertNotEqual(e.tokens('x + 5'),e.tokens('x + 6'))
        self.assertNotEqual(e.tokens('x + 5'),e.tokens('x - 5'))
        self.assertNotEqual(e.tokens('X + 5'),e.tokens('x + 5'))

if __name__=='__main__':unittest.main()
