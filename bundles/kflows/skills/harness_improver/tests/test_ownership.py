"""Public CLI fixtures; no live chat, device or provider effects."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/ownership.py'


class OwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'user.txt').write_text('preserve me')
        self.registry = self.root / 'registry.json'
        self.request = dict(schemaVersion=1, owner=dict(chatId='worker120', hostId='local'),
                            checkout=str(self.repo), branch='main', phase='implementation',
                            pendingAction='edit', resources=['checkout:' + str(self.repo)],
                            evidence=[], budgetReceipts=[])

    def call(self, operation, request=None, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), '--registry', str(self.registry), operation],
                                input=json.dumps(request or self.request), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_claim_retry_conflict_and_owner_release(self):
        claim = self.call('claim')['claim']
        self.assertEqual(self.call('claim')['claim'], claim)
        other = dict(self.request, owner=dict(chatId='worker122', hostId='local'))
        conflict = self.call('claim', other, ok=False)
        self.assertEqual(conflict['error'], 'conflict')
        self.assertEqual(conflict['conflicts'][0]['owner']['chatId'], 'worker120')
        release = dict(self.request, token=claim['token'], generation=claim['generation'])
        self.call('release', dict(release, owner=other['owner']), ok=False)
        self.call('release', release)
        newer = self.call('claim', other)['claim']
        self.assertGreater(newer['generation'], claim['generation'])
        self.call('release', release, ok=False)
        self.assertEqual((self.repo / 'user.txt').read_text(), 'preserve me')

    def test_group_conflict_is_atomic_and_paths_alias(self):
        device = 'simulator:local/AAAAAAAA-1111-2222-3333-444444444444'
        claim = self.call('claim', dict(self.request, resources=[device]))['claim']
        alias = self.root / 'alias'
        alias.symlink_to(self.repo, target_is_directory=True)
        other = dict(self.request, owner=dict(chatId='worker122', hostId='local'),
                     checkout=str(alias), resources=['checkout:' + str(alias), device.lower()])
        self.call('claim', other, ok=False)
        # Partial failure must not have retained the free checkout.
        first = self.call('claim')['claim']
        other['resources'] = ['checkout:' + str(alias)]
        self.assertEqual(self.call('claim', other, ok=False)['error'], 'conflict')
        self.call('release', dict(self.request, token=first['token'], generation=first['generation']))
        self.call('release', dict(self.request, resources=[device], token=claim['token'], generation=claim['generation']))

    def test_simultaneous_competitors_have_one_owner(self):
        commands = [subprocess.Popen([sys.executable, str(SCRIPT), '--registry', str(self.registry), 'claim'],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    for _ in range(6)]
        for index, process in enumerate(commands):
            process.stdin.write(json.dumps(dict(self.request, owner=dict(chatId=f'worker{index}', hostId='local'))))
            process.stdin.close()
        results = []
        for process in commands:
            results.append(json.loads(process.stdout.read()))
            process.wait()
            process.stdout.close()
            process.stderr.close()
        self.assertEqual(sum(result['status'] == 'owned' for result in results), 1)
        self.assertEqual(sum(result.get('error') == 'conflict' for result in results), 5)

    def test_invalid_schema_and_corrupt_state_preserve_bytes(self):
        self.call('claim')
        original = self.registry.read_bytes()
        for change in ({'schemaVersion': 9}, {'owner': {}}, {'resources': []}, {'phase': 'x' * 129}):
            self.call('claim', dict(self.request, **change), ok=False)
            self.assertEqual(self.registry.read_bytes(), original)
        self.registry.write_text('{broken')
        self.assertEqual(self.call('claim', ok=False)['error'], 'corrupt_or_unsupported_state')
        self.assertEqual(self.registry.read_text(), '{broken')

    def test_restart_requires_explicit_release_even_after_attention(self):
        claim = self.call('claim', dict(self.request, phase='attention', pendingAction='approval'))['claim']
        other = dict(self.request, owner=dict(chatId='worker122', hostId='local'))
        self.call('claim', other, ok=False)
        stale = dict(self.request, token=claim['token'], generation=claim['generation'] + 1)
        self.call('release', stale, ok=False)
        expected = [dict(resource=claim['resources'][0], owner=claim['owner'], generation=claim['generation'])]
        reconciliation = dict(self.request, expected=expected, evidence=['handoff://120/approval'],
                              budgetReceipts=['receipt://125/authoritative'])
        result = self.call('reconcile', reconciliation)
        self.assertEqual(result['budgetReceipts'], ['receipt://125/authoritative'])
        self.call('reconcile', dict(reconciliation, expected=[]), ok=False)
        self.call('claim', other, ok=False)
        self.call('release', dict(self.request, token=claim['token'], generation=claim['generation']))
        self.call('claim', other)

    def test_interrupted_write_needs_reviewed_reconciliation(self):
        import hashlib
        claim = self.call('claim')['claim']
        original = self.registry.read_bytes()
        self.registry.with_suffix('.json.pending').write_text('interrupted replacement')
        self.assertEqual(self.call('claim', ok=False)['error'], 'interrupted_write')
        expected = [dict(resource=claim['resources'][0], owner=claim['owner'], generation=claim['generation'])]
        recovery = dict(self.request, expected=expected, recoverInterrupted=True,
                        reviewer=dict(chatId='reviewer', hostId='local'), expectedFingerprint=hashlib.sha256(original).hexdigest())
        self.call('reconcile', recovery, ok=False)
        self.call('reconcile', dict(recovery, evidence=['handoff://120/reviewed-recovery']))
        self.assertEqual(self.registry.read_bytes(), original)
        self.assertEqual(self.call('claim')['claim'], claim)

    def test_denied_registry_does_not_grant(self):
        self.registry.mkdir()
        self.assertEqual(self.call('claim', ok=False)['error'], 'io_or_invalid_json')
        self.assertTrue(self.registry.is_dir())

    @unittest.skipIf(__import__('os').geteuid() == 0, 'root bypasses filesystem permission fixture')
    def test_permission_denial_preserves_last_ownership(self):
        self.call('claim')
        original = self.registry.read_bytes()
        self.registry.chmod(0)
        try:
            self.assertEqual(self.call('claim', ok=False)['error'], 'io_or_invalid_json')
        finally:
            self.registry.chmod(0o600)
        self.assertEqual(self.registry.read_bytes(), original)

    def test_real_interrupted_replace_preserves_last_published_state(self):
        # Mock only the operating-system write boundary, then restart through CLI.
        import importlib.util
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('fixture_ownership', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        claim = self.call('claim')['claim']
        original = self.registry.read_bytes()
        release = dict(self.request, token=claim['token'], generation=claim['generation'])
        with patch.object(module.os, 'replace', side_effect=OSError('fixture interruption')):
            with self.assertRaises(OSError):
                module.Registry(self.registry).operate('release', release)
        self.assertEqual(self.registry.read_bytes(), original)
        self.assertEqual(self.call('claim', ok=False)['error'], 'interrupted_write')

    def test_reconcile_uses_canonical_order_across_owners(self):
        later = dict(self.request, resources=['output:' + str(self.root / 'z')])
        earlier = dict(self.request, owner=dict(chatId='worker122', hostId='local'),
                       resources=['output:' + str(self.root / 'a')])
        z = self.call('claim', later)['claim']
        a = self.call('claim', earlier)['claim']
        expected = [dict(resource=claim['resources'][0], owner=claim['owner'], generation=claim['generation'])
                    for claim in (a, z)]
        result = self.call('reconcile', dict(self.request, resources=a['resources'] + z['resources'], expected=expected))
        self.assertEqual(result['observed'], expected)

    def test_unsupported_persisted_boolean_schema_fails_closed(self):
        self.call('claim')
        data = json.loads(self.registry.read_text())
        data['schemaVersion'] = True
        self.registry.write_text(json.dumps(data))
        original = self.registry.read_bytes()
        self.assertEqual(self.call('claim', ok=False)['error'], 'corrupt_or_unsupported_state')
        self.assertEqual(self.registry.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
