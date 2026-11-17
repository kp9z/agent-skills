#!/usr/bin/env python3
"""Inspect existing runner receipts and extract bounded test-log failures."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ERROR = re.compile(r"error:|XCTAssert.*failed|Test Case '[^'\n]*' failed\b|failed to (?:launch|start)|TEST (?:EXECUTE )?FAILED|Testing failed:", re.I)
COMPILER = re.compile(r"\.(?:swift|m|mm|c|cc|cpp|h):\d+(?::\d+)?: error:|fatal error:", re.I)


def source_verification(data, chars=500):
    before, after = data.get('source'), data.get('sourceAfter')
    if before is None and after is None:
        return {'state': 'unknown', 'detail': 'Legacy execution-only receipt; source-bound completion is not established.'}
    if before is None or after is None:
        return {'state': 'unknown', 'detail': 'Both source and sourceAfter are required.'}
    def valid(value):
        return (isinstance(value, dict)
                and all(isinstance(value.get(k), str) for k in ('checkout', 'baseline', 'revision', 'algorithm', 'fingerprint'))
                and value['checkout'].startswith('/')
                and re.fullmatch(r'[0-9a-f]{40,64}', value['baseline'])
                and re.fullmatch(r'[0-9a-f]{40,64}', value['revision'])
                and re.fullmatch(r'[0-9a-f]{64}', value['fingerprint'])
                and isinstance(value.get('excluded'), list)
                and all(isinstance(x, str) for x in value['excluded'])
                and isinstance(value.get('installed', []), list)
                and all(isinstance(x, dict) and isinstance(x.get('path'), str)
                        and isinstance(x.get('sha256'), str) and re.fullmatch(r'[0-9a-f]{64}', x['sha256'])
                        for x in value.get('installed', [])))
    if not valid(before) or not valid(after):
        return {'state': 'invalid', 'detail': 'Malformed source identity; inspect source/sourceAfter in the receipt.'}
    if (before['algorithm'] != 'git-working-bytes-v1'
            or any(before.get(k, []) != after.get(k, []) for k in ('checkout', 'baseline', 'algorithm', 'excluded', 'installed'))):
        return {'state': 'unknown', 'detail': 'Incomparable source scope or unsupported algorithm.'}
    changed = before['fingerprint'] != after['fingerprint']
    return {'state': 'changed' if changed else 'matching',
            'detail': 'Comparable receipt identities differ.' if changed else 'Receipt identities match; completion still validates current source and reviews.',
            'fields': ['source.fingerprint', 'sourceAfter.fingerprint'],
            'scope': dict(checkout=clipped(before['checkout'], chars), baseline=before['baseline'],
                          algorithm=before['algorithm'], excluded_count=len(before['excluded']),
                          installed_count=len(before.get('installed', [])),
                          checkout_truncated=len(before['checkout']) > chars),
            'before': {k: before[k] for k in ('fingerprint', 'revision')},
            'after': {k: after[k] for k in ('fingerprint', 'revision')}}


# Input caps bound inspection work as well as output; partial coverage never proves a pass.
RECEIPT_BYTES = 8 * 1024 * 1024
LOG_BYTES = 2 * 1024 * 1024
LINE_BYTES = 4096
UNIQUE_ERRORS = 4096


def clipped(value, chars):
    return ''.join(c if c.isprintable() else '?' for c in str(value))[:chars]


def inspect(receipt=None, log=None, limit=8, chars=500):
    if not 1 <= limit <= 50 or not 1 <= chars <= 10000:
        raise ValueError('Invalid output limits')
    data = {}
    if receipt:
        with receipt.open('rb') as stream:
            raw = stream.read(RECEIPT_BYTES + 1)
        if len(raw) > RECEIPT_BYTES:
            raise ValueError('Receipt exceeds inspection limit')
        data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError('Receipt must be an object')
    if log is None and receipt:
        candidate = receipt.parent / 'test.log'
        log = candidate if candidate.exists() else None
    errors, seen = [], set()
    compiler = assertion = runner_error = False
    scanned = matched = 0
    partial = False
    if log:
        with log.open('rb') as stream:
            number = 0
            while scanned < LOG_BYTES:
                raw = stream.readline(min(LINE_BYTES + 1, LOG_BYTES - scanned))
                if not raw:
                    break
                scanned += len(raw)
                number += 1
                long_line = not raw.endswith(b'\n') and len(raw) > LINE_BYTES
                line = raw[:LINE_BYTES].decode('utf-8', errors='replace')
                if long_line:
                    partial = True
                    # Drain the physical line within the byte budget, keeping line references accurate.
                    while not raw.endswith(b'\n') and scanned < LOG_BYTES:
                        raw = stream.readline(min(LINE_BYTES, LOG_BYTES - scanned))
                        if not raw: break
                        scanned += len(raw)
                if ERROR.search(line):
                    matched += 1
                    is_compiler = bool(COMPILER.search(line))
                    is_assertion = bool(re.search(r"XCTAssert.*failed|Test Case '[^'\n]*' failed\b", line, re.I))
                    compiler = compiler or is_compiler
                    assertion = assertion or is_assertion
                    runner_error = runner_error or not (is_compiler or is_assertion)
                    digest = hashlib.sha256(line.encode()).digest()
                    if digest not in seen:
                        if len(seen) < UNIQUE_ERRORS:
                            seen.add(digest)
                        else:
                            partial = True
                        if len(errors) < limit:
                            kind = 'compiler' if is_compiler else 'test_assertion' if is_assertion else 'runner_or_unclassified'
                            # Arbitrary log payloads may contain secrets. Preserve location/category, not text.
                            label = kind + ' evidence; inspect raw log at this line'
                            errors.append(dict(line=number, kind=kind, text=label[:chars],
                                               truncated=len(label) > chars, content_omitted=True))
            if stream.read(1): partial = True
    selected, executed = data.get("selected"), data.get("executed")
    summary = data.get("summary")
    summary = summary if isinstance(summary, dict) else {}
    complete = (isinstance(selected, list) and isinstance(executed, list)
                and all(isinstance(x, str) and x for x in selected + executed)
                and all(type(summary.get(k)) is int and summary[k] >= 0 for k in ("failedTests", "skippedTests"))
                and type(data.get("exitCode")) is int and data.get("status") in ('passed', 'failed'))
    missing = sorted(set(selected) - set(executed)) if complete else None
    unexpected = sorted(set(executed) - set(selected)) if complete else None
    source = source_verification(data, chars)
    changed = source['state'] == 'changed'
    legacy = 'source' not in data and 'sourceAfter' not in data
    identity_unknown = source['state'] in ('invalid', 'unknown') and not legacy
    reasons = []
    if changed: reasons.append('source_changed')
    if compiler: reasons.append('compiler')
    if assertion or (type(summary.get('failedTests')) is int and summary['failedTests'] > 0):
        reasons.append('test_assertion')
    if complete and (not selected or not executed or missing or unexpected or summary['skippedTests']):
        reasons.append('execution_mismatch')
    if data.get('exitCode') not in (None, 0) or data.get('status') == 'failed' or runner_error:
        reasons.append('runner_or_unclassified')
    if not complete: reasons.append('receipt_invalid')
    passed = complete and not reasons and not identity_unknown and not partial
    return {"source_verification": source, "failure_reasons": reasons, "receipt": clipped(receipt, chars) if receipt else None,
            "log": clipped(log, chars) if log else None,
            "verification": "passed" if passed else "not_passed" if changed or (complete and reasons and not identity_unknown) else "unverified",
            "failure_kind": reasons[0] if reasons else None,
            "status": data.get('status') if data.get('status') in ('passed', 'failed', 'running') else None,
            "exit_code": data.get('exitCode') if type(data.get('exitCode')) is int else None,
            "selected_count": len(selected) if isinstance(selected, list) else None,
            "executed_count": len(executed) if isinstance(executed, list) else None,
            "failed": summary.get('failedTests') if type(summary.get('failedTests')) is int else None,
            "skipped": summary.get('skippedTests') if type(summary.get('skippedTests')) is int else None,
            "missing_count": len(missing) if missing is not None else None,
            "missing": [clipped(x, chars) for x in missing[:limit]] if missing is not None else None,
            "unexpected_count": len(unexpected) if unexpected is not None else None,
            "unexpected": [clipped(x, chars) for x in unexpected[:limit]] if unexpected is not None else None,
            "errors": errors, "additional_error_lines": max(0, len(seen) - len(errors)),
            "log_coverage": dict(state='unknown' if partial else 'complete' if log else 'unavailable',
                                 scanned_bytes=scanned, matched_lines=matched,
                                 distinct_matches=len(seen) if not partial else None),
            "truncation": dict(errors=len(seen) > len(errors),
                               missing=missing is not None and len(missing) > limit,
                               unexpected=unexpected is not None and len(unexpected) > limit,
                               items=any(len(x) > chars for x in (missing or [])[:limit] + (unexpected or [])[:limit]),
                               references=any(len(str(x)) > chars for x in (receipt, log) if x)),
            "limits": "Log matches are evidence, not a diagnosis. Incomplete receipts/log-only input cannot establish a pass. Execution-only results do not prove source-bound completion."}


def describe(result):
    """Compact handoff; original receipt/log remain the authoritative evidence."""
    reasons = ', '.join(result.get('failure_reasons', [])) or 'no supported failure reason'
    source = result.get('source_verification', {})
    fingerprints = ''
    if 'before' in source:
        fingerprints = f" {source['before']['fingerprint'][:12]} -> {source['after']['fingerprint'][:12]}"
    return (f"{result['verification']}: {reasons}; source={source.get('state', 'unknown')}{fingerprints}; "
            f"log={result.get('log_coverage', {}).get('state', 'unknown')}; "
            f"receipt={result.get('receipt')} (source/sourceAfter)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path, nargs="?")
    parser.add_argument("--log", type=Path)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--chars", type=int, default=500)
    args = parser.parse_args()
    if not args.receipt and not args.log:
        parser.error("Supply a receipt or --log")
    if not 1 <= args.limit <= 50 or not 1 <= args.chars <= 10000:
        parser.error("limit must be 1..50; chars must be 1..10000")
    print(json.dumps(inspect(args.receipt, args.log, args.limit, args.chars)))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, TypeError):
        print(json.dumps({"verification": "unverified", "failure_kind": "receipt_invalid",
                          "failure_reasons": ["receipt_invalid"],
                          "error": "Cannot inspect input; check JSON shape, access and documented size limits."}))
        sys.exit(1)
