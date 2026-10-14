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

Stdlib only. No GitHub remote, no network beyond what pre-commit needs for uncached hook repos.
The repo is built in a temp dir and renamed at the end; the first commit is made only after
the new repo's own `pre-commit run --all-files` passes. `.secrets.baseline` comes from
`detect-secrets scan` when that tool is on PATH, else the template's static copy.
The generated repo is not in planning's CANONICAL_REPOS roster; adding it there,
and the first daily repo-facts refresh, are operator steps.
"""

from __future__ import annotations

import argparse
import keyword
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
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
_RESERVED = frozenset({"src", "tests", "test", "scripts"})
_TOKEN_RE = re.compile(rb"@@[A-Z_]+@@")


class GenerateError(Exception):
    """A refusal: bad input or an unusable environment. main() prints it and exits 2."""


def package_name(name: str) -> str:
    """Importable package for a repo name: `my-repo` -> `my_repo`."""
    if not _NAME_RE.match(name):
        raise GenerateError(f"repo name {name!r} must match {_NAME_RE.pattern}")
    if name[-1] in "-_":
        raise GenerateError(f"repo name {name!r} must not end with '-' or '_'")
    pkg = name.replace("-", "_")
    if keyword.iskeyword(pkg) or pkg in sys.stdlib_module_names or pkg in _RESERVED:
        raise GenerateError(
            f"repo name {name!r} gives package {pkg!r}, a keyword, stdlib module or reserved name"
        )
    return pkg


def current_tag() -> str:
    """The newest vX.Y.Z tag of this repo (git tag --sort=-v:refname); refuses if none."""
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "tag", "--sort=-v:refname", "--list", "v*"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, OSError) as exc:
        raise GenerateError(f"cannot list spec_agents tags: {exc}") from exc
    for tag in out:
        if re.fullmatch(r"v\d+\.\d+\.\d+", tag):
            return tag
    raise GenerateError("spec_agents has no vX.Y.Z tag to pin")


def _copy_lf(src: Path, dst: Path) -> None:
    """Copy bytes, folding CRLF to LF (a Windows checkout of planning may be CRLF)."""
    dst.write_bytes(src.read_bytes().replace(b"\r\n", b"\n"))


def _run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, env=env)


def tool_env() -> dict[str, str]:
    """Environment with this interpreter's dir and Scripts first on PATH (so `python`,
    pre-commit and detect-secrets resolve to it), minus git's repo-discovery variables."""
    exe = Path(sys.executable).resolve().parent
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["PATH"] = os.pathsep.join([str(exe), str(exe / "Scripts"), env.get("PATH", "")])
    return env


def _rmtree(path: Path) -> None:
    def onerror(func, p, _exc):  # git objects are read-only on Windows
        os.chmod(p, stat.S_IWRITE)
        func(p)

    shutil.rmtree(path, onerror=onerror)


def generate(
    name: str,
    dest: Path,
    *,
    planning: Path | None = None,
    forge: Path | None = None,
    commit: bool = True,
) -> Path:
    """Build the repo in a temp dir under dest, then rename it to dest/name; return that path.

    Raises GenerateError for refusals; subprocess/OS errors propagate. On any failure the
    temp dir is removed, so no half-built repo is left behind.
    """
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
            raise GenerateError(f"missing {needed}; pass --planning / --forge")
    tag = current_tag()
    env = tool_env()
    pre_commit = shutil.which("pre-commit", path=env["PATH"])
    if pre_commit is None:
        raise GenerateError("pre-commit not found on PATH")

    target = dest / name
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise GenerateError(f"{target} exists and is not an empty directory")
    dest.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix=".new_repo-", dir=dest))
    try:
        work = tmp / name
        work.mkdir()
        _render(work, name, pkg, tag, canon)
        _run(["git", "init", "-q", "-b", "main"], work, env)
        _run([sys.executable, str(forge / "kit" / "install.py"), str(work)], work, env)
        _run(["git", "add", "-A"], work, env)
        detect_secrets = shutil.which("detect-secrets", path=env["PATH"])
        if detect_secrets is not None:
            scan = subprocess.run(
                [detect_secrets, "scan"], cwd=work, env=env, check=True, capture_output=True
            )
            (work / ".secrets.baseline").write_bytes(scan.stdout.replace(b"\r\n", b"\n"))
            _run(["git", "add", "-A"], work, env)
        # The first commit must pass its own hooks: install them and run them first.
        _run([pre_commit, "install"], work, env)
        _run([pre_commit, "run", "--all-files"], work, env)
        if commit:
            _run(["git", "add", "-A"], work, env)
            _run(
                ["git", "commit", "-q", "-m", f"chore: {name} from the spec_agents repo template"],
                work,
                env,
            )
        if target.exists():
            target.rmdir()  # empty dir; a rename onto it fails on Windows
        work.rename(target)
    finally:
        _rmtree(tmp)
    return target


def _render(work: Path, name: str, pkg: str, tag: str, canon: Path) -> None:
    """Write every file of the new repo into `work` (no git yet)."""
    reading_order = (canon / "agent-templates" / READING_ORDER).read_text(encoding="utf-8")
    tokens = {
        "@@NAME@@": name,
        "@@PKG@@": pkg,
        "@@TAG@@": tag,
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
        out = work / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(text.encode("utf-8"))

    # 2. Canonical bytes, copied untouched.
    (work / "scripts").mkdir()
    for fname in MIRRORED_SCRIPTS:
        _copy_lf(canon / "scripts" / fname, work / "scripts" / fname)
    agent = work / ".agent"
    for fname in AGENT_TEMPLATES:
        _copy_lf(canon / "agent-templates" / fname, agent / fname)
    (agent / "lenses").mkdir()
    for lens in sorted((canon / "agent-templates" / "lenses").glob("*.md")):
        _copy_lf(lens, agent / "lenses" / lens.name)
    for sub in ("tasks", "verifications"):
        (agent / sub).mkdir(exist_ok=True)
        (agent / sub / ".gitkeep").write_bytes(b"")
    (work / "tests" / "__init__.py").write_bytes(b"")

    # 3. No unreplaced token may survive in any written file.
    for f in sorted(work.rglob("*")):
        if f.is_file():
            m = _TOKEN_RE.search(f.read_bytes())
            if m:
                raise GenerateError(
                    f"unreplaced token {m.group().decode()} in {f.relative_to(work)}"
                )


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
    except GenerateError as exc:
        print(f"new_repo: {exc}", file=sys.stderr)
        return 2
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"new_repo: failed: {exc}", file=sys.stderr)
        return 1
    print(f"created {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
