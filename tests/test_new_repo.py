"""kit-template-1 property: a repo made by scripts/new_repo.py is green on its first commit.

Runs the generator into tmp_path, then the new repo's own `pre-commit run --all-files`,
`pytest -q`, `ruff check .`, `ruff format --check .` and `pyright` (everything the generated
CI runs except `pip install`, which would fetch the spec-agents git pin from GitHub; the
placeholder module does not import it), and compares the drift-script copies to planning's.
Slow (pre-commit builds hook environments, cached after the first run). Skipped only on a
specific probe, checked up front: git, bash, pre-commit, ruff, pyright or the planning /
forge-v2 checkouts missing, or the pre-commit hook cache lacking a repo@rev the template uses.
"""

import importlib.util
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("new_repo", _REPO / "scripts" / "new_repo.py")
assert _SPEC is not None and _SPEC.loader is not None
new_repo = importlib.util.module_from_spec(_SPEC)
sys.modules["new_repo"] = new_repo
_SPEC.loader.exec_module(new_repo)

_PLANNING = new_repo.HOME / "planning"
_FORGE = new_repo.HOME / "forge-v2"


def _missing_hook_cache() -> list[str]:
    """Template hook repos@rev absent from pre-commit's cache (empty list = all cached)."""
    config = (new_repo.TEMPLATE / ".pre-commit-config.yaml.tmpl").read_text(encoding="utf-8")
    wanted = re.findall(r"repo:\s*(https://\S+)\s+rev:\s*(\S+)", config)
    home = Path(os.environ.get("PRE_COMMIT_HOME") or Path.home() / ".cache" / "pre-commit")
    db = home / "db.db"
    if not db.is_file():
        return [f"{r}@{v}" for r, v in wanted]
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        have = {tuple(row) for row in con.execute("select repo, ref from repos")}
    except sqlite3.Error:
        have = set()
    finally:
        con.close()
    return [f"{r}@{v}" for r, v in wanted if (r, v) not in have]


def test_name_validation() -> None:
    assert new_repo.package_name("my-repo") == "my_repo"
    bad = ["My-Repo", "1abc", "a b", "", "a/b", "abc-", "abc_", "class", "json", "src", "tests"]
    bad += ["test", "scripts", "os", "a-"]
    for name in bad:
        with pytest.raises(new_repo.GenerateError):
            new_repo.package_name(name)


def test_refuses_existing_file_and_nonempty_dir(tmp_path: Path) -> None:
    (tmp_path / "afile").write_text("x")
    full = tmp_path / "full"
    full.mkdir()
    (full / "f").write_text("x")
    for name in ("afile", "full"):
        with pytest.raises(new_repo.GenerateError):
            new_repo.generate(name, tmp_path, planning=_PLANNING, forge=_FORGE)
        assert new_repo.main([name, "--dest", str(tmp_path)]) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == ["afile", "full"]


@pytest.mark.slow
def test_generated_repo_passes_its_own_gates_on_first_commit(tmp_path: Path) -> None:
    env = new_repo.tool_env()
    tools = {t: shutil.which(t, path=env["PATH"]) for t in ("git", "bash", "pre-commit", "ruff")}
    tools["pyright"] = shutil.which("pyright", path=env["PATH"])
    absent = [t for t, path in tools.items() if path is None]
    if absent:
        pytest.skip(f"tool(s) not available: {', '.join(absent)}")
    if not (_PLANNING / "agent-task" / "scripts").is_dir() or not (_FORGE / "kit").is_dir():
        pytest.skip("planning / forge-v2 checkouts not found beside spec_agents")
    uncached = _missing_hook_cache()
    if uncached:
        pytest.skip(f"pre-commit hook cache lacks: {', '.join(uncached)}")

    repo = new_repo.generate("tmpl-demo", tmp_path, planning=_PLANNING, forge=_FORGE)
    assert [p.name for p in tmp_path.iterdir()] == ["tmpl-demo"]  # no temp dir left behind

    # First commit exists on main, tree is clean.
    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=repo, capture_output=True, text=True
    )
    assert branch.stdout.strip() == "main"
    count = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"], cwd=repo, capture_output=True, text=True
    )
    assert count.stdout.strip() == "1"
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True
    )
    assert status.stdout == ""

    # Drift-script copies are byte-identical (modulo CRLF) to planning's canonical ones.
    for name in new_repo.MIRRORED_SCRIPTS:
        mine = (repo / "scripts" / name).read_bytes()
        canonical = (_PLANNING / "agent-task" / "scripts" / name).read_bytes()
        assert mine == canonical.replace(b"\r\n", b"\n"), name
        assert b"\r" not in mine, name

    # The new repo's own gates.
    gates = [
        [tools["pre-commit"], "run", "--all-files"],
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        [tools["ruff"], "check", "."],
        [tools["ruff"], "format", "--check", "."],
        [tools["pyright"]],
    ]
    for cmd in gates:
        done = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True)
        assert done.returncode == 0, f"{cmd}\n{done.stdout}{done.stderr}"
