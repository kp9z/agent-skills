#!/usr/bin/env python3
"""Collect completion evidence locally; no tracker mutations or authorization decisions."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys

from test_results import inspect, describe


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)


def installed_files(root, installed_root=None):
    """Adapter-maintained installation pins are source; verify their actual installed bytes."""
    manifest = Path(root) / 'docs/agents/snapshot-verification-installation.json'
    if not manifest.exists():
        return []
    result = []
    for item in load(manifest)['files']:
        path = Path(installed_root) / item['relative'] if installed_root else Path(item['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['after']:
            raise ValueError('Installed helper differs from pinned source: ' + str(path))
        result.append(dict(path=item['path'], sha256=item['after']))
    return result


def source_identity(root, baseline, excluded=(), installed_root=None):
    """Hash working bytes, paths and modes, including nonignored untracked files/deletions.

    Index/HEAD metadata is recorded separately: committing identical bytes preserves identity.
    Exclusions are runner-owned generated directories, never caller-supplied receipt claims.
    """
    root = Path(root).resolve()
    baseline = git(root, 'rev-parse', '--verify', baseline + '^{commit}').decode().strip()
    names = set(git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard').split(b'\0')) - {b''}
    digest = hashlib.sha256()
    for name in sorted(names):
        relative = os.fsdecode(name)
        if any(relative == prefix or relative.startswith(prefix + '/') for prefix in excluded):
            continue
        path = root / relative
        if path.is_symlink():
            mode, content = b'link', os.fsencode(os.readlink(path))
        elif path.is_file():
            mode = b'executable' if path.stat().st_mode & 0o111 else b'file'
            content = path.read_bytes()
        elif not path.exists():
            # A tracked deletion and its subsequent commit have identical source identity.
            continue
        else:
            raise ValueError(f'Unsupported source entry (including submodule): {relative}')
        for value in (name, mode, content):
            digest.update(str(len(value)).encode() + b':' + value)
    return dict(checkout=str(root), baseline=baseline,
                revision=git(root, 'rev-parse', 'HEAD').decode().strip(),
                fingerprint=digest.hexdigest(), algorithm='git-working-bytes-v1', excluded=list(excluded), installed=installed_files(root, installed_root))


def load(path):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f'Expected JSON object: {path}')
    return data


def same_source(a, b):
    keys = ('checkout', 'baseline', 'fingerprint', 'algorithm', 'excluded', 'installed')
    return isinstance(a, dict) and all(a.get(k) == b.get(k) for k in keys)


def checked_mapping(mapping, current, base, tests, reviews):
    """Recompute both checkouts and pin run/test/review bytes, rather than trust a claim."""
    def path(ref):
        value = Path(ref)
        return value if value.is_absolute() else base / value
    def hashed(ref, expected):
        value = path(ref)
        if hashlib.sha256(value.read_bytes()).hexdigest() != expected:
            raise ValueError('Mapped evidence bytes changed')
        return value
    if mapping.get('kind') != 'checked-snapshot-equivalence-v1' or mapping.get('schemaVersion') != 1:
        raise ValueError('Unsupported snapshot mapping')
    run_path = hashed(mapping['run'], mapping['runSha256'])
    run = load(run_path)
    snapshot = run['snapshot']
    if run['status'] != 'passed' or not same_source(run['snapshotAfter'], snapshot):
        raise ValueError('Snapshot run did not pass on fixed input')
    # Exclusions come from the adapter currently performing verification, never from evidence.
    actual = source_identity(snapshot['checkout'], current['baseline'], current['excluded'], run.get('globalsRoot'))
    if not same_source(actual, snapshot) or not same_source(mapping['snapshot'], snapshot):
        raise ValueError('Snapshot content changed or mapping names different input')
    if not same_source(mapping['target'], current):
        raise ValueError('Integration checkout changed after mapping')
    for key in ('baseline', 'fingerprint', 'algorithm', 'excluded', 'installed'):
        if snapshot[key] != current[key]:
            raise ValueError('Integration content is not equivalent')
    if run['baseline'] != current['baseline'] or run['revision'] != snapshot['revision']:
        raise ValueError('Revision/baseline provenance differs')
    git(snapshot['checkout'], 'cat-file', '-e', snapshot['revision'] + '^{commit}')
    git(current['checkout'], 'merge-base', '--is-ancestor', snapshot['revision'], current['revision'])
    for declared, pinned in ((tests, run['tests']), (reviews, mapping['reviews'])):
        if {str(path(ref).resolve()) for ref in declared} != {str(path(item['path']).resolve()) for item in pinned}:
            raise ValueError('Mapped test/review inventory differs')
        for item in pinned:
            hashed(item['path'], item['sha256'])
    for item in mapping['reviews']:
        review = load(path(item['path']))
        reference = Path(review['reference'])
        if not reference.is_absolute(): reference = path(item['path']).resolve().parent/reference
        if str(reference.resolve()) != item['report']['path']:
            raise ValueError('Review report provenance differs')
        hashed(item['report']['path'], item['report']['sha256'])
    return snapshot


def evaluate(manifest, current, base):
    """Judgments are supplied attestations; validate provenance/coverage, never invent them."""
    for key in ('tests', 'reviews', 'requiredReviewScopes', 'acceptance', 'missingChecks', 'exceptions'):
        if not isinstance(manifest.get(key, []), list):
            raise ValueError(f'{key} must be an array')
    for key in ('acceptance', 'exceptions'):
        if not all(isinstance(item, dict) for item in manifest.get(key, [])):
            raise ValueError(f'{key} entries must be objects')
    for key in ('tests', 'reviews', 'requiredReviewScopes', 'missingChecks'):
        if not all(isinstance(item, str) and item.strip() for item in manifest.get(key, [])):
            raise ValueError(f'{key} entries must be nonempty strings')
    reasons, missing, evidence = [], [], []
    mapped = None
    if 'provenance' in manifest:
        try:
            mapped = checked_mapping(manifest['provenance'], current, base, manifest.get('tests', []), manifest.get('reviews', []))
        except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
            reasons.append(dict(reason='Invalid snapshot provenance: ' + str(error), evidence='manifest.provenance'))
    def gap(message, ref=None, inconsistent=False):
        (reasons if inconsistent else missing).append(dict(reason=message, evidence=ref))
    def read(ref):
        path = Path(ref)
        path = path if path.is_absolute() else base / path
        return load(path), path
    def check_source(value, ref):
        if not isinstance(value, dict) or not value.get('revision'):
            gap('Source identity missing', ref)
        elif not same_source(value, current) and not (mapped and same_source(value, mapped)):
            gap('Source identity differs from current checkout/baseline/bytes', ref, True)
        else:
            try:
                if not re.fullmatch(r'[0-9a-f]{40,64}', value['revision']):
                    raise ValueError('Expected full commit SHA')
                git(current['checkout'], 'merge-base', '--is-ancestor', value['revision'], current['revision'])
            except (ValueError, subprocess.CalledProcessError):
                gap('Source revision cannot be resolved', ref, True)
    def references(refs, label):
        if not isinstance(refs, list) or not refs:
            gap(f'{label} evidence references required')
            return
        for ref in refs:
            if not isinstance(ref, str) or not ref.strip():
                gap(f'{label} invalid evidence reference')
            elif not re.match(r'^[a-z][a-z0-9+.-]*://\S+$', ref, re.I):
                path = Path(ref)
                if not (path if path.is_absolute() else base / path).is_file():
                    gap(f'{label} evidence file unavailable', ref)
    ticket, worker = manifest.get('ticket'), manifest.get('worker')
    if not ticket or not worker:
        gap('Ticket and worker identities required')
    check_source(manifest.get('source'), 'manifest.source')
    tests = manifest.get('tests', [])
    if not tests:
        gap('No required test receipts declared')
    for ref in tests:
        try:
            receipt, path = read(ref)
            result = inspect(path)
            evidence.append(dict(kind='test', reference=str(path), result=result,
                                 source=receipt.get('source'), sourceAfter=receipt.get('sourceAfter')))
            check_source(receipt.get('source'), str(path))
            check_source(receipt.get('sourceAfter'), str(path))
            if result['verification'] != 'passed':
                gap('Test execution incomplete, failed, skipped or mismatched', str(path))
        except (OSError, ValueError, TypeError, KeyError) as error:
            gap(f'Cannot inspect test receipt: {error}', str(ref))
    scopes = manifest.get('requiredReviewScopes', [])
    if not scopes or len(scopes) != len(set(scopes)):
        gap('Declare unique required independent review scopes')
    covered = set()
    for ref in manifest.get('reviews', []):
        try:
            review, path = read(ref)
            evidence.append(dict(kind='review', reference=str(path), record=review))
            check_source(review.get('source'), str(path))
            if review.get('ticket') != ticket:
                gap('Review ticket mismatch', str(path), True)
            if not review.get('reviewer') or review['reviewer'] == worker:
                gap('Independent reviewer identity required', str(path))
            elif review.get('judgment') != 'approved' or not review.get('reference'):
                gap('Review approval/reference missing or unresolved findings remain', str(path))
            else:
                references([review['reference']], 'Review')
                covered.update(review.get('scopes', []))
        except (OSError, ValueError, TypeError, KeyError) as error:
            gap(f'Cannot inspect review: {error}', str(ref))
    for scope in sorted(set(scopes) - covered):
        gap(f'Independent review missing: {scope}')
    criteria = manifest.get('acceptance', [])
    ids = [item.get('id') for item in criteria]
    if not ids or not all(ids) or len(ids) != len(set(ids)):
        gap('Declare unique acceptance criteria from the agreed specification')
    for item in criteria:
        references(item.get('evidence'), f'Acceptance {item.get("id")}')
        check_source(item.get('source'), f'acceptance:{item.get("id")}')
        if item.get('result') != 'passed' or not item.get('evidence'):
            gap(f'Acceptance unverified: {item.get("id")}', item.get('evidence'))
    for check in manifest.get('missingChecks', []):
        gap(f'Missing check: {check}')
    # Exceptions document a decision, never turn missing evidence into verification.
    for exception in manifest.get('exceptions', []):
        gap('User exception preserves an unverified check', exception.get('reference'))
        if not exception.get('reference') or not exception.get('reason'):
            gap('Explicit exception requires user reference and reason')
    if manifest.get('tracker', {}).get('availability') == 'live' and manifest['tracker'].get('issue', {}).get('url') != ticket:
        gap('Live tracker ticket mismatch', ticket, True)
    status = 'inconsistent' if reasons else 'incomplete' if missing else 'verified'
    record = dict(schemaVersion=1, status=status, ticket=ticket, worker=worker,
                  recordedAt=datetime.now(timezone.utc).isoformat(), source=current,
                  declaredSource=manifest.get('source'), evidence=evidence,
                  requiredReviewScopes=scopes, missingChecks=manifest.get('missingChecks', []),
                  acceptance=criteria, exceptions=manifest.get('exceptions', []),
                  tracker=manifest.get('tracker', {'availability': 'not requested'}),
                  reasons=reasons + missing,
                  limits='Local attestations, not signatures. Scope completeness and independent judgments require human review. No authorization or tracker mutation is implied.')
    record['summary'] = summarize(record)
    return record


def summarize(record):
    lines = [f'{record.get("ticket")}: {record["status"]}',
             f'Source: {record["source"]["revision"][:12]} / {record["source"]["fingerprint"][:12]}',
             f'Evidence: {len(record["evidence"])} receipts; acceptance: {sum(x.get("result") == "passed" and bool(x.get("evidence")) for x in record["acceptance"])}/{len(record["acceptance"])}']
    for entry in record['evidence']:
        if entry['kind'] == 'test':
            lines.append('- Test: ' + describe(entry['result']))
        else:
            review = entry['record']
            revision = (review.get('source') or {}).get('revision', 'unknown')
            lines.append(f'- Review: {review.get("judgment")} by {review.get("reviewer")} at {revision[:12]} ({entry["reference"]}; {review.get("reference")})')
    for item in record['acceptance']:
        lines.append(f'- Acceptance {item.get("id")}: {item.get("result")} ({item.get("evidence")})')
    tracker = record['tracker']
    lines.append(f'Tracker: {tracker.get("availability", "supplied snapshot")}' +
                 (f' / {tracker["issue"].get("state")} at {tracker.get("observedAt")}' if 'issue' in tracker else ''))
    lines += [f'- {x["reason"]}' + (f' ({x["evidence"]})' if x.get('evidence') else '') for x in record['reasons']]
    lines += [f'- User exception: {x.get("reason")} ({x.get("reference")})' for x in record['exceptions']]
    return '\n'.join(lines)


def main(root=None, excluded=()):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, default=root or Path.cwd())
    commands = parser.add_subparsers(dest='command', required=True)
    capture = commands.add_parser('source', help='Capture identity for a reviewer or acceptance observer')
    capture.add_argument('--baseline', required=True)
    review = commands.add_parser('review', help='Package a reviewer judgment against a captured source identity')
    review.add_argument('--source', type=Path, required=True)
    review.add_argument('--ticket', required=True)
    review.add_argument('--reviewer', required=True)
    review.add_argument('--scope', action='append', required=True)
    review.add_argument('--judgment', choices=['approved', 'changes-requested', 'incomplete'], required=True)
    review.add_argument('--reference', required=True)
    init = commands.add_parser('init', help='Emit an incomplete worker manifest; fill it once')
    init.add_argument('--baseline', required=True)
    init.add_argument('--ticket', required=True)
    init.add_argument('--worker', required=True)
    verify = commands.add_parser('verify', help='Re-read evidence and current bytes; emit shared JSON record')
    verify.add_argument('manifest', type=Path)
    verify.add_argument('--refresh-tracker', action='store_true', help='Read live GitHub state via gh; ticket must be an issue URL')
    summary = commands.add_parser('summary', help='Render a saved record snapshot without revalidation')
    summary.add_argument('record', type=Path)
    args = parser.parse_args()
    if args.command == 'summary':
        print(summarize(load(args.record)))
        return 0
    if args.command == 'review':
        data = dict(ticket=args.ticket, reviewer=args.reviewer, scopes=args.scope, judgment=args.judgment,
                    reference=args.reference, source=load(args.source))
    elif args.command in ('source', 'init'):
        source = source_identity(args.checkout, args.baseline, excluded)
        data = source if args.command == 'source' else dict(schemaVersion=1, ticket=args.ticket, worker=args.worker,
            source=source, tests=[], requiredReviewScopes=['standards', 'spec'], reviews=[],
            acceptance=[], missingChecks=[], exceptions=[])
    else:
        manifest = load(args.manifest)
        source = source_identity(args.checkout, manifest['source']['baseline'], excluded)
        if args.refresh_tracker:
            try:
                if not re.fullmatch(r'https://[^/]+/[^/]+/[^/]+/issues/[0-9]+', manifest['ticket']):
                    raise ValueError('Live tracker read requires an issue URL')
                result = subprocess.run(['gh', 'issue', 'view', manifest['ticket'], '--json', 'url,state,stateReason,updatedAt'],
                                        check=True, capture_output=True, text=True, timeout=30)
                manifest['tracker'] = dict(availability='live', observedAt=datetime.now(timezone.utc).isoformat(), issue=json.loads(result.stdout))
            except (OSError, ValueError, subprocess.SubprocessError):
                manifest['tracker'] = dict(availability='unavailable')
        elif 'tracker' in manifest:
            manifest['tracker'] = dict(availability='supplied snapshot', snapshot=manifest['tracker'])
        data = evaluate(manifest, source, args.manifest.resolve().parent)
        data['manifest'] = str(args.manifest.resolve())
    if args.command == 'verify' and 'provenance' in manifest:
        data['provenance'] = manifest['provenance']
    print(json.dumps(data, indent=2))
    return 0 if data.get('status', 'verified') == 'verified' else 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, KeyError, subprocess.CalledProcessError) as error:
        print(json.dumps({'status': 'incomplete', 'error': str(error)}))
        sys.exit(2)
