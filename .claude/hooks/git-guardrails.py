#!/usr/bin/env python3
"""Block destructive git commands from running via the Bash tool.

Reads the PreToolUse hook payload from stdin, inspects the Bash command,
and exits 2 with a stderr warning if the command matches a blocklist
pattern. Allows everything else through (exit 0, no output).

Blocked:
  - git push --force / -f  (any position, including --force-with-lease bypass)
  - git reset --hard
  - git clean with -f, -fd, -fx, -fX (any combined order)

Installed Session 15 after Session 13's pre-flight incident. To bypass
for a legitimate operation, temporarily disable the hook in
.claude/settings.json rather than deleting this file.
"""

from __future__ import annotations

import json
import re
import shlex
import sys


def _tokenise(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _has_force_flag(tokens: list[str]) -> bool:
    # Handoff says "git push --force (any variant)" — block any --force*
    # form (including --force-with-lease) and the -f shorthand. Short-flag
    # bundles like -fu are not used by git push and are ignored.
    for tok in tokens:
        if tok == "-f":
            return True
        if tok.startswith("--force"):
            return True
    return False


def _is_destructive_clean(tokens: list[str]) -> bool:
    # git clean with any -f, -fd, -fx, -fX (or combined like -fdx).
    for tok in tokens[2:]:
        if tok.startswith("-") and not tok.startswith("--") and "f" in tok[1:]:
            return True
        if tok in ("--force",):
            return True
    return False


def _check(command: str) -> str | None:
    """Return a reason string if blocked, else None."""
    stripped = command.strip()
    if not stripped:
        return None

    # Match against every git invocation in the command (handle && / ; / | chains).
    segments = re.split(r"\s*(?:&&|\|\||;|\|)\s*", stripped)
    for segment in segments:
        tokens = _tokenise(segment)
        if len(tokens) < 2 or tokens[0] != "git":
            continue
        sub = tokens[1]

        if sub == "push" and _has_force_flag(tokens):
            return "git push --force is blocked by .claude/hooks/git-guardrails.py"
        if sub == "reset" and "--hard" in tokens:
            return "git reset --hard is blocked by .claude/hooks/git-guardrails.py"
        if sub == "clean" and _is_destructive_clean(tokens):
            return "destructive git clean (-f/-fd/-fx/-fX) is blocked by .claude/hooks/git-guardrails.py"

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    reason = _check(command)
    if reason is None:
        return 0

    sys.stderr.write(
        f"BLOCKED: {reason}\n"
        "If this is genuinely required, edit .claude/settings.json to "
        "disable the hook for this single command and explain why in the "
        "commit message.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
