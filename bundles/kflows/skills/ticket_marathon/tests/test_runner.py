"""Actual marathon integration with fake chat/device effects and disposable repos."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from runner import Marathon
from ownership import OwnershipError


class MarathonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'original'
        self.isolated = self.root / 'isolated'
        for repo in (self.repo, self.isolated):
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / 'user.txt').write_text('untouched draft')
        self.registry = self.root / 'ownership.json'
        self.runner = Marathon(self.registry)
        self.device = 'simulator:local/aaaaaaaa-1111-2222-3333-444444444444'
        self.effects = []

    def request(self, key='120', repo=None):
        repo = repo or self.repo
        return dict(schemaVersion=1, dispatchId=key, owner=dict(chatId='orchestrator', hostId='local'),
                    checkout=str(repo), branch='main', phase='implementation', pendingAction='dispatch',
                    resources=['checkout:' + str(repo), self.device], authorizationRef='user://routine-testing',
                    cursor='initial', evidence=[], budgetReceipts=['receipt://125/existing-404'])

    def create(self, chat):
        def effect(prompt):
            self.effects.append(('create', chat))
            return dict(chatId=chat, hostId='local', cursor='cursor-' + chat)
        return effect

    def test_dispatch_is_once_and_resume_preserves_cursor_and_authorization(self):
        request = self.request()
        result = self.runner.dispatch(request, self.create('worker120'))
        saved = dict(request, owner=dict(chatId='worker120', hostId='local'), cursor=result['worker']['cursor'], **result['credentials'])
        resumed = Marathon(self.registry).resume(saved, lambda permit: self.effects.append(('edit', permit['cursor'])))
        self.assertEqual(resumed['worker']['cursor'], 'cursor-worker120')
        self.assertEqual(resumed['worker']['authorizationRef'], 'user://routine-testing')
        retry = self.runner.dispatch(request, self.create('duplicate'))
        self.assertEqual(retry['status'], 'existing_worker')
        self.assertEqual(self.effects, [('create', 'worker120'), ('edit', 'cursor-worker120')])

    def assert_blocked(self, code, function):
        with self.assertRaises(OwnershipError) as raised:
            function()
        self.assertEqual(raised.exception.result['error'], code)

    def saved(self, request, result):
        return dict(request, owner=result['worker']['owner'], cursor=result['worker']['cursor'], **result['credentials'])

    def test_unknown_chat_creation_never_redispatches_and_attaches_observed_worker(self):
        data = self.request()
        def interrupted(prompt):
            self.effects.append(('created-but-response-lost', 'worker120'))
            raise ConnectionError('fake lost reply')
        with self.assertRaises(ConnectionError):
            self.runner.dispatch(data, interrupted)
        restarted = Marathon(self.registry)
        pending = restarted.dispatch(data, self.create('duplicate'))
        self.assertEqual(pending['status'], 'pending_dispatch')
        attached = restarted.attach(dict(data, **pending['credentials'], worker=dict(chatId='worker120', hostId='local'),
                                         workerCursor='observed-cursor'))
        self.assertEqual(attached['worker']['owner']['chatId'], 'worker120')
        self.assertEqual(self.effects, [('created-but-response-lost', 'worker120')])

    def test_stale_cursor_and_authorization_never_reach_effect(self):
        data = self.request()
        result = self.runner.dispatch(data, self.create('worker120'))
        saved = self.saved(data, result)
        self.runner.resume(dict(saved, nextCursor='new-cursor'))
        self.assert_blocked('stale_cursor', lambda: self.runner.resume(saved, lambda _: self.effects.append('bad')))
        self.assert_blocked('authorization_disagreement', lambda: self.runner.resume(
            dict(saved, cursor='new-cursor', authorizationRef='manufactured'), lambda _: self.effects.append('bad')))
        self.assertEqual(self.effects, [('create', 'worker120')])

    def test_resume_returns_current_phase_and_pending_action(self):
        data = self.request()
        result = self.runner.dispatch(data, self.create('worker120'))
        saved = self.saved(data, result)
        current = dict(saved, phase='attention', pendingAction='actual environment permission')
        resumed = self.runner.resume(current)
        self.assertEqual(resumed['worker']['phase'], 'attention')
        self.assertEqual(resumed['worker']['pendingAction'], 'actual environment permission')
        claim = self.runner.registry.operate('claim', current)['claim']
        self.assertEqual(claim['phase'], 'attention')
        self.assertEqual(claim['pendingAction'], 'actual environment permission')

    def test_120_122_handoff_late_resume_and_clean_checkout_reassignment(self):
        # Before contract: a fake shared device observes the overlapping late resume.
        before_device_owner = 'worker122'
        before_conflicts = int(before_device_owner != 'worker120')
        data120 = self.request()
        result120 = self.runner.dispatch(data120, self.create('worker120'))
        saved120 = self.saved(data120, result120)
        data122 = self.request('122', self.isolated)
        self.assert_blocked('conflict', lambda: self.runner.dispatch(data122, self.create('worker122')))
        # #120 keeps its dirty checkout reserved but explicitly releases the phone.
        self.runner.registry.operate('release', dict(saved120, resources=[self.device]))
        result122 = self.runner.dispatch(data122, self.create('worker122'))
        saved122 = self.saved(data122, result122)
        self.assert_blocked('stale_or_wrong_owner', lambda: self.runner.resume(saved120, lambda _: self.effects.append('bad-device')))
        self.runner.resume(dict(saved120, resources=['checkout:' + str(self.repo)]),
                           lambda _: self.effects.append(('reserved-checkout', 'worker120')))
        self.runner.resume(saved122, lambda _: self.effects.append(('fake-device', 'worker122')))
        # Existing #120 chat resumes on a clean integration checkout after explicit releases.
        self.runner.registry.operate('release', dict(saved120, resources=['checkout:' + str(self.repo)]))
        self.runner.registry.operate('release', saved122)
        clean = self.root / 'integration'
        subprocess.run(['git', 'init', '-q', str(clean)], check=True)
        new_request = dict(saved120, checkout=str(clean), resources=['checkout:' + str(clean), self.device])
        reassigned = Marathon(self.registry).reassign(new_request)
        resumed = self.saved(new_request, reassigned)
        self.assert_blocked('stale_worker', lambda: self.runner.resume(saved120, lambda _: self.effects.append('bad-stale')))
        self.runner.resume(resumed, lambda _: self.effects.append(('fake-device', 'worker120')))
        self.assertEqual(self.runner.dispatch(data120, self.create('duplicate'))['status'], 'existing_worker')
        self.runner.registry.operate('release', resumed)
        report = self.runner.registry.operate('reconcile', dict(resumed, expected=[], evidence=['fixture://handoff/explicit-release']))
        self.assertEqual(report['observed'], [])
        self.assertEqual([item for item in self.effects if item[0] == 'create'], [('create', 'worker120'), ('create', 'worker122')])
        for repo in (self.repo, self.isolated):
            self.assertEqual((repo / 'user.txt').read_text(), 'untouched draft')
        demo = dict(scenario='mocked-120-122-handoff', before=dict(observedFakeDeviceOverlaps=before_conflicts),
                    after=dict(ownershipConflicts=2, staleSavedStateRejections=1, duplicateDispatches=0,
                               explicitReleaseOperations=4, fakeDeviceEffects=['worker122', 'worker120'], remainingClaims=0),
                    budgetReceipts=data120['budgetReceipts'], effects=self.effects,
                    limits='Disposable mock only; no live requests/devices, nonparticipating edits or measured savings claims.')
        if os.environ.get('HARNESS_DEMO_RECEIPT'):
            Path(os.environ['HARNESS_DEMO_RECEIPT']).write_text(json.dumps(demo, indent=2) + '\n')

    def test_prepare_cli_serializes_competing_dispatch_and_rejects_bad_input(self):
        script = Path(__file__).resolve().parents[1] / 'scripts/runner.py'
        data = self.request()
        processes = [subprocess.Popen([sys.executable, str(script), '--registry', str(self.registry), 'prepare'],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for _ in range(4)]
        for process in processes:
            process.stdin.write(json.dumps(data))
            process.stdin.close()
        results = []
        for process in processes:
            results.append(json.loads(process.stdout.read()))
            self.assertEqual(process.wait(), 0)
            process.stdout.close()
            process.stderr.close()
        self.assertEqual([result['status'] for result in results].count('prepared'), 1)
        self.assertEqual([result['status'] for result in results].count('pending_dispatch'), 3)
        self.assert_blocked('dispatch_disagreement', lambda: self.runner.prepare(dict(data, authorizationRef='different')))


if __name__ == '__main__':
    unittest.main()
