import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "scripts/two_regime_medqa_batch.py"
spec = importlib.util.spec_from_file_location("medqa_batch", path)
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


class BatchReviews(unittest.TestCase):
    def test_frozen_batch_ids(self):
        self.assertEqual(batch.launch.cell(batch.CELL)["candidates"], batch.IDS)
        self.assertEqual(len(set(batch.IDS[1:])), 7)

    def test_preserve_unsupported_and_invalid_without_prompt(self):
        for status in ("invalid", "unsupported"):
            packet = dict(entry_for_review=dict(contract={}), source={},
                          row=dict(status="completed", review=dict(status=status),
                                   raw_response=json.dumps(dict(reason="No usable plan"))))
            with patch("builtins.input", side_effect=AssertionError):
                self.assertEqual(batch.contract_review(packet)["decision"], status)

    def test_fit_failure_has_no_contract(self):
        packet = dict(entry_for_review=dict(contract={}), row=dict(status="unrun_fit", review=None))
        entry = batch.contract_review(packet)
        self.assertEqual(entry["decision"], "invalid")
        self.assertNotIn("contract", entry)

    def test_binding_preserves_dependency_and_only_one_option_field(self):
        tasks = [dict(id="T1", responsibility="Assess evidence", required_inputs=["problem_statement"]),
                 dict(id="T2", responsibility="Compare options", required_inputs=["T1"])]
        packet = dict(entry_for_review=dict(contract={}), source={},
                      row=dict(status="completed", review=dict(status="wire_valid"),
                               raw_response=json.dumps(dict(tasks=tasks))))
        with patch("builtins.input", side_effect=["admitted reviewed"]):
            entry = batch.contract_review(packet)
        contract = entry["contract"]
        self.assertEqual(contract["outputs"], ["t1"])
        self.assertEqual(contract["tasks"][1]["parents"], ["t0"])
        self.assertEqual(contract["tasks"][0]["fields"], ["derivation", "artifact"])
        self.assertEqual(contract["tasks"][1]["fields"], ["justification", "option_label"])

    def test_expanded_or_reordered_stage_rejected(self):
        scope = dict(cell=batch.CELL, source_ids=[batch.IDS[1]], history=[{}], family_review={},
                     limits=dict(maximum_calls=1, calls_per_source=1, token_cap=16384, output_cap=3072,
                                 physical_gpus=1, wall_seconds=3600))
        batch.check_stage(scope, 1, [{}], {})
        for field in scope["limits"]:
            changed = dict(scope, limits=dict(scope["limits"]))
            changed["limits"][field] += 1
            with self.subTest(field=field), self.assertRaises(batch.launch.grid.Invalid):
                batch.check_stage(changed, 1, [{}], {})
        for changed in (dict(scope, wave={}), dict(scope, source_ids=[batch.IDS[2]]), dict(scope, history=[])):
            with self.assertRaises(batch.launch.grid.Invalid):
                batch.check_stage(changed, 1, [{}], {})

    def test_resume_first_receipt_then_stop_at_selected_bundle(self):
        from contextlib import ExitStack
        from tempfile import TemporaryDirectory

        scope = dict(source_ids=[batch.IDS[0]], cell=batch.CELL, history=[], parent="/anchor",
                     limits=dict(maximum_calls=1, calls_per_source=1, token_cap=16384,
                                 output_cap=3072, physical_gpus=1, wall_seconds=3600))
        key = batch.digest(scope)
        with TemporaryDirectory() as directory, ExitStack() as stack:
            campaign = Path(directory)
            step = campaign / "plan-1"
            step.mkdir()
            run = campaign / "finished-job"
            entry = dict(source_id=batch.IDS[0], run=str(run), contract={})
            packet = dict(scope_digest=key, previous_prefix=[], entry_for_review=entry,
                          row=dict(status="completed", review=dict(status="invalid")))
            batch.save(step / "manifest.disabled.json", dict(scope=scope, scope_digest=key))
            batch.save(step / "submission.json", {"job_id": "123"})
            batch.save(step / "contract-review.json", packet)
            stack.enter_context(patch.object(batch, "FIRST", key))
            stack.enter_context(patch.object(batch.launch, "anchor", return_value={}))
            stack.enter_context(patch.object(batch.launch, "public_rows", return_value={}))
            stack.enter_context(patch.object(batch, "wait_for_result", return_value=run))
            submit = stack.enter_context(patch.object(batch.launch.base, "submit"))
            def select(slot, public, entries):
                if entries:
                    return {"status": "bundle_frozen"}, {"calls": 1}
                return {"status": "next_candidate", "source_id": batch.IDS[0]}, {}
            stack.enter_context(patch.object(batch.launch, "history", side_effect=select))
            batch.drive(campaign)
            batch.drive(campaign)
            submit.assert_not_called()
            self.assertFalse((campaign / "plan-2").exists())
            self.assertEqual(batch.read(campaign / "planner-batch-result.json")["selection"]["status"], "bundle_frozen")

    def test_math_equal_prefix_and_terminal_field(self):
        slot = batch.launch.cell(batch.MATH_CELL)
        self.assertEqual(slot["candidates"], batch.MATH_IDS)
        self.assertEqual((slot["target_m"], len(batch.MATH_IDS)), (4, 8))
        plan = {"tasks": [dict(id="T1", responsibility="Evaluate", required_inputs=["problem_statement"])]}
        packet = dict(entry_for_review=dict(contract={}), source={},
                      row=dict(status="completed", review=dict(status="wire_valid"), raw_response=json.dumps(plan)))
        with patch("builtins.input", return_value="admitted reviewed"):
            entry = batch.contract_review(packet, "final_answer")
        self.assertEqual(entry["contract"]["tasks"][0]["fields"], ["justification", "final_answer"])
