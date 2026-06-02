"""Tests for spec_agents.secrets.get_secret (offline; keyring monkeypatched)."""

from __future__ import annotations

import pytest

from spec_agents import secrets
from spec_agents.secrets import get_secret


def test_prefers_keyring_over_env(monkeypatch):
    monkeypatch.setattr(secrets, "_from_keyring", lambda s, n: "kr-val")
    monkeypatch.setenv("FOO", "env-val")
    assert get_secret("FOO") == "kr-val"


def test_env_fallback_when_keyring_empty(monkeypatch):
    monkeypatch.setattr(secrets, "_from_keyring", lambda s, n: None)
    monkeypatch.setenv("FOO", "env-val")
    assert get_secret("FOO") == "env-val"


def test_missing_returns_none(monkeypatch):
    monkeypatch.setattr(secrets, "_from_keyring", lambda s, n: None)
    monkeypatch.delenv("FOO", raising=False)
    assert get_secret("FOO") is None


def test_env_fallback_disabled(monkeypatch):
    monkeypatch.setattr(secrets, "_from_keyring", lambda s, n: None)
    monkeypatch.setenv("FOO", "env-val")
    assert get_secret("FOO", env_fallback=False) is None


def test_required_raises_when_unresolved(monkeypatch):
    monkeypatch.setattr(secrets, "_from_keyring", lambda s, n: None)
    monkeypatch.delenv("FOO", raising=False)
    with pytest.raises(KeyError):
        get_secret("FOO", required=True)


def test_empty_string_treated_as_unset(monkeypatch):
    monkeypatch.setattr(secrets, "_from_keyring", lambda s, n: None)
    monkeypatch.setenv("FOO", "")
    assert get_secret("FOO") is None


def test_from_keyring_returns_none_without_keyring(monkeypatch):
    # Force the keyring import to fail; _from_keyring must swallow and return None.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "keyring":
            raise ImportError("no keyring")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert secrets._from_keyring("claude-stack", "FOO") is None
