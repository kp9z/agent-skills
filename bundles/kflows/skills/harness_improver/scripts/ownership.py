#!/usr/bin/env python3
"""Cooperative local ownership. JSON stdin/stdout; no device or network effects."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

VERSION = 1
LIMIT = 1024 * 1024


class OwnershipError(Exception):
    def __init__(self, code, **details):
        self.result = dict(status='blocked', error=code, **details)


def fail(code, **details):
    raise OwnershipError(code, **details)


def string(value, maximum=512):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        fail('invalid_input')
    return value


def identity(value):
    if not isinstance(value, dict) or set(value) != {'chatId', 'hostId'}:
        fail('invalid_identity')
    return {key: string(value[key], 128) for key in ('chatId', 'hostId')}


def references(values):
    if not isinstance(values, list) or len(values) > 8:
        fail('invalid_evidence')
    return [string(value) for value in values]


def checkout(path):
    path = Path(string(path)).expanduser()
    if not path.is_absolute() or not path.is_dir():
        fail('invalid_checkout')
    try:
        root = subprocess.check_output(['git', '-C', str(path.resolve()), 'rev-parse', '--show-toplevel'], stderr=subprocess.PIPE).decode().strip()
    except subprocess.CalledProcessError:
        fail('invalid_checkout')
    return str(Path(root).resolve())


def resource(value, host):
    kind, separator, name = string(value).partition(':')
    if not separator:
        fail('invalid_resource')
    if kind == 'checkout':
        return 'checkout:' + checkout(name)
    if kind == 'output':
        path = Path(name).expanduser()
        if not path.is_absolute():
            fail('invalid_resource')
        return 'output:' + str(path.resolve())
    if kind == 'simulator':
        device_host, separator, device = name.partition('/')
        if not separator or device_host != host or not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', device):
            fail('invalid_resource')
        return 'simulator:' + device_host + '/' + device.lower()
    fail('invalid_resource')


def request(data):
    if not isinstance(data, dict) or type(data.get('schemaVersion')) is not int or data['schemaVersion'] != VERSION:
        fail('unsupported_schema')
    owner = identity(data.get('owner'))
    root = checkout(data.get('checkout'))
    resources = data.get('resources')
    if not isinstance(resources, list) or not 1 <= len(resources) <= 16:
        fail('invalid_resources')
    resources = sorted(set(resource(value, owner['hostId']) for value in resources))
    # Device-only handoffs still identify the worker's checkout without claiming it again.
    return dict(owner=owner, checkout=root, branch=string(data.get('branch'), 256),
                phase=string(data.get('phase'), 128), pendingAction=string(data.get('pendingAction'), 256),
                resources=resources, evidence=references(data.get('evidence', [])),
                budgetReceipts=references(data.get('budgetReceipts', [])))


def fingerprint(raw):
    return hashlib.sha256(raw).hexdigest()


def default_registry():
    return Path(os.environ.get('HARNESS_OWNERSHIP_REGISTRY', '~/.local/state/codex-harness/ownership.json')).expanduser()


class Registry:
    def __init__(self, path=None):
        # Resolve registry aliases too; all participants must use the same registry inode namespace.
        self.path = Path(path or default_registry()).expanduser().resolve()
        self.pending = self.path.with_name(self.path.name + '.pending')
        self.lock = self.path.with_name(self.path.name + '.lock')

    @contextmanager
    def locked(self, recovering=False):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock.open('a+b') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            if self.pending.exists() and not recovering:
                fail('interrupted_write', recovery='reconcile with reviewed evidence and current fingerprint')
            raw = self.path.read_bytes() if self.path.exists() else b''
            if len(raw) > LIMIT:
                fail('corrupt_state')
            if not raw:
                if self.path.exists():
                    fail('corrupt_state')
                state = dict(schemaVersion=VERSION, generation=0, claims=[], dispatches={})
            else:
                try:
                    state = json.loads(raw)
                    self.validate(state)
                except (ValueError, TypeError, KeyError, OwnershipError):
                    fail('corrupt_or_unsupported_state', fingerprint=fingerprint(raw), recovery='preserve files; restore only a reviewed complete ownership snapshot')
            yield state, fingerprint(raw)

    def validate(self, state):
        if not isinstance(state, dict) or type(state.get('schemaVersion')) is not int or state['schemaVersion'] != VERSION or type(state.get('generation')) is not int or state['generation'] < 0:
            fail('corrupt_state')
        claims, dispatches = state['claims'], state['dispatches']
        if not isinstance(claims, list) or len(claims) > 32 or not isinstance(dispatches, dict) or len(dispatches) > 128:
            fail('corrupt_state')
        seen = set()
        for claim in claims:
            # Validate structure without resolving paths: a removed checkout never releases its claims.
            identity(claim['owner'])
            for key in ('checkout', 'branch', 'phase', 'pendingAction', 'token'):
                string(claim[key])
            if type(claim['generation']) is not int or not 0 < claim['generation'] <= state['generation']:
                fail('corrupt_state')
            if not isinstance(claim['resources'], list) or not 1 <= len(claim['resources']) <= 16:
                fail('corrupt_state')
            for value in claim['resources']:
                string(value)
                if value in seen:
                    fail('corrupt_state')
                seen.add(value)
            references(claim['evidence'])
            references(claim['budgetReceipts'])
        for key, record in dispatches.items():
            string(key, 128)
            if not isinstance(record, dict) or record.get('status') not in ('prepared', 'attached'):
                fail('corrupt_state')
            identity(record['owner'])
            string(record['token'])
            if type(record['generation']) is not int or not 0 < record['generation'] <= state['generation']:
                fail('corrupt_state')
            string(record['cursor'], 512)
            string(record['authorizationRef'])
            string(record['phase'], 128)
            string(record['pendingAction'], 256)
            if not isinstance(record['resources'], list) or not 1 <= len(record['resources']) <= 16:
                fail('corrupt_state')
            for value in record['resources']:
                string(value)

    def sync_directory(self):
        fd = os.open(self.path.parent, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def write(self, state):
        self.validate(state)
        raw = json.dumps(state, sort_keys=True, separators=(',', ':')).encode()
        if len(raw) > LIMIT:
            fail('registry_full')
        # The durable pending file is also the replacement payload. A crash anywhere
        # after its creation is explicit ambiguity; never infer that ownership is free.
        with self.pending.open('xb') as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        self.sync_directory()
        os.replace(self.pending, self.path)
        self.sync_directory()

    def view(self, state, resources):
        observations = [dict(resource=value, owner=claim['owner'], generation=claim['generation'])
                        for claim in state['claims'] for value in claim['resources'] if value in resources]
        return sorted(observations, key=lambda item: item['resource'])

    def find(self, state, data, req):
        token = string(data.get('token'))
        generation = data.get('generation')
        if type(generation) is not int or generation < 1:
            fail('invalid_generation')
        for claim in state['claims']:
            if claim['token'] == token and claim['generation'] == generation and claim['owner'] == req['owner'] and set(req['resources']) <= set(claim['resources']):
                if any(claim[key] != req[key] for key in ('checkout', 'branch')):
                    fail('ownership_mismatch')
                return claim
        fail('stale_or_wrong_owner', conflicts=self.view(state, req['resources']))

    def claim(self, state, req):
        matches = [claim for claim in state['claims'] if set(claim['resources']) & set(req['resources'])]
        if len(matches) == 1 and all(matches[0].get(key) == value for key, value in req.items()):
            return matches[0]
        if matches:
            fail('conflict', conflicts=self.view(state, req['resources']))
        if len(state['claims']) >= 32:
            fail('registry_full')
        state['generation'] += 1
        claim = dict(req, token=secrets.token_urlsafe(32), generation=state['generation'])
        state['claims'].append(claim)
        return claim

    def operate(self, operation, data):
        req = request(data)
        with self.locked(recovering=operation == 'reconcile') as (state, digest):
            if operation == 'claim':
                claim = self.claim(state, req)
                self.write(state)
                return dict(status='owned', claim=claim)
            if operation == 'release':
                claim = self.find(state, data, req)
                remaining = sorted(set(claim['resources']) - set(req['resources']))
                if remaining:
                    claim['resources'] = remaining
                else:
                    state['claims'].remove(claim)
                self.write(state)
                return dict(status='released', resources=req['resources'], generation=state['generation'])
            if operation == 'reconcile':
                observed = self.view(state, req['resources'])
                expected = data.get('expected')
                if not isinstance(expected, list) or len(expected) > 16:
                    fail('invalid_expectation')
                for item in expected:
                    if not isinstance(item, dict) or set(item) != {'resource', 'owner', 'generation'}:
                        fail('invalid_expectation')
                    string(item['resource'])
                    identity(item['owner'])
                    if type(item['generation']) is not int or item['generation'] < 1:
                        fail('invalid_expectation')
                if observed != expected:
                    fail('disagreement', observed=observed, fingerprint=digest)
                if data.get('recoverInterrupted'):
                    identity(data.get('reviewer'))
                    if not req['evidence'] or data.get('expectedFingerprint') != digest:
                        fail('recovery_evidence_required', fingerprint=digest)
                    # Retain the last atomically published state, never staged new claims.
                    # A prepared dispatch remains prepared, even if chat creation succeeded.
                    if self.pending.exists():
                        self.pending.unlink()
                        self.sync_directory()
                elif self.pending.exists():
                    fail('interrupted_write', fingerprint=digest, observed=observed)
                return dict(status='reconciled', observed=observed, fingerprint=digest,
                            evidence=req['evidence'], budgetReceipts=req['budgetReceipts'])
            fail('invalid_operation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=default_registry())
    parser.add_argument('operation', choices=['claim', 'release', 'reconcile'])
    args = parser.parse_args()
    data = json.loads(sys.stdin.read(LIMIT + 1))
    result = Registry(args.registry).operate(args.operation, data)
    result.update(schemaVersion=VERSION, registry=str(Registry(args.registry).path))
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except OwnershipError as error:
        print(json.dumps(error.result))
        sys.exit(2)
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps(dict(status='blocked', error='io_or_invalid_json', recovery='preserve registry and pending files; inspect permissions and reconcile')))
        sys.exit(2)
