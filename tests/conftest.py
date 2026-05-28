"""Shared test bootstrapping.

Note: the sys.path prepend at the top exists so worktree-based test
runs resolve imports to THIS tree, not the main checkout via the
editable install path. Idempotent; no-op in main checkouts.

Sibling pattern mirrors spectacular/personal_os/photo_archive
conftests (Added 2026-05-21 / S5.A3 there; spec_agents was missed in
that pass — added 2026-05-28 via spec-agents-conftest).

spec_agents kernel intentionally exposes no shared pytest fixtures
beyond what `spec_agents.testing.db` provides as a primitive for
consumers; this conftest is path-bootstrap only.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
