#!/usr/bin/env python3
"""Opt-in disposable source verification. JSON stdin/stdout; execution is an argv boundary."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import time
import uuid

from ownership import Registry, OwnershipError
from completion_record import git, load, same_source, source_identity
from test_results import inspect

EXCLUDED = ('build',)  # SkinSense runner-owned policy; not supplied by a receipt.


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    temp = path.with_suffix('.pending')
    with temp.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def entries(root):
    """Exact portable inventory, with no contents disclosed in receipts."""
    names = set(git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0')) - {b''}
    result = []
    for name in sorted(names):
        relative = os.fsdecode(name)
        if any(relative == p or relative.startswith(p + '/') for p in EXCLUDED):
            continue
        path = Path(root) / relative
        if path.is_symlink():
            mode, content = 'link', os.fsencode(os.readlink(path))
        elif path.is_file():
            mode = 'executable' if path.stat().st_mode & 0o111 else 'file'
            content = path.read_bytes()
        elif not path.exists():
            continue
        else:
            raise ValueError('Unsupported source entry')
        result.append(dict(path=relative, mode=mode, sha256=hashlib.sha256(content).hexdigest(), bytes=len(content)))
    return result


def capture(root, baseline, globals_root=None):
    return source_identity(root, baseline, EXCLUDED, globals_root)


def grant(data, checkout, resources):
    return dict(schemaVersion=1, owner=data['owner'], checkout=str(checkout),
                branch=git(checkout, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip(),
                resources=resources, phase='snapshot verification', pendingAction='fixed execution and evidence retention',
                evidence=[], budgetReceipts=[])


def validate_input(root, relative):
    if not isinstance(relative, str) or not relative or PurePosixPath(relative).as_posix() != relative:
        raise ValueError('Input must be an exact repository-relative path')
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in ('.', '..', '.git', 'build') for part in path.parts):
        raise ValueError('Input escapes source or names runner-owned metadata')
    if any(parent.is_symlink() for parent in (root / relative).parents if parent != root.parent):
        raise ValueError('Input has symlink parent')
    ignored = subprocess.run(['git','-C',str(root),'check-ignore','--no-index','-q','--',relative]).returncode
    if ignored not in (0,1) or ignored == 0:
        raise ValueError('Ignored input is unavailable; credentials are never copied')
    # Explicit selection is not permission to import conventional secret material.
    if any(p.lower() in ('.env', '.aws', '.ssh', 'credentials', 'credentials.json') or
           p.lower().endswith(('.pem','.key','.p12')) or p.lower().startswith('.env.') for p in path.parts):
        raise ValueError('Credential input is unsupported')
    tracked = bool(git(root, 'ls-files', '-z', '--', relative).strip(b'\0'))
    item = root / relative
    if not item.exists() and not item.is_symlink() and not tracked:
        raise ValueError('Selected input is missing')
    if item.is_dir():
        raise ValueError('Select individual files, not directories')
    if item.is_symlink():
        raise ValueError('Selected symlink inputs are unsupported; commit them explicitly')
    return item


def run(data):
    started = time.monotonic()
    root = Path(data['source']).resolve(strict=True)
    if Path(git(root,'rev-parse','--show-toplevel').decode().strip()).resolve() != root:
        raise ValueError('Source must name the checkout root')
    revision = git(root,'rev-parse','--verify',data['revision']+'^{commit}').decode().strip()
    baseline = git(root,'rev-parse','--verify',data['baseline']+'^{commit}').decode().strip()
    git(root,'merge-base','--is-ancestor',baseline,revision)
    selected = data.get('inputs', [])
    if not isinstance(selected,list) or len(selected) != len(set(selected)):
        raise ValueError('Inputs must be a unique explicit file list')
    selected_files = []
    for name in selected:
        path = validate_input(root, name)
        selected_files.append((name, path.read_bytes() if path.exists() else None, path.stat().st_mode if path.exists() else None))
    command = data['command']
    if not isinstance(command,list) or not command or not all(isinstance(a,str) and a for a in command):
        raise ValueError('Command must be nonempty argv')
    destination = Path(data['destination']).expanduser().absolute()
    if destination != destination.resolve() or destination.exists() or root == destination or root in destination.parents:
        raise ValueError('Destination must be a new canonical isolated path outside source')
    destination.parent.mkdir(parents=True,exist_ok=True)
    registry = Registry(data.get('registry'))
    output_req = grant(data,root,['output:'+str(destination)])
    output = registry.operate('claim',output_req)['claim']
    # Retain this initial grant even when creation fails; caller can recover from the bounded error.
    state = dict(schemaVersion=1, id=uuid.uuid4().hex, status='setup', source=str(root),
                 revision=revision, baseline=baseline, inputs=selected, registry=str(registry.path),
                 grants=[output], protected=True, selection=data.get('selection',[]))
    try:
        destination.mkdir()
        record = destination/'snapshot.json'
        state['record'] = str(record)
        state['destination'] = str(destination)
        save(record,state)
        checkout = destination/'checkout'
        subprocess.run(['git','clone','--quiet','--no-local','--no-checkout',str(root),str(checkout)],check=True,capture_output=True)
        subprocess.run(['git','-C',str(checkout),'checkout','--quiet','--detach',revision],check=True,capture_output=True)
        # Only explicitly named working inputs replace the selected committed revision.
        for name,content,mode in selected_files:
            target = checkout/name
            if any(parent.is_symlink() for parent in target.parents):
                raise ValueError('Selected destination has a symlink parent')
            if content is not None:
                target.parent.mkdir(parents=True,exist_ok=True)
                if target.is_symlink(): target.unlink()
                target.write_bytes(content)
                target.chmod(mode & 0o777)
            elif target.exists() or target.is_symlink():
                target.unlink()
            else:
                raise ValueError('Selected deletion is absent in the source revision')
        # A committed build/ is still runner output, never a reusable passing receipt.
        if (checkout/'build').exists():
            if (checkout/'build').is_symlink(): raise ValueError('Symlink build output is unsupported')
            shutil.rmtree(checkout/'build')
        # Final ignore policy must include every explicitly selected input in identity.
        for name in selected:
            ignored = subprocess.run(['git','-C',str(checkout),'check-ignore','--no-index','-q','--',name]).returncode
            if ignored != 1:
                raise ValueError('Selected input is excluded by snapshot ignore policy: ' + name)
        resources=['checkout:'+str(checkout)]
        if data.get('simulator'):
            resources.append('simulator:'+data['owner']['hostId']+'/'+data['simulator'])
        state['grants'].append(registry.operate('claim',grant(data,checkout,resources))['claim'])
        installation = checkout/'docs/agents/snapshot-verification-installation.json'
        if installation.exists():
            globals_root = destination/'globals'
            for item in load(installation)['files']:
                original = Path(item['path'])
                if sha(original) != item['after']: raise ValueError('Global installation changed')
                target = globals_root/item['relative']
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(original,target)
            state['globalsRoot'] = str(globals_root)
        state.update(original=capture(root,baseline), snapshot=capture(checkout,baseline,state.get('globalsRoot')),
                     content=entries(checkout), status='running', setupSeconds=round(time.monotonic()-started,6))
        save(record,state)
        environment=dict(os.environ, COMPLETION_BASELINE=baseline,KEEP_TEST_RESULTS='1',
                         DERIVED_DATA_PATH=str(checkout/'build/DerivedData'))
        if state.get('globalsRoot'):
            environment.update(HARNESS_SKILLS_ROOT=state['globalsRoot'], SNAPSHOT_INSTALLED_ROOT=state['globalsRoot'])
        if data.get('simulator'): environment['SIMULATOR_ID']=data['simulator']
        # Build/cache/output is always confined to the disposable checkout's excluded build/.
        with (destination/'runner.log').open('w') as log:
            execution=subprocess.run(command,cwd=checkout,env=environment,stdout=log,stderr=subprocess.STDOUT)
        state['runnerExitCode']=execution.returncode
        state['snapshotAfter']=capture(checkout,baseline,state.get('globalsRoot'))
        state['originalAfter']=capture(root,baseline)
        receipts=sorted((checkout/'build/results/runs').glob('*/run.json'))
        state['tests']=[dict(path=str(p),sha256=sha(p)) for p in receipts]
        valid=bool(receipts) and execution.returncode == 0 and same_source(state['snapshot'],state['snapshotAfter'])
        for path in receipts:
            receipt=load(path)
            valid = valid and inspect(path)['verification']=='passed' and same_source(receipt.get('source'),state['snapshot']) and same_source(receipt.get('sourceAfter'),state['snapshot'])
        state['status']='passed' if valid else 'failed'
        state['wallSeconds']=round(time.monotonic()-started,6)
        state['sourceBytes']=sum(x['bytes'] for x in state['content'])
        save(record,state)
        return state
    except (OSError,ValueError,subprocess.SubprocessError,OwnershipError) as error:
        state.update(status='failed', error=error.result if isinstance(error,OwnershipError) else type(error).__name__,
                     recovery='retain diagnostics and grants; release using current owner credentials')
        if destination.is_dir(): save(destination/'snapshot.json',state)
        return state


def checked_run(path):
    state=load(path)
    checkout=state['snapshot']['checkout']
    if state['status']!='passed' or not same_source(capture(checkout,state['baseline'],state.get('globalsRoot')),state['snapshot']) or entries(checkout)!=state['content']:
        raise ValueError('Snapshot is unavailable, changed, failed or released')
    for test in state['tests']:
        if sha(test['path'])!=test['sha256'] or inspect(Path(test['path']))['verification']!='passed':
            raise ValueError('Test evidence changed')
    return state


def mapping(data):
    state=checked_run(data['run'])
    target=capture(Path(data['target']).resolve(),state['baseline'])
    if any(target[k]!=state['snapshot'][k] for k in ('baseline','algorithm','excluded','fingerprint','installed')):
        raise ValueError('Integration target differs from tested content')
    git(target['checkout'],'merge-base','--is-ancestor',state['revision'],target['revision'])
    reviews=[]
    for path in data.get('reviews',[]):
        review=load(path)
        if not same_source(review.get('source'),state['snapshot']):
            raise ValueError('Review differs from snapshot')
        git(state['snapshot']['checkout'],'merge-base','--is-ancestor',review['source']['revision'],state['revision'])
        report = Path(review['reference'])
        if not report.is_absolute(): report = Path(path).resolve().parent/report
        if not report.is_file(): raise ValueError('Snapshot mapping requires a retained local review report')
        reviews.append(dict(path=str(Path(path).resolve()),sha256=sha(path),
                            report=dict(path=str(report.resolve()),sha256=sha(report))))
    return dict(schemaVersion=1, kind='checked-snapshot-equivalence-v1', run=str(Path(data['run']).resolve()),
                runSha256=sha(data['run']), snapshot=state['snapshot'], target=target,tests=state['tests'],reviews=reviews)


def release(data):
    path=Path(data['run']); state=load(path)
    if data.get('owner')!=state['grants'][0]['owner']:
        raise ValueError('Wrong snapshot owner')
    if state.get('released'): return dict(status='released',testStatus=state['status'],run=str(path))
    # Release is explicit, conservative, and never deletes evidence. Persist each completed member.
    registry=Registry(state['registry'])
    for claim in reversed(state['grants']):
        if claim.get('released'): continue
        registry.operate('release',dict(claim,schemaVersion=1))
        claim['released']=True
        save(path,state)
    state['released']=True
    save(path,state)
    return dict(status='released',testStatus=state['status'],run=str(path))


def cleanup(data):
    state=load(data['run'])
    # Existing retention defaults protect every snapshot. Unknown/referenced/failed/active evidence stays.
    return dict(status='preserved', testStatus=state['status'], run=data['run'],
                reason='protected snapshot evidence; explicit release retains source and diagnostics',
                released=state.get('released',False))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['run','map','release','cleanup'])
    args=parser.parse_args()
    data=json.loads(sys.stdin.read(1024*1024+1))
    result={'run':run,'map':mapping,'release':release,'cleanup':cleanup}[args.operation](data)
    print(json.dumps(result,indent=2))
    return 0 if result.get('status')!='failed' else 2


if __name__=='__main__':
    try: sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError,OwnershipError) as error:
        print(json.dumps(error.result if isinstance(error,OwnershipError) else dict(status='blocked',error=type(error).__name__,reason=str(error)[:300])))
        sys.exit(2)
