#!/usr/bin/env python3
"""Tests for the shared destructive-command hook."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


HOOK = Path(__file__).parents[1] / "shared" / "destructive_commands.py"

BLOCKED = {
    "rm -rf /": "Never delete the root filesystem.",
    "rm -rf /*": "Never delete the contents of the root filesystem.",
    "rm -rf ~": "Never delete the entire home directory.",
    "rm -rf $HOME": "Never delete the entire home directory.",
    "rm -rf /Users": "Never delete all user directories.",
    "rm -rf /System": "Never delete macOS system files.",
    "diskutil eraseDisk disk-name GPT /dev/disk9": "Never erase or repartition a disk.",
    "diskutil eraseVolume APFS disk-name /dev/disk9s1": "Never erase or repartition a disk.",
    "diskutil partitionDisk /dev/disk9 GPT APFS disk-name 100%": "Never erase or repartition a disk.",
    "mkfs /dev/disk9": "Never format a filesystem.",
}


def run_raw(raw: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=raw,
        text=True,
        capture_output=True,
        check=False,
    )


def run_command(command: str) -> subprocess.CompletedProcess[str]:
    return run_raw(json.dumps({"tool_input": {"command": command}}))


class DestructiveCommandHookTests(unittest.TestCase):
    def assert_blocked(self, command: str, reason: str) -> None:
        result = run_command(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertEqual(output["permissionDecisionReason"], reason)

    def assert_allowed(self, command: str) -> None:
        result = run_command(command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_every_prefix_directly_and_after_safe_segment(self) -> None:
        for command, reason in BLOCKED.items():
            with self.subTest(command=command):
                self.assert_blocked(command, reason)
                self.assert_blocked(f"echo safe && {command}", reason)

    def test_quoted_destructive_text_is_allowed(self) -> None:
        self.assert_allowed("echo 'rm -rf /'")
        self.assert_allowed('printf "%s\\n" "diskutil eraseDisk"')

    def test_representative_safe_commands_are_allowed(self) -> None:
        for command in ("rm -rf ./build", "diskutil list", "echo ok; git status"):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_malformed_and_incomplete_payloads_are_allowed(self) -> None:
        for raw in ("not-json", "{}", '{"tool_input":{}}', "[]"):
            with self.subTest(raw=raw):
                result = run_raw(raw)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

    def test_wrappers_and_nested_shell_are_blocked(self) -> None:
        self.assert_blocked("sudo rm -rf /", BLOCKED["rm -rf /"])
        self.assert_blocked("env SAFE=1 /bin/rm -rf /", BLOCKED["rm -rf /"])
        self.assert_blocked("bash -c 'rm -rf /'", BLOCKED["rm -rf /"])
        self.assert_blocked('rm -rf "$HOME"', BLOCKED["rm -rf $HOME"])
        self.assert_blocked("echo safe\nrm -rf /", BLOCKED["rm -rf /"])


if __name__ == "__main__":
    unittest.main()
