#!/usr/bin/env python3
"""Pre-commit hook: catch CURRENT_STATE.md staleness before it accumulates.

Fails the commit when `docs/CURRENT_STATE.md` carries an `## As of YYYY-MM-DD`
line older than MAX_DRIFT_DAYS AND the repo has commits since that date.

Rationale (planning/architecture-reviews/2026-05-23-cross-stack-architect-review-03.md
Gap 1): the drift-audit lens exists but didn't fire between 2026-05-21 and
2026-05-23, accumulating 2-3 days of drift across all four canonical repos.
A structural hook is cheaper than relying on agent/operator discipline at
session-start.

Source of truth: planning/agent-task/scripts/check_current_state_drift.py
Mirrored into each canonical repo at scripts/check_current_state_drift.py
and wired into .pre-commit-config.yaml as a local hook.

Behavior:
- No `docs/CURRENT_STATE.md` → pass (nothing to drift against).
- No `## As of <date>` line in the doc → pass with a note (someone removed it).
- Date <= MAX_DRIFT_DAYS old → pass.
- Date > MAX_DRIFT_DAYS old AND no commits since → pass (benign — repo is idle).
- Date > MAX_DRIFT_DAYS old AND commits since → fail with actionable guidance.

Bypass (rare, intentional): `git commit --no-verify`. Use only when the
operator has waived the check (e.g., committing a doc-only refresh that
will fix the staleness in this same commit but pre-commit fired before
seeing the staged change — which shouldn't happen since we read the
staged version, but kept here for safety).
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

CURRENT_STATE = Path("docs/CURRENT_STATE.md")
MAX_DRIFT_DAYS = 3
AS_OF_RE = re.compile(r"^## As of (\d{4}-\d{2}-\d{2})", re.MULTILINE)


def main() -> int:
    if not CURRENT_STATE.is_file():
        return 0

    # Read the staged version if available (so a commit that's fixing the
    # doc passes); fall back to working-dir content.
    text = _read_staged_or_disk(CURRENT_STATE)
    match = AS_OF_RE.search(text)
    if not match:
        # Doc has no '## As of' line — someone removed or restructured it.
        # Don't block commits; just note.
        print(
            f"drift-audit: {CURRENT_STATE} has no '## As of YYYY-MM-DD' line; skipping check.",
            file=sys.stderr,
        )
        return 0

    try:
        doc_date = datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        print(
            f"drift-audit: {CURRENT_STATE} '## As of' line has invalid date "
            f"'{match.group(1)}'; skipping check.",
            file=sys.stderr,
        )
        return 0

    today = date.today()
    age_days = (today - doc_date).days
    if age_days <= MAX_DRIFT_DAYS:
        return 0

    # Stale dated; check if any commits landed since.
    try:
        log = subprocess.check_output(
            ["git", "log", "--since", match.group(1), "--oneline"],
            text=True,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git command failed; don't block commits on tooling issues.
        return 0

    commits = [line for line in log.splitlines() if line.strip()]
    if not commits:
        # Doc is stale-dated but no commits since — benign.
        return 0

    # Stale dated AND commits since this date → fail with guidance.
    print("", file=sys.stderr)
    print(
        f"drift-audit: docs/CURRENT_STATE.md '## As of {doc_date}' is "
        f"{age_days} days old (max allowed: {MAX_DRIFT_DAYS})",
        file=sys.stderr,
    )
    print(
        f"  and {len(commits)} commit(s) have landed in this repo since:",
        file=sys.stderr,
    )
    for c in commits[:5]:
        print(f"    {c}", file=sys.stderr)
    if len(commits) > 5:
        print(f"    ... and {len(commits) - 5} more", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Refresh docs/CURRENT_STATE.md (date + master-commit + test count)", file=sys.stderr)
    print("  in the same commit as your work, then re-run the commit.", file=sys.stderr)
    print("", file=sys.stderr)
    print("  Bypass (rare, intentional): git commit --no-verify", file=sys.stderr)
    print("", file=sys.stderr)
    return 1


def _read_staged_or_disk(path: Path) -> str:
    """Prefer the staged version of the file so a same-commit fix passes."""
    try:
        out = subprocess.check_output(
            ["git", "show", f":{path.as_posix()}"],
            text=True,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )
        if out:
            return out
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


if __name__ == "__main__":
    sys.exit(main())
