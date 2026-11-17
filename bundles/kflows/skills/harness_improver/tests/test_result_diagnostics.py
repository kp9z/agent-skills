"""Public receipt inspector checks shared with the standalone installed helper."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/test_results.py'
if not CLI.exists():
    CLI = ROOT / 'evidence/test_results.py'


def identity():
    return dict(checkout='/fixture/checkout', baseline='a' * 40, revision='a' * 40,
                algorithm='git-working-bytes-v1', fingerprint='1' * 64, excluded=['build'], installed=[])


def receipt():
    source = identity()
    return dict(source=source, sourceAfter=dict(source), selected=['a', 'b', 'c', 'd'],
                executed=['a', 'b', 'c', 'd'], status='passed', exitCode=0,
                summary=dict(failedTests=0, skippedTests=0))


class DiagnosticTests(unittest.TestCase):
    def inspect(self, data, log=None, *options):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'run.json'
            path.write_text(json.dumps(data))
            if log is not None:
                (path.parent/'test.log').write_text(log)
            run = subprocess.run([sys.executable, str(CLI), str(path), *options], text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            return json.loads(run.stdout)

    def test_stale_four_pass_receipt_is_source_changed(self):
        data = receipt()
        data['sourceAfter']['fingerprint'] = '2' * 64
        data.update(exitCode=1, status='failed')
        result = self.inspect(data)
        self.assertEqual(result['verification'], 'not_passed')
        self.assertEqual(result['failure_kind'], 'source_changed')
        self.assertEqual(result['source_verification']['state'], 'changed')
        self.assertEqual(result['source_verification']['after']['fingerprint'], '2' * 64)
        self.assertEqual(result['failure_reasons'], ['source_changed', 'runner_or_unclassified'])

    def test_identity_trust_and_execution_only_limits(self):
        data = receipt()
        self.assertEqual(self.inspect(data)['source_verification']['state'], 'matching')
        data['sourceAfter']['fingerprint'] = '2' * 64
        result = self.inspect(data)
        self.assertEqual((result['verification'], result['failure_kind']), ('not_passed', 'source_changed'))
        for field, value, state in [('fingerprint', 'bogus', 'invalid'), ('algorithm', 'other', 'unknown'),
                                    ('checkout', '/other', 'unknown'), ('baseline', 'b'*40, 'unknown'),
                                    ('excluded', [], 'unknown'), ('installed', [{'path': '/helper', 'sha256': '3'*64}], 'unknown')]:
            data = receipt(); data['sourceAfter'][field] = value
            result = self.inspect(data)
            self.assertEqual(result['source_verification']['state'], state)
            self.assertEqual(result['verification'], 'unverified')
            self.assertNotIn('source_changed', result['failure_reasons'])
        data = receipt(); del data['sourceAfter']
        self.assertEqual(self.inspect(data)['verification'], 'unverified')
        del data['source']
        result = self.inspect(data)
        self.assertEqual(result['verification'], 'passed')
        self.assertIn('execution-only', result['source_verification']['detail'])
        self.assertIn('source-bound completion', result['limits'])

    def test_concurrent_reasons_and_execution_failures(self):
        data = receipt(); data['sourceAfter']['fingerprint'] = '2'*64
        data.update(status='failed', exitCode=65, executed=['a', 'extra'], summary=dict(failedTests=1, skippedTests=1))
        result = self.inspect(data, "a.swift:12:3: error: compiler message\nTest Case '-[Tests testA]' failed (0.1 seconds).\n")
        self.assertEqual(result['failure_reasons'], ['source_changed', 'compiler', 'test_assertion', 'execution_mismatch', 'runner_or_unclassified'])
        self.assertEqual(result['failure_kind'], 'source_changed')
        self.assertEqual(result['missing_count'], 3)
        self.assertEqual(result['unexpected'], ['extra'])
        for change in [dict(executed=[]), dict(selected=[]), dict(executed=['extra']),
                       dict(summary=dict(failedTests=0, skippedTests=1))]:
            data = receipt(); data.update(change)
            self.assertEqual(self.inspect(data)['verification'], 'not_passed')
        for summary in [None, [], {'failedTests': 'bad', 'skippedTests': 0}, {'failedTests': -1, 'skippedTests': 0}]:
            data = receipt(); data['summary'] = summary
            result = self.inspect(data)
            self.assertEqual(result['verification'], 'unverified')
            self.assertIn('receipt_invalid', result['failure_reasons'])
        result = self.inspect(receipt(), "XCTAssertTrue failed - assertion\n")
        self.assertEqual(result['failure_kind'], 'test_assertion')

    def test_bounded_safe_diagnostics_and_unknown_log_coverage(self):
        data = receipt(); data['executed'] = ['other']
        data['selected'] = ['case'+str(n)+'x'*2000 for n in range(20)]
        lines = [f'a.swift:{n}:1: error: TOKEN=secret-value ' + 'x'*1000 for n in range(20)]
        result = self.inspect(data, '\n'.join(lines + [lines[0]])+'\n', '--limit', '2', '--chars', '80')
        self.assertEqual(len(result['errors']), 2)
        self.assertEqual(result['additional_error_lines'], 18)
        self.assertEqual(result['log_coverage']['matched_lines'], 21)
        self.assertTrue(result['truncation']['errors'])
        self.assertTrue(result['truncation']['missing'])
        self.assertTrue(result['truncation']['items'])
        self.assertLessEqual(max(map(len, result['missing'])), 80)
        self.assertNotIn('secret-value', json.dumps(result))
        self.assertEqual(result['errors'][0]['line'], 1)
        result = self.inspect(receipt(), 'x'*(3*1024*1024) + '\nerror: late secret\n')
        self.assertEqual(result['verification'], 'unverified')
        self.assertEqual(result['log_coverage']['state'], 'unknown')
        self.assertLess(len(json.dumps(result)), 12000)
        result = self.inspect(receipt(), None)
        self.assertEqual(result['log_coverage']['state'], 'unavailable')

    def test_malformed_receipt_has_safe_bounded_cli_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'run.json'; path.write_text('{"secret":"do-not-print",')
            run = subprocess.run([sys.executable, str(CLI), str(path)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            result = json.loads(run.stdout)
            self.assertEqual(result['verification'], 'unverified')
            self.assertEqual(result['failure_kind'], 'receipt_invalid')
            self.assertNotIn('do-not-print', run.stdout)

    def test_shared_golden_corpus_and_optional_peer_cli(self):
        corpus = json.loads((Path(__file__).parent/'fixtures/test-result-golden.json').read_text())
        peer = os.environ.get('DIAGNOSTICS_PEER_CLI')
        for case in corpus:
            with self.subTest(case=case['name']), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'run.json'; path.write_text(json.dumps(case['receipt']))
                if case['log'] is not None:
                    (path.parent/'test.log').write_text(case['log'])
                results = []
                for cli in [CLI] + ([Path(peer)] if peer else []):
                    run = subprocess.run([sys.executable, str(cli), str(path)], capture_output=True, text=True)
                    self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                    result = json.loads(run.stdout); results.append(result)
                    expected = case['expected']
                    self.assertEqual(result['verification'], expected['verification'])
                    self.assertEqual(result['failure_reasons'], expected['failure_reasons'])
                    self.assertEqual(result['source_verification']['state'], expected['source_state'])
                if peer:
                    self.assertEqual(results[0], results[1])
