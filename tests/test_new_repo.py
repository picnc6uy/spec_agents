"""kit-template-1 property: a repo made by scripts/new_repo.py is green on its first commit.

Runs the generator into tmp_path, then the new repo's own `pre-commit run --all-files`
and `pytest -q`, and compares its drift-script copies to planning's canonical ones.
Slow (pre-commit builds hook environments, cached after the first run) and skipped
when git, pre-commit, the planning or forge-v2 checkouts, or the pre-commit hook
cache are unavailable.
"""

import importlib.util
import os
import shutil
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


def _env_with_python_first() -> dict[str, str]:
    """PATH with this interpreter's dir and Scripts first: `python` resolves to it, and
    pre-commit's `language: system` hooks (`python scripts/...`) run under it."""
    exe = Path(sys.executable).resolve().parent
    parts = [str(exe), str(exe / "Scripts"), os.environ.get("PATH", "")]
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["PATH"] = os.pathsep.join(parts)
    return env


def test_package_name_validation() -> None:
    assert new_repo.package_name("my-repo") == "my_repo"
    for bad in ("My-Repo", "1abc", "a b", "", "a/b"):
        with pytest.raises(ValueError):
            new_repo.package_name(bad)


@pytest.mark.slow
def test_generated_repo_passes_its_own_gates_on_first_commit(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("git not available")
    if not (_PLANNING / "agent-task" / "scripts").is_dir() or not (_FORGE / "kit").is_dir():
        pytest.skip("planning / forge-v2 checkouts not found beside spec_agents")
    env = _env_with_python_first()
    pre_commit = shutil.which("pre-commit", path=env["PATH"])
    bash = shutil.which("bash", path=env["PATH"])
    if pre_commit is None or bash is None:
        pytest.skip("pre-commit or bash not available")

    repo = new_repo.generate("tmpl-demo", tmp_path, planning=_PLANNING, forge=_FORGE)

    # First commit exists on main, tree is clean.
    log = subprocess.run(
        ["git", "log", "--oneline", "--format=%D"], cwd=repo, capture_output=True, text=True
    )
    assert "main" in log.stdout
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True
    )
    assert status.stdout == ""

    # Drift-script copies are byte-identical (modulo CRLF) to planning's canonical ones.
    for name in new_repo.MIRRORED_SCRIPTS:
        mine = (repo / "scripts" / name).read_bytes()
        canonical = (_PLANNING / "agent-task" / "scripts" / name).read_bytes()
        # CRLF folded to LF, as planning's conformance check compares them.
        assert mine == canonical.replace(b"\r\n", b"\n"), name
        assert b"\r" not in mine, name

    # Gate 1: the new repo's own pre-commit, all files.
    hooks = subprocess.run(
        [pre_commit, "run", "--all-files"], cwd=repo, env=env, capture_output=True, text=True
    )
    if "Failed to clone" in hooks.stdout + hooks.stderr or "unable to access" in (
        hooks.stdout + hooks.stderr
    ):
        pytest.skip("pre-commit hook repos not cached and no network")
    assert hooks.returncode == 0, hooks.stdout + hooks.stderr

    # Gate 2: its own tests.
    tests = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )
    assert tests.returncode == 0, tests.stdout + tests.stderr
