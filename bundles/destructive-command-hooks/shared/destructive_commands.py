#!/usr/bin/env python3
"""Deny a small, explicit set of destructive shell command prefixes."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from typing import Iterable


BLOCKED_RM_TARGETS = {
    "/": "Never delete the root filesystem.",
    "/*": "Never delete the contents of the root filesystem.",
    "~": "Never delete the entire home directory.",
    "$HOME": "Never delete the entire home directory.",
    "/Users": "Never delete all user directories.",
    "/System": "Never delete macOS system files.",
}

BLOCKED_DISKUTIL = {
    "eraseDisk": "Never erase or repartition a disk.",
    "eraseVolume": "Never erase or repartition a disk.",
    "partitionDisk": "Never erase or repartition a disk.",
}

ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEPARATORS = set(";&|()\n")


def _segments(command: str) -> list[list[str]]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
        lexer.commenters = ""
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        tokens = list(lexer)
    except (TypeError, ValueError):
        return []

    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token and all(character in SEPARATORS for character in token):
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def _without_wrappers(tokens: Iterable[str]) -> list[str]:
    remaining = list(tokens)
    while remaining:
        while remaining and ASSIGNMENT.match(remaining[0]):
            remaining.pop(0)
        if not remaining:
            break

        command = os.path.basename(remaining[0])
        if command in {"command", "sudo"}:
            remaining.pop(0)
            while remaining and remaining[0].startswith("-"):
                remaining.pop(0)
            continue
        if command == "env":
            remaining.pop(0)
            while remaining and (
                remaining[0].startswith("-") or ASSIGNMENT.match(remaining[0])
            ):
                remaining.pop(0)
            continue
        break
    return remaining


def _reason_for_segment(segment: Iterable[str], depth: int = 0) -> str | None:
    tokens = _without_wrappers(segment)
    if not tokens:
        return None

    command = os.path.basename(tokens[0])
    arguments = tokens[1:]

    if command == "rm" and len(arguments) >= 2 and arguments[0] == "-rf":
        return BLOCKED_RM_TARGETS.get(arguments[1])

    if command == "diskutil" and arguments:
        return BLOCKED_DISKUTIL.get(arguments[0])

    if command == "mkfs" or command.startswith("mkfs."):
        return "Never format a filesystem."

    if depth < 3 and command in {"bash", "dash", "ksh", "sh", "zsh"}:
        for index, argument in enumerate(arguments):
            if argument == "-c" and index + 1 < len(arguments):
                return reason_for_command(arguments[index + 1], depth + 1)

    return None


def reason_for_command(command: str, depth: int = 0) -> str | None:
    if not isinstance(command, str) or not command:
        return None
    for segment in _segments(command):
        reason = _reason_for_segment(segment, depth)
        if reason:
            return reason
    return None


def denial(reason: str) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        command = payload.get("tool_input", {}).get("command")
    except (AttributeError, json.JSONDecodeError, OSError, TypeError):
        return 0

    reason = reason_for_command(command)
    if reason:
        json.dump(denial(reason), sys.stdout, separators=(",", ":"))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
