#!/usr/bin/env python3
"""Bump the spec_agents git-URL pin across all canonical consumers.

Usage:
    python scripts/bump_consumers.py v0.7.0
    python scripts/bump_consumers.py v0.7.0 --no-commit

Hardcodes the consumer list (CONSUMERS). Add new apps there when they
join the canonical stack.

Per-consumer flow:
    1. Read pyproject.toml.
    2. Locate the `spec-agents @ git+...@vX.Y.Z` line.
    3. Replace the version suffix with the new tag.
    4. If --no-commit not set and the file changed: `git add` + commit.
    5. Skip cleanly if already at the target version, or if the working
       tree has uncommitted changes to other files (safer than
       auto-stashing).

Does NOT update CURRENT_STATE.md / HANDOVER.md prose -- that's editorial.
Does NOT push. Does NOT tag. Run AFTER tagging + pushing the kernel:

    cd c:/Users/ghendrick/spec_agents
    # ... bump pyproject version, commit, tag, push, push tags ...
    python scripts/bump_consumers.py v0.7.0
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CONSUMERS = (
    Path(r"C:\Users\ghendrick\spectacular"),
    Path(r"C:\Users\ghendrick\personal_os"),
    Path(r"C:\Users\ghendrick\photo_archive"),
)

PIN_RE = re.compile(
    r'("spec-agents @ git\+https://github\.com/picnc6uy/spec_agents@)(v\d+\.\d+\.\d+)(")'
)
TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")


@dataclass
class BumpResult:
    repo: Path
    status: str  # "bumped" | "unchanged" | "no-pin" | "missing" | "dirty-skipped"
    old_version: str | None = None
    commit_sha: str | None = None


def _git(repo: Path, *args: str, capture: bool = False) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=capture,
        text=True,
    )
    return res.stdout.strip() if capture else ""


def bump_one(repo: Path, new_tag: str, *, commit: bool) -> BumpResult:
    pyproj = repo / "pyproject.toml"
    if not pyproj.exists():
        return BumpResult(repo, "missing")
    text = pyproj.read_text(encoding="utf-8")
    match = PIN_RE.search(text)
    if not match:
        return BumpResult(repo, "no-pin")
    old_version = match.group(2)
    if old_version == new_tag:
        return BumpResult(repo, "unchanged", old_version=old_version)

    if commit:
        status = _git(repo, "status", "--porcelain", capture=True)
        # Skip if anything OTHER than pyproject.toml is dirty. Safer than auto-stash.
        other_changes = [
            line for line in status.splitlines() if line[3:].strip() != "pyproject.toml"
        ]
        if other_changes:
            return BumpResult(repo, "dirty-skipped", old_version=old_version)

    new_text = PIN_RE.sub(rf"\g<1>{new_tag}\g<3>", text)
    pyproj.write_text(new_text, encoding="utf-8")

    sha: str | None = None
    if commit:
        _git(repo, "add", "pyproject.toml")
        _git(repo, "commit", "-m", f"chore: bump spec_agents pin to {new_tag}")
        sha = _git(repo, "rev-parse", "--short", "HEAD", capture=True)
    return BumpResult(repo, "bumped", old_version=old_version, commit_sha=sha)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("tag", help="Target version tag, e.g. v0.7.0")
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Update files but don't git-commit (review diffs, commit manually).",
    )
    args = parser.parse_args()

    if not TAG_RE.match(args.tag):
        print(f"error: tag must look like vX.Y.Z, got: {args.tag}", file=sys.stderr)
        return 2

    results = [bump_one(repo, args.tag, commit=not args.no_commit) for repo in CONSUMERS]

    print(f"\nBumping spec_agents pin -> {args.tag} across {len(results)} consumers:\n")
    for r in results:
        name = r.repo.name
        if r.status == "bumped":
            tail = f" -> {r.commit_sha}" if r.commit_sha else " (uncommitted)"
            print(f"  [bumped]   {name}: {r.old_version} -> {args.tag}{tail}")
        elif r.status == "unchanged":
            print(f"  [skip]     {name}: already at {r.old_version}")
        elif r.status == "no-pin":
            print(f"  [warn]     {name}: no spec-agents pin in pyproject.toml")
        elif r.status == "missing":
            print(f"  [warn]     {name}: no pyproject.toml")
        elif r.status == "dirty-skipped":
            print(f"  [skip]     {name}: working tree dirty; resolve and re-run")

    bumped = [r for r in results if r.status == "bumped"]
    skipped = [r for r in results if r.status == "dirty-skipped"]
    if skipped:
        return 1
    if bumped and not args.no_commit:
        print(
            "\nReminder: update CURRENT_STATE.md / HANDOVER.md prose if it "
            "mentions the kernel version."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
