"""Reporting regression controls, no model or SQL execution."""
import unittest
from unittest.mock import Mock
from beyond_consensus.experiments.reporecourse import check_preflight_responses


class PreflightReportingTests(unittest.TestCase):
    def env(self, sql=None):
        env=Mock()
        env.action.return_value={'version':'synthetic-version'}
        env.execute.return_value=sql or {'status':'ok','outputs':[{'rows':[[1]]}]}
        return env

    def test_reasoning_only_long_output_preserves_short_sql_success(self):
        env=self.env()
        sql,short,long=check_preflight_responses(env,'{"tool":"publish"}','Wait, I should output JSON...')
        self.assertEqual(sql,env.execute.return_value)
        self.assertTrue(short['passed']);self.assertFalse(long['passed'])
        self.assertEqual(long['status'],'invalid_json')
        env.execute.assert_called_once_with('synthetic-version')

    def test_short_parse_failure_never_executes_and_long_is_independent(self):
        env=self.env()
        sql,short,long=check_preflight_responses(env,'not JSON','{"tool":"list_sources"}')
        self.assertEqual(sql['status'],'not_executed')
        self.assertEqual(short['stage'],'short_action_parse')
        self.assertFalse(short['passed']);self.assertTrue(long['passed'])
        env.action.assert_not_called();env.execute.assert_not_called()

    def test_publish_failure_has_own_stage(self):
        env=self.env();env.action.side_effect=ValueError('synthetic rejection')
        sql,short,long=check_preflight_responses(env,'{}','{"tool":"list_sources"}')
        self.assertFalse(short['passed']);self.assertEqual(short['stage'],'short_action_publish')
        self.assertEqual(short['error_type'],'ValueError');env.execute.assert_not_called()
        self.assertEqual(sql['status'],'not_executed')

    def test_sql_semantic_error_is_not_long_parse_error(self):
        expected={'status':'semantic_error'};env=self.env(expected)
        sql,short,long=check_preflight_responses(env,'{}','{"tool":"list_sources"}')
        self.assertEqual(sql,expected);self.assertFalse(short['passed']);self.assertTrue(long['passed'])
        self.assertEqual(short['stage'],'short_sql_execution')

    def test_both_pass_and_wrong_or_partial_long_action_fails(self):
        for text,expected in [('{"tool":"list_sources"}',True),('{}',False),('{"tool":',False)]:
            with self.subTest(text=text):
                _,short,long=check_preflight_responses(self.env(),'{}',text)
                self.assertTrue(short['passed']);self.assertEqual(long['passed'],expected)


class LongContextProbeTests(unittest.TestCase):
    def test_deterministic_fit_and_instruction_separation(self):
        from beyond_consensus.experiments.reporecourse import long_context_probe
        def count(messages):
            return sum(len(m['content']) for m in messages)+20
        first=long_context_probe(count,8192)
        self.assertEqual(first,long_context_probe(count,8192))
        self.assertLessEqual(count(first),8192-2048)
        self.assertGreater(count(first),8192-2048-100)
        self.assertIn('record 00000:',first[1]['content'])
        self.assertIn('</synthetic_records>',first[1]['content'])
        self.assertNotIn('synthetic datum',first[1]['content'])
        self.assertTrue(first[1]['content'].endswith('Return {"tool":"list_sources"}.'))

    def test_too_small_context_fails_closed(self):
        from beyond_consensus.experiments.reporecourse import long_context_probe
        from beyond_consensus.util import BCError
        with self.assertRaises(BCError):
            long_context_probe(lambda messages: 500,2048)
