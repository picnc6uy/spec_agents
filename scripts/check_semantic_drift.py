#!/usr/bin/env python3
"""Semantic load-bearing drift checks: docs must match git/pyproject truth.

The drift apparatus' date checks enforce freshness, not content truth — a
freshly-dated doc can lie indefinitely (observed three ways on 2026-06-04,
see planning/sprints/2026-06-04-drift-mechanization.md). Three deterministic
checks close the observed lie-shapes, all BLOCKING (operator decision (a),
2026-06-05):

- C1 — branch-in-flight: if docs/CURRENT_STATE.md's *current* section claims
  `Branch in flight: <branch>`, that branch must exist and be unmerged into
  the default branch. `none` always passes.
- C2 — sprint-status ghosts: a docs/SPRINTS.md entry whose status is
  `⬜`/`not started` must not reference a branch id whose
  `.agent/verifications/<branch-id>.md` says `status: ready-to-merge`.
- C3 — pin-claim sync: a `spec-agents @ git+...@vX.Y.Z` pin quoted in
  CURRENT_STATE.md's current section must equal the pin in pyproject.toml.

Pure git/regex — no API, no LLM, $0. stdlib only (sibling repos run hooks
from bare venvs).

Source of truth: planning/agent-task/scripts/check_semantic_drift.py
Mirrored into each canonical repo at scripts/check_semantic_drift.py next to
scripts/check_current_state_drift.py, which imports and runs these checks —
the drift-audit hook entry itself is unchanged (operator decision (b)).

"Current section" = text from the first `## As of` heading up to the next
one (CURRENT_STATE keeps history as stacked sections; older sections
legitimately name merged branches and stale pins).

Missing docs/CURRENT_STATE.md or docs/SPRINTS.md → the affected check passes
silently (planning itself has neither).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

CURRENT_STATE = Path("docs/CURRENT_STATE.md")
SPRINTS = Path("docs/SPRINTS.md")
VERIFICATIONS = Path(".agent/verifications")

BRANCH_IN_FLIGHT_RE = re.compile(
    r"Branch in flight:\*{0,2}\s*(?:`(?P<branch>[^`]+)`|(?P<word>\S+))"
)
NOT_STARTED_RE = re.compile(r"⬜|not started", re.IGNORECASE)
READY_TO_MERGE_RE = re.compile(r"^status:\s*ready-to-merge\s*$", re.MULTILINE)
# Branch ids referenced inside a SPRINTS.md entry: `agent/<id>` or
# `.agent/tasks/<id>.md` / `.agent/verifications/<id>.md`.
AGENT_BRANCH_RE = re.compile(r"`agent/(?P<id>[A-Za-z0-9][A-Za-z0-9._-]*)`")
AGENT_DOC_RE = re.compile(r"\.agent/(?:tasks|verifications)/(?P<id>[A-Za-z0-9][A-Za-z0-9._-]*)\.md")
PIN_RE = re.compile(r"spec-agents\s*@\s*git\+\S+?@(?P<version>v\d+\.\d+\.\d+)")
PROJECT_NAME_RE = re.compile(r'^name\s*=\s*"spec[-_]agents"', re.MULTILINE)
OWN_VERSION_RE = re.compile(r'^version\s*=\s*"(?P<version>\d+\.\d+\.\d+)"', re.MULTILINE)
AS_OF_HEADING_RE = re.compile(r"^## As of ", re.MULTILINE)


class Violation(NamedTuple):
    check: str
    file: str
    detail: str


def _git(repo: Path, *args: str) -> str | None:
    """Run git in `repo`; None on any failure (don't block commits on tooling)."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _default_branch(repo: Path) -> str | None:
    """origin/HEAD if set; else local main, else master (spec_agents is master)."""
    ref = _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD")
    if ref:
        return ref.strip().rsplit("/", 1)[-1]
    for name in ("main", "master"):
        if _git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{name}") is not None:
            return name
    return None


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _current_section(text: str) -> str:
    """Text of the first `## As of` section (or the whole doc if unsectioned)."""
    matches = list(AS_OF_HEADING_RE.finditer(text))
    if not matches:
        return text
    start = matches[0].start()
    end = matches[1].start() if len(matches) > 1 else len(text)
    return text[start:end]


def check_branch_in_flight(repo: Path) -> list[Violation]:
    """C1: a claimed in-flight branch must exist and be unmerged."""
    text = _read(repo / CURRENT_STATE)
    if text is None:
        return []
    match = BRANCH_IN_FLIGHT_RE.search(_current_section(text))
    if not match:
        return []
    claimed = match.group("branch") or match.group("word")
    if claimed.strip("*.,;:").lower() == "none":
        return []
    exists = _git(repo, "branch", "--list", claimed)
    if exists is not None and not exists.strip():
        return [
            Violation(
                "C1",
                str(CURRENT_STATE),
                f"claims 'Branch in flight: {claimed}' but no such branch exists",
            )
        ]
    default = _default_branch(repo)
    if default is None:
        return []
    merged = _git(repo, "branch", "--merged", default)
    if merged is not None and any(
        line.lstrip("* ").strip() == claimed for line in merged.splitlines()
    ):
        return [
            Violation(
                "C1",
                str(CURRENT_STATE),
                f"claims 'Branch in flight: {claimed}' but it is already merged into {default}",
            )
        ]
    return []


def _split_entries(text: str) -> list[tuple[str, str]]:
    """(heading, body) per `##`/`###` heading in SPRINTS.md."""
    entries: list[tuple[str, str]] = []
    heading: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        if re.match(r"^#{2,3} ", line):
            if heading is not None:
                entries.append((heading, "\n".join(body)))
            heading = line
            body = []
        elif heading is not None:
            body.append(line)
    if heading is not None:
        entries.append((heading, "\n".join(body)))
    return entries


def check_sprint_ghosts(repo: Path) -> list[Violation]:
    """C2: a not-started entry must not have a ready-to-merge verification."""
    text = _read(repo / SPRINTS)
    if text is None:
        return []
    violations: list[Violation] = []
    for heading, body in _split_entries(text):
        entry = f"{heading}\n{body}"
        status_lines = [heading] + [
            line for line in body.splitlines() if line.startswith("**Status:**")
        ]
        if not any(NOT_STARTED_RE.search(line) for line in status_lines):
            continue
        branch_ids = {
            m.group("id").lower()
            for pattern in (AGENT_BRANCH_RE, AGENT_DOC_RE)
            for m in pattern.finditer(entry)
        }
        for branch_id in sorted(branch_ids):
            verification = repo / VERIFICATIONS / f"{branch_id}.md"
            verification_text = _read(verification)
            if verification_text and READY_TO_MERGE_RE.search(verification_text):
                violations.append(
                    Violation(
                        "C2",
                        str(SPRINTS),
                        f"entry '{heading.lstrip('# ').strip()}' is marked not "
                        f"started but {VERIFICATIONS / (branch_id + '.md')} says "
                        f"status: ready-to-merge",
                    )
                )
    return violations


def check_pin_claims(repo: Path) -> list[Violation]:
    """C3: pins quoted in CURRENT_STATE's current section must match pyproject.

    Consumer repos: the doc pin must equal the spec-agents pin in their
    pyproject dependencies. The producer repo (pyproject name =
    spec-agents) legitimately quotes the consumer pin string; there the
    doc pin must equal the repo's own `version` instead (also catches the
    v0.10.0 __version__-lag class of lie).
    """
    text = _read(repo / CURRENT_STATE)
    if text is None:
        return []
    doc_pins = {m.group("version") for m in PIN_RE.finditer(_current_section(text))}
    if not doc_pins:
        return []
    pyproject = _read(repo / "pyproject.toml")
    if pyproject and PROJECT_NAME_RE.search(pyproject):
        own = OWN_VERSION_RE.search(pyproject)
        if own is None:
            return []
        actual = f"v{own.group('version')}"
        return [
            Violation(
                "C3",
                str(CURRENT_STATE),
                f"quotes spec-agents pin {claimed} but this repo's own "
                f"pyproject.toml version is {actual}",
            )
            for claimed in sorted(doc_pins)
            if claimed != actual
        ]
    toml_match = PIN_RE.search(pyproject) if pyproject else None
    if toml_match is None:
        return [
            Violation(
                "C3",
                str(CURRENT_STATE),
                f"quotes spec-agents pin {'/'.join(sorted(doc_pins))} but "
                f"pyproject.toml has no spec-agents pin",
            )
        ]
    actual = toml_match.group("version")
    return [
        Violation(
            "C3",
            str(CURRENT_STATE),
            f"quotes spec-agents pin {claimed} but pyproject.toml pins {actual}",
        )
        for claimed in sorted(doc_pins)
        if claimed != actual
    ]


def run_checks(repo: Path) -> list[Violation]:
    return [
        *check_branch_in_flight(repo),
        *check_sprint_ghosts(repo),
        *check_pin_claims(repo),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path("."), help="repo root")
    args = parser.parse_args(argv)
    violations = run_checks(args.repo)
    for v in violations:
        _eprint(f"semantic-drift [{v.check}] {v.file}: {v.detail}")
    if violations:
        _eprint(
            "\n  Fix the doc to match reality (or reality to match the doc),\n"
            "  then re-run the commit. Bypass (rare): git commit --no-verify\n"
        )
        return 1
    return 0


def _eprint(msg: str) -> None:
    """stderr print that survives cp1252 capture (details may contain ⬜)."""
    encoding = getattr(sys.stderr, "encoding", None) or "utf-8"
    sys.stderr.write(msg.encode(encoding, "replace").decode(encoding, "replace") + "\n")


if __name__ == "__main__":
    sys.exit(main())
