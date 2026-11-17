#!/usr/bin/env python3
"""Marathon dispatch/resume boundary. Effects are supplied by the chat-tool caller."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'harness_improver/scripts'))
from ownership import (LIMIT, VERSION, OwnershipError, Registry, default_registry, fail,
                       identity, request, string)


class Marathon:
    def __init__(self, registry=None):
        self.registry = Registry(registry)

    def result(self, record, status):
        return dict(status=status, schemaVersion=VERSION, worker=record,
                    credentials=dict(token=record['token'], generation=record['generation']))

    def record(self, state, data):
        key = string(data.get('dispatchId'), 128)
        if key not in state['dispatches']:
            fail('unknown_dispatch')
        return state['dispatches'][key]

    def prepare(self, data):
        req = request(data)
        key = string(data.get('dispatchId'), 128)
        authorization = string(data.get('authorizationRef'))
        cursor = string(data.get('cursor'))
        with self.registry.locked() as (state, _):
            if key in state['dispatches']:
                record = state['dispatches'][key]
                if record['assignment'] != req or record['authorizationRef'] != authorization:
                    fail('dispatch_disagreement')
                return self.result(record, 'existing_worker' if record['status'] == 'attached' else 'pending_dispatch')
            if len(state['dispatches']) >= 128:
                fail('registry_full')
            claim = self.registry.claim(state, req)
            if any(item['token'] == claim['token'] for item in state['dispatches'].values()):
                fail('claim_already_dispatched')
            record = dict(status='prepared', owner=req['owner'], token=claim['token'], generation=claim['generation'],
                          resources=req['resources'], cursor=cursor, authorizationRef=authorization,
                          phase=req['phase'], pendingAction=req['pendingAction'], assignment=req)
            state['dispatches'][key] = record
            self.registry.write(state)
            return self.result(record, 'prepared')

    def attach(self, data):
        req = request(data)
        worker = identity(data.get('worker'))
        cursor = string(data.get('workerCursor'))
        if worker['hostId'] != req['owner']['hostId']:
            fail('host_mismatch')
        with self.registry.locked() as (state, _):
            record = self.record(state, data)
            if record['status'] != 'prepared' or record['assignment'] != req:
                fail('dispatch_disagreement')
            claim = self.registry.find(state, data, req)
            state['claims'].remove(claim)
            new_claim = self.registry.claim(state, dict(req, owner=worker, pendingAction='worker execution'))
            record.update(status='attached', owner=worker, cursor=cursor, token=new_claim['token'],
                          generation=new_claim['generation'], pendingAction='worker execution')
            self.registry.write(state)
            return self.result(record, 'attached')

    def dispatch(self, data, create_worker):
        prepared = self.prepare(data)
        if prepared['status'] != 'prepared':
            return prepared
        # Intent is durable before the external call. Exceptions/unknown delivery retain it.
        # Resume a pending dispatch by attaching its observed chat; never call create again.
        worker = create_worker(dict(data, ownership=prepared, routineTestingAuthorization=data['authorizationRef']))
        return self.attach(dict(data, **prepared['credentials'], worker=identity({key: worker[key] for key in ('chatId', 'hostId')}),
                                workerCursor=worker['cursor']))

    def resume(self, data, effect=None):
        req = request(data)
        with self.registry.locked() as (state, _):
            record = self.record(state, data)
            if record['status'] != 'attached' or any(record[key] != data.get(key) for key in ('token', 'generation')) or record['owner'] != req['owner']:
                fail('stale_worker')
            if not set(req['resources']) <= set(record['resources']):
                fail('unassigned_resource')
            claim = self.registry.find(state, data, req)
            if data.get('cursor') != record['cursor']:
                fail('stale_cursor', cursor=record['cursor'])
            if data.get('authorizationRef') != record['authorizationRef']:
                fail('authorization_disagreement')
            if 'nextCursor' in data:
                record['cursor'] = string(data['nextCursor'])
            record.update(phase=req['phase'], pendingAction=req['pendingAction'])
            claim.update(phase=req['phase'], pendingAction=req['pendingAction'])
            self.registry.write(state)
            permit = dict(self.result(record, 'resumable'), cursor=record['cursor'],
                          authorizationRef=record['authorizationRef'], resources=req['resources'])
            # The public in-process boundary holds the lock across the supplied effect,
            # so a participating handoff cannot race this operation. CLI permits require
            # the worker to recheck immediately before each operation (cooperative limit).
            if effect is not None:
                effect(permit)
            return permit

    def reassign(self, data):
        req = request(data)
        with self.registry.locked() as (state, _):
            record = self.record(state, data)
            if record['status'] != 'attached' or record['owner'] != req['owner'] or any(record[key] != data.get(key) for key in ('token', 'generation')):
                fail('stale_worker')
            if data.get('cursor') != record['cursor'] or data.get('authorizationRef') != record['authorizationRef']:
                fail('worker_state_disagreement')
            if any(claim['token'] == record['token'] for claim in state['claims']):
                fail('explicit_release_required')
            claim = self.registry.claim(state, req)
            record.update(token=claim['token'], generation=claim['generation'], resources=req['resources'],
                          phase=req['phase'], pendingAction=req['pendingAction'])
            self.registry.write(state)
            return self.result(record, 'reassigned')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registry', type=Path, default=default_registry())
    parser.add_argument('operation', choices=['prepare', 'attach', 'resume', 'reassign'])
    args = parser.parse_args()
    data = json.loads(sys.stdin.read(LIMIT + 1))
    result = getattr(Marathon(args.registry), args.operation)(data)
    result['registry'] = str(Registry(args.registry).path)
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except OwnershipError as error:
        print(json.dumps(error.result))
        sys.exit(2)
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps(dict(status='blocked', error='io_or_invalid_json', recovery='retain dispatch identity and reconcile; never repeat unknown chat creation')))
        sys.exit(2)
