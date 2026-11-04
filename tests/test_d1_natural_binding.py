"""Synthetic binding tampering checks; no filesystem source/model reads."""
import copy
import unittest
from bc_phase2 import d1_natural_binding as b
from bc_phase2 import d1_natural_screen as n
from bc_phase2 import joint_d1_local as l
from bc_phase2.model import Invalid,digest


def fixtures():
    h='a'*64
    v={'status':'three_statement_requests_tokenized_no_model','model_executed':False,'execution_allowed':False,
       'checkpoint':n.CHECKPOINT,'revision':n.REVISION,'interface_implementation':n.implementation(),
       'prompt_hash':digest(n.PROMPT),'schema_hash':digest(n.response_schema()),
       'statements_file_sha256':l.STATEMENTS_HASH,
       'statements_file':n.disabled_manifest()['scope']['source_package']['path']+'/statements.json',
       'files':{k:{'sha256':x} for k,x in l.METADATA.items()},
       'template_check':{'enable_thinking':False,'template_hash':l.TEMPLATE_HASH,
                         'on_off_switch':{'reasoning_support_verified':True,'probe_on_hash':h,'probe_off_hash':'b'*64}},
       'output_reservation_tokens':3072,
       'real_source_counts':[{'source_id':s,'input_tokens':100,'reserved_tokens':3172,
                             'statement_sha256':l.STATEMENT_HASHES[s],'payload_digest':h,'rendered_ids_digest':h} for s in n.SMOKE]}
    shards=[f'model-{i}.safetensors' for i in range(11)]
    old={'schema':'joint-d1-local-verification-v1','checkpoint':n.CHECKPOINT,'revision':n.REVISION,
         'source_ids':list(n.SMOKE),'statements_file_sha256':l.STATEMENTS_HASH,
         'inventory':{'files':{**l.METADATA,**{s:h for s in shards}},'weight_shards':shards},
         'local_path':'/synthetic/'+n.REVISION,'generation_tokens':{'eos_token_id':[248046,248044],'pad_token_id':248044}}
    cluster=dict(partition='NA100q',time='01:00:00',memory_gb=128,python='/synthetic/python',
                 storage_root='/synthetic',cache_root='/synthetic/cache',snapshot_root='/synthetic/snapshots',output_root='/synthetic/outputs')
    return v,old,cluster,'PartitionName=NA100q State=UP Nodes=node01'


class Binding(unittest.TestCase):
    def test_disabled_no_calls_and_preserves_limits(self):
        args=fixtures();before=copy.deepcopy(args);m=b.bind(*args);r=b.review(m)
        self.assertEqual(args,before)
        self.assertFalse(r['execution_allowed']);self.assertFalse(r['model_executed'])
        self.assertEqual(r['resources']['maximum_calls'],3)
        self.assertEqual(r['resources']['output_token_cap'],3072)
        self.assertEqual(r['observed_total_reservation_tokens'],9516)
        self.assertEqual(r['approval_template']['decision'],'pending')
        self.assertEqual(m['scope']['stop_policy'],n.disabled_manifest()['scope']['stop_policy'])

    def test_token_source_prompt_and_thinking_tampering(self):
        changes=[lambda v:v.update(prompt_hash='0'*64),lambda v:v['real_source_counts'].reverse(),
                 lambda v:v['real_source_counts'][0].update(input_tokens=14000),
                 lambda v:v['real_source_counts'][0].update(reserved_tokens=4000),
                 lambda v:v['template_check'].update(enable_thinking=True),
                 lambda v:v.update(statements_file_sha256='0'*64),
                 lambda v:v.update(interface_implementation={})]
        for change in changes:
            with self.subTest(change=change):
                args=fixtures();change(args[0])
                with self.assertRaises(Invalid):b.bind(*args)

    def test_inventory_and_resource_tampering(self):
        for kind in ('model','shard','metadata','stop','time','memory','partition','state'):
            with self.subTest(kind=kind):
                v,o,c,p=fixtures()
                if kind=='model':o['revision']='other'
                if kind=='shard':o['inventory']['weight_shards'].pop()
                if kind=='metadata':o['inventory']['files']['config.json']='0'*64
                if kind=='stop':o['generation_tokens']['eos_token_id']=[1]
                if kind=='time':c['time']='02:00:00'
                if kind=='memory':c['memory_gb']=256
                if kind=='partition':c['partition']='other'
                if kind=='state':p=p.replace('UP','DOWN')
                with self.assertRaises(Invalid):b.bind(v,o,c,p)

    def test_digest_and_approval_do_not_enable_execution(self):
        m=b.bind(*fixtures());m['scope']['resources']['maximum_calls']=4
        with self.assertRaises(Invalid):b.review(m)
        m=b.bind(*fixtures());m['approval']={'decision':'approved'}
        with self.assertRaises(Invalid):b.review(m)
        with self.assertRaises(Invalid):n.open_live(m)

if __name__=='__main__':unittest.main()
