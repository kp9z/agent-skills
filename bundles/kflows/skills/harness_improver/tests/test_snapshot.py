"""Public snapshot CLI with disposable Git repos and a supplied execution boundary."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
HELPER = Path(os.environ.get('SNAPSHOT_HELPER', str(Path(os.environ.get('HARNESS_SKILLS_ROOT', str(Path.home()/'.agents/skills'))) / 'harness_improver/scripts/snapshot.py')))


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='snapshot fixture ')
        self.addCleanup(self.temp.cleanup)
        self.area = Path(self.temp.name).resolve()
        self.repo = self.area / 'original source'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        (self.repo / '.gitignore').write_text('build/\n.env\n')
        (self.repo / 'code.txt').write_text('fixed input')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.revision = self.git('rev-parse', 'HEAD').strip()
        self.stub = self.area / 'execute.py'
        self.stub.write_text('''import json,os,sys
from pathlib import Path
sys.path.insert(0,os.environ['COMPLETION_MODULE'])
from completion_record import source_identity
root=Path.cwd(); source=source_identity(root,os.environ['COMPLETION_BASELINE'],('build',))
Path(os.environ['ORIGINAL_SOURCE']).joinpath('code.txt').write_text('original edited during collection')
if os.environ.get('MUTATE_SNAPSHOT'): (root/'code.txt').write_text('snapshot mutation')
p=root/'build/results/runs/fixture'; p.mkdir(parents=True)
case='Tests/Suite/testOne'; data=dict(status='passed',exitCode=0,selected=[case],executed=[case],summary=dict(failedTests=0,skippedTests=0),source=source,sourceAfter=source_identity(root,source['baseline'],('build',)))
(p/'run.json').write_text(json.dumps(data))
''')
        self.data = dict(schemaVersion=1, source=str(self.repo), revision=self.revision,
                         baseline=self.revision, destination=str(self.area / 'snapshot output'),
                         owner=dict(chatId='fixture-worker', hostId='local'), registry=str(self.area/'registry.json'),
                         simulator='00000000-0000-0000-0000-000000000015', inputs=[],
                         command=[sys.executable,str(self.stub)], selection=['-only-testing:Tests/Suite/testOne'])

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],text=True)

    def cli(self,op='run',data=None,env=None):
        result=subprocess.run([sys.executable,str(HELPER),op],input=json.dumps(data or self.data),
            text=True,capture_output=True,env=dict(os.environ, ORIGINAL_SOURCE=str(self.repo),
            COMPLETION_MODULE=str(HELPER.parent),**(env or {})),cwd=ROOT)
        self.assertTrue(result.stdout,result.stderr)
        return result.returncode,json.loads(result.stdout)

    def test_original_mutation_keeps_fixed_input_and_checked_mapping(self):
        code, result=self.cli()
        self.assertEqual(code,0,result)
        self.assertEqual(result['status'],'passed')
        self.assertEqual(Path(result['snapshot']['checkout']).joinpath('code.txt').read_text(),'fixed input')
        self.assertNotEqual(result['original']['fingerprint'],result['originalAfter']['fingerprint'])
        code,mapping=self.cli('map',dict(run=result['record'],target=str(self.repo)))
        self.assertEqual(code,2,mapping)
        (self.repo/'code.txt').write_text('fixed input')
        code,mapping=self.cli('map',dict(run=result['record'],target=str(self.repo)))
        self.assertEqual(code,0,mapping)
        self.assertEqual(mapping['target']['fingerprint'],result['snapshot']['fingerprint'])


if __name__=='__main__': unittest.main()

class SnapshotSafetyTests(SnapshotTests):
    def test_snapshot_mutation_and_runner_failure_never_pass(self):
        code,result=self.cli(env={'MUTATE_SNAPSHOT':'1'})
        self.assertEqual(code,2,result)
        self.assertEqual(result['status'],'failed')
        self.assertTrue(result['grants'])
        for _ in range(2):
            self.assertEqual(self.cli('cleanup',{'run':result['record']})[1]['status'],'preserved')
        self.assertTrue(Path(result['record']).exists())

    def test_explicit_dirty_and_untracked_selection_excludes_unrelated_and_secrets(self):
        (self.repo/'code.txt').write_text('selected dirty')
        (self.repo/'new file.txt').write_text('selected untracked')
        (self.repo/'unrelated.txt').write_text('private draft')
        (self.repo/'.env').write_text('SECRET=fixture')
        self.data['inputs']=['code.txt','new file.txt']
        code,result=self.cli()
        self.assertEqual(code,0,result)
        snapshot=Path(result['snapshot']['checkout'])
        self.assertEqual((snapshot/'code.txt').read_text(),'selected dirty')
        self.assertEqual((snapshot/'new file.txt').read_text(),'selected untracked')
        self.assertFalse((snapshot/'unrelated.txt').exists())
        self.assertFalse((snapshot/'.env').exists())
        self.assertEqual((self.repo/'.env').read_text(),'SECRET=fixture')
        code,mapping=self.cli('map',dict(run=result['record'],target=str(self.repo)))
        self.assertEqual(code,2,mapping)  # integration still has unrelated source inputs

    def test_selected_input_hidden_by_snapshot_ignore_policy_is_rejected(self):
        (self.repo/'.gitignore').write_text('build/\n.env\nhidden.txt\n')
        self.git('add','.gitignore'); self.git('commit','-qm','committed ignore policy')
        self.data['revision']=self.git('rev-parse','HEAD').strip()
        (self.repo/'.gitignore').write_text('build/\n.env\n')
        (self.repo/'hidden.txt').write_text('required selected test input')
        self.data['inputs']=['hidden.txt']
        code,result=self.cli()
        self.assertEqual(code,2,result)
        self.assertFalse((Path(self.data['destination'])/'runner.log').exists())
        self.assertEqual((self.repo/'code.txt').read_text(),'fixed input')

    def test_missing_ignored_and_ambiguous_inputs_fail_before_execution(self):
        for inputs in [['missing.txt'],['.env'],['code.txt','code.txt'],['../execute.py'],['.']]:
            with self.subTest(inputs=inputs):
                self.data['inputs']=inputs
                code,result=self.cli()
                self.assertEqual(code,2,result)
                self.assertEqual((self.repo/'code.txt').read_text(),'fixed input')
                self.assertFalse(Path(self.data['destination']).exists())

    def test_runner_failure_retains_diagnostics_and_repeated_release_is_safe(self):
        self.data['command']=[sys.executable,'-c','raise SystemExit(7)']
        code,result=self.cli()
        self.assertEqual(code,2,result)
        self.assertEqual(result['runnerExitCode'],7)
        self.assertTrue(Path(result['record']).exists())
        request=dict(run=result['record'],owner=self.data['owner'])
        wrong=dict(request,owner=dict(chatId='other',hostId='local'))
        self.assertEqual(self.cli('release',wrong)[0],2)
        for _ in range(2): self.assertEqual(self.cli('release',request)[0],0)
        self.assertTrue(Path(result['record']).exists())

    def test_alias_and_spaces_are_canonical(self):
        alias=self.area/'alias'; alias.symlink_to(self.repo,target_is_directory=True)
        self.data['source']=str(alias)
        code,result=self.cli()
        self.assertEqual(code,0,result)
        self.assertEqual(result['original']['checkout'],str(self.repo))

    def test_existing_or_denied_destination_preserves_original(self):
        self.data['destination']=str(self.repo)
        self.assertEqual(self.cli()[0],2)
        self.assertEqual((self.repo/'code.txt').read_text(),'fixed input')
        self.data['destination']='/dev/null/cannot-create'
        self.assertEqual(self.cli()[0],2)
        self.assertEqual((self.repo/'code.txt').read_text(),'fixed input')

class SnapshotCompletionTests(SnapshotTests):
    def test_checked_mapping_preserves_tests_review_bytes_and_scope_checks(self):
        code,run=self.cli()
        self.assertEqual(code,0,run)
        (self.repo/'code.txt').write_text('fixed input')
        report=self.area/'review.txt'; report.write_text('Independent review fixture')
        review=self.area/'review.json'
        review.write_text(json.dumps(dict(ticket='fixture://140',reviewer='reviewer',judgment='approved',
            scopes=['standards','spec'],source=run['snapshot'],reference=str(report))))
        code,mapping=self.cli('map',dict(run=run['record'],target=str(self.repo),reviews=[str(review)]))
        self.assertEqual(code,0,mapping)
        manifest=dict(ticket='fixture://140',worker='worker',source=mapping['target'],
            provenance=mapping, tests=[x['path'] for x in run['tests']],reviews=[str(review)],
            requiredReviewScopes=['standards','spec'],acceptance=[dict(id='AC',result='passed',
            source=run['snapshot'],evidence=[str(report)])],missingChecks=[],exceptions=[])
        path=self.area/'manifest.json'; path.write_text(json.dumps(manifest))
        def verify():
            result=subprocess.run([sys.executable,'-c', 'import sys; sys.path.insert(0,sys.argv.pop(1)); from completion_record import main; sys.exit(main(excluded=("build",)))',str(HELPER.parent),
                '--checkout',str(self.repo),'verify',str(path)],capture_output=True,text=True)
            return result.returncode,json.loads(result.stdout)
        self.assertEqual(verify()[0],0,verify())
        report.write_text('Review now contains unresolved findings')
        self.assertNotEqual(verify()[0],0)
        report.write_text('Independent review fixture')
        review.write_text(review.read_text()+' ')
        self.assertNotEqual(verify()[0],0)
        review.write_text(json.dumps(dict(ticket='fixture://140',reviewer='reviewer',judgment='approved',
            scopes=['standards'],source=run['snapshot'],reference=str(report))))
        code,mapping=self.cli('map',dict(run=run['record'],target=str(self.repo),reviews=[str(review)]))
        manifest['provenance']=mapping; path.write_text(json.dumps(manifest))
        self.assertNotEqual(verify()[0],0)  # an explicit mapping never fills missing review scope

class SnapshotConflictTests(SnapshotTests):
    def test_simulator_conflict_stops_before_runner(self):
        claim=dict(schemaVersion=1,owner=dict(chatId='other',hostId='local'),checkout=str(self.repo),
            branch=self.git('rev-parse','--abbrev-ref','HEAD').strip(),phase='fixture',pendingAction='retain',
            resources=['simulator:local/'+self.data['simulator']],evidence=[],budgetReceipts=[])
        result=subprocess.run([sys.executable,str(HELPER.parent/'ownership.py'),'--registry',self.data['registry'],'claim'],
            input=json.dumps(claim),capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout)
        code,run=self.cli()
        self.assertEqual(code,2,run)
        self.assertEqual(run['error']['error'],'conflict')
        self.assertFalse((Path(self.data['destination'])/'runner.log').exists())
        self.assertEqual((self.repo/'code.txt').read_text(),'fixed input')

    def test_deletion_and_changed_test_receipt(self):
        (self.repo/'code.txt').unlink()
        self.data['inputs']=['code.txt']
        code,run=self.cli()
        self.assertEqual(code,0,run)
        self.assertFalse((Path(run['snapshot']['checkout'])/'code.txt').exists())
        receipt=Path(run['tests'][0]['path'])
        data=json.loads(receipt.read_text()); data['selected']=['Tests/Other/testChanged']
        receipt.write_text(json.dumps(data))
        self.assertEqual(self.cli('map',dict(run=run['record'],target=str(self.repo)))[0],2)


class SnapshotComparisonTests(SnapshotTests):
    def test_source_changing_fixture_reports_cost_separately(self):
        started = time.monotonic()
        environment = dict(os.environ, ORIGINAL_SOURCE=str(self.repo), COMPLETION_MODULE=str(HELPER.parent), COMPLETION_BASELINE=self.revision)
        direct = subprocess.run([sys.executable,str(self.stub)],cwd=self.repo,env=environment,capture_output=True)
        direct_wall = time.monotonic()-started
        receipt = json.loads((self.repo/'build/results/runs/fixture/run.json').read_text())
        self.assertEqual(direct.returncode,0)
        self.assertNotEqual(receipt['source']['fingerprint'],receipt['sourceAfter']['fingerprint'])
        (self.repo/'code.txt').write_text('fixed input')
        code, result = self.cli()
        self.assertEqual(code,0,result)
        comparison = dict(fixture='125-shaped source change during collection',
            direct=dict(invalidatedRuns=1,interventions=1,wallSeconds=direct_wall,setupSeconds=0),
            snapshot=dict(invalidatedRuns=0,interventions=0,wallSeconds=result['wallSeconds'],
                setupSeconds=result['setupSeconds'],sourceBytes=result['sourceBytes'],
                storageBytes=sum(p.stat().st_size for p in Path(result['destination']).rglob('*') if p.is_file())),
            limits='Disposable stub fixture; wall/setup/storage overhead is separate; no speedup or token-savings claim.')
        if os.environ.get('SNAPSHOT_DEMO_RECEIPT'):
            Path(os.environ['SNAPSHOT_DEMO_RECEIPT']).write_text(json.dumps(comparison,indent=2))
