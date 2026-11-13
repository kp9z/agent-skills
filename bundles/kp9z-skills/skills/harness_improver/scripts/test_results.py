#!/usr/bin/env python3
"""Inspect existing runner receipts and extract bounded test-log failures."""
import argparse
import json
from pathlib import Path
import re
import sys


ERROR = re.compile(r"error:|XCTAssert.*failed|Test Case '[^'\n]*' failed\b|failed to (?:launch|start)|TEST (?:EXECUTE )?FAILED|Testing failed:", re.I)
COMPILER = re.compile(r"\.(?:swift|m|mm|c|cc|cpp|h):\d+(?::\d+)?: error:|fatal error:", re.I)


def inspect(receipt=None, log=None, limit=8, chars=500):
    data = json.loads(receipt.read_text()) if receipt else {}
    if not isinstance(data, dict):
        raise ValueError("Receipt must be an object")
    if log is None and receipt:
        candidate = receipt.parent / "test.log"
        log = candidate if candidate.exists() else None
    errors, seen, compiler = [], set(), False
    if log:
        with log.open(errors="replace") as stream:
            for number, line in enumerate(stream, 1):
                if ERROR.search(line):
                    compiler = compiler or bool(COMPILER.search(line))
                    if line not in seen:
                        seen.add(line)
                        if len(errors) < limit:
                            errors.append({"line": number, "text": line.rstrip()[:chars], "truncated": len(line.rstrip()) > chars})
    selected, executed = data.get("selected"), data.get("executed")
    summary = data.get("summary") or {}
    if not isinstance(summary, dict):
        raise ValueError("Receipt summary must be an object")
    complete = (isinstance(selected, list) and isinstance(executed, list)
                and all(isinstance(x, str) for x in selected + executed)
                and all(type(summary.get(k)) is int for k in ("failedTests", "skippedTests"))
                and type(data.get("exitCode")) is int and "status" in data)
    missing = sorted(set(selected) - set(executed)) if complete else None
    unexpected = sorted(set(executed) - set(selected)) if complete else None
    passed = bool(complete and selected and executed and not missing and not unexpected
                  and summary["failedTests"] == 0 and summary["skippedTests"] == 0
                  and data["exitCode"] == 0 and data["status"] == "passed" and not errors)
    kind = ("compiler" if compiler else "test_assertion" if summary.get("failedTests", 0) > 0
            else "execution_mismatch" if complete and (not executed or missing or unexpected or summary["skippedTests"])
            else "runner_or_unclassified" if data.get("exitCode") not in (None, 0) or errors
            else None)
    return {"receipt": str(receipt) if receipt else None, "log": str(log) if log else None,
            "verification": "passed" if passed else "not_passed" if complete else "unverified",
            "failure_kind": kind, "status": data.get("status"), "exit_code": data.get("exitCode"),
            "selected_count": len(selected) if isinstance(selected, list) else None,
            "executed_count": len(executed) if isinstance(executed, list) else None,
            "failed": summary.get("failedTests"), "skipped": summary.get("skippedTests"),
            "missing_count": len(missing) if missing is not None else None,
            "missing": missing[:limit] if missing is not None else None,
            "unexpected_count": len(unexpected) if unexpected is not None else None,
            "unexpected": unexpected[:limit] if unexpected is not None else None,
            "errors": errors, "additional_error_lines": max(0, len(seen) - len(errors)),
            "limits": "Log matches are evidence, not a diagnosis. Incomplete receipts/log-only input cannot establish a pass."}


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
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"error": str(error)}))
        sys.exit(1)
