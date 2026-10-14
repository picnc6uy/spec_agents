#!/usr/bin/env python3
"""Generate a new stack repo from the spec_agents template (kit-template-1).

    py -3.12 scripts/new_repo.py NAME --dest DIR

Writes DIR/NAME/ and makes its first commit on `main`: a src/<pkg>/ package with
one module, one test, pyproject (ruff 0.16.6 / pyright 1.1.411 pinned, spec-agents
pinned to the current release tag), the stack's .pre-commit-config.yaml,
AGENTS.md + CLAUDE.md stub + docs/, the .agent/ scaffold, byte copies of the three
agent-task scripts, then `git init -b main`, the Forge v2 kit install, and a commit.

Two sources, never duplicated here:
  - templates/new_repo/ (next to this repo's scripts/): the files that are ours.
    Every `*.tmpl` file is copied with the `.tmpl` suffix dropped and these
    tokens replaced: @@NAME@@ @@PKG@@ @@TAG@@ @@TODAY@@ @@READING_ORDER@@.
    A path segment named `@@PKG@@` becomes the package name.
  - planning/agent-task/ (canonical): the drift scripts, the verification/task
    templates, the lenses, and the AGENTS.md reading-order block. These are
    copied as bytes with CRLF folded to LF (the form git stores; a CRLF checkout of a
    .sh breaks `set -eu` on Linux), which is how planning's
    check_stack_conformance.py compares them.

Stdlib only. No GitHub remote, no network (the commit does not install anything).
The generated repo is not in planning's CANONICAL_REPOS roster; adding it there,
and the first daily repo-facts refresh, are operator steps.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "templates" / "new_repo"
HOME = REPO_ROOT.parent  # spec_agents and its worktrees sit beside planning/ and forge-v2/

#: Canonical files mirrored byte-for-byte: (dir under planning/agent-task, name, dest in new repo).
MIRRORED_SCRIPTS: tuple[str, ...] = (
    "check_semantic_drift.py",
    "check_current_state_drift.py",
    "check_agent_task_spec.sh",
)
AGENT_TEMPLATES: tuple[str, ...] = (
    "task-template.md",
    "verification-template.md",
    "verification-template-light.md",
)
READING_ORDER = "agents-reading-order.md"

_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


def package_name(name: str) -> str:
    """Importable package for a repo name: `my-repo` -> `my_repo`."""
    if not _NAME_RE.match(name):
        raise ValueError(f"repo name {name!r} must match {_NAME_RE.pattern}")
    return name.replace("-", "_")


def current_tag() -> str:
    """The newest release tag of this repo; falls back to v<pyproject version>."""
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "describe", "--tags", "--abbrev=0", "--match", "v*"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if re.fullmatch(r"v\d+\.\d+\.\d+", out):
            return out
    except (subprocess.CalledProcessError, OSError):
        pass
    m = re.search(
        r'^version\s*=\s*"(\d+\.\d+\.\d+)"', (REPO_ROOT / "pyproject.toml").read_text(), re.M
    )
    if not m:
        raise SystemExit("cannot determine the current spec_agents tag")
    return f"v{m.group(1)}"


def _copy_lf(src: Path, dst: Path) -> None:
    """Copy bytes, folding CRLF to LF (a Windows checkout of planning may be CRLF)."""
    dst.write_bytes(src.read_bytes().replace(b"\r\n", b"\n"))


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def generate(
    name: str,
    dest: Path,
    *,
    planning: Path | None = None,
    forge: Path | None = None,
    commit: bool = True,
) -> Path:
    """Write the repo at dest/name and return its path."""
    pkg = package_name(name)
    planning = planning or HOME / "planning"
    forge = forge or HOME / "forge-v2"
    canon = planning / "agent-task"
    for needed in (
        canon / "scripts",
        canon / "agent-templates" / READING_ORDER,
        forge / "kit" / "install.py",
    ):
        if not needed.exists():
            raise SystemExit(f"missing {needed}; pass --planning / --forge")

    target = dest / name
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"{target} exists and is not empty")
    target.mkdir(parents=True, exist_ok=True)

    reading_order = (canon / "agent-templates" / READING_ORDER).read_text(encoding="utf-8")
    tokens = {
        "@@NAME@@": name,
        "@@PKG@@": pkg,
        "@@TAG@@": current_tag(),
        "@@TODAY@@": date.today().isoformat(),
        "@@READING_ORDER@@": reading_order.strip("\n"),
    }

    # 1. Our templates, with tokens replaced. LF endings always.
    for src in sorted(TEMPLATE.rglob("*.tmpl")):
        rel = src.relative_to(TEMPLATE).with_suffix("")
        rel = Path(*(pkg if part == "@@PKG@@" else part for part in rel.parts))
        text = src.read_text(encoding="utf-8")
        for token, value in tokens.items():
            text = text.replace(token, value)
        out = target / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))

    # 2. Canonical bytes, copied untouched.
    (target / "scripts").mkdir()
    for fname in MIRRORED_SCRIPTS:
        _copy_lf(canon / "scripts" / fname, target / "scripts" / fname)
    agent = target / ".agent"
    for fname in AGENT_TEMPLATES:
        _copy_lf(canon / "agent-templates" / fname, agent / fname)
    (agent / "lenses").mkdir()
    for lens in sorted((canon / "agent-templates" / "lenses").glob("*.md")):
        _copy_lf(lens, agent / "lenses" / lens.name)
    for sub in ("tasks", "verifications"):
        (agent / sub).mkdir(exist_ok=True)
        (agent / sub / ".gitkeep").write_bytes(b"")
    (target / "tests" / "__init__.py").write_bytes(b"")

    # 3. Git, Forge kit, first commit.
    _run(["git", "init", "-q", "-b", "main"], target)
    _run([sys.executable, str(forge / "kit" / "install.py"), str(target)], target)
    if commit:
        _run(["git", "add", "-A"], target)
        _run(
            ["git", "commit", "-q", "-m", f"chore: {name} from the spec_agents repo template"],
            target,
        )
    return target


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name", help="repo name, e.g. my-repo (package: my_repo)")
    ap.add_argument(
        "--dest", type=Path, required=True, help="parent directory; repo goes in DEST/NAME"
    )
    ap.add_argument("--planning", type=Path, help="planning repo (default: sibling of spec_agents)")
    ap.add_argument("--forge", type=Path, help="forge-v2 repo (default: sibling of spec_agents)")
    args = ap.parse_args(argv)
    try:
        target = generate(args.name, args.dest.resolve(), planning=args.planning, forge=args.forge)
    except ValueError as exc:
        print(f"new_repo: {exc}", file=sys.stderr)
        return 2
    print(f"created {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
