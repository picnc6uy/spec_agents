"""Resolve a secret from the OS keyring first, with an env/.env fallback.

Keeps secrets out of the shell / Claude Code environment: call ``get_secret(name)``
and it reads the OS keyring (Windows Credential Manager via ``keyring``) under a
stack-wide service namespace, only falling back to ``os.environ`` if absent.
Values are never logged.

``keyring`` is an OPTIONAL dependency, imported lazily — if it isn't installed,
resolution silently falls back to the environment, so importing this module
never hard-fails.

Migration helper: store a secret once with
``keyring.set_password("claude-stack", "DPLA_API_KEY", "<value>")`` (or via the
operator's getpass recipe), then have scripts read it with
``get_secret("DPLA_API_KEY")`` instead of ``os.environ[...]``.
"""

from __future__ import annotations

import os

# Stack-wide keyring service namespace. (The Anthropic admin key intentionally
# lives under its own "anthropic"/"admin_key" entry; pass service= to read it.)
DEFAULT_SERVICE = "claude-stack"


def _from_keyring(service: str, name: str) -> str | None:
    """Return the keyring value, or None if keyring is absent/empty/erroring."""
    try:
        import keyring
    except Exception:
        return None
    try:
        return keyring.get_password(service, name) or None
    except Exception:
        return None


def get_secret(
    name: str,
    *,
    service: str = DEFAULT_SERVICE,
    env_fallback: bool = True,
    required: bool = False,
) -> str | None:
    """Resolve secret ``name`` from the keyring, falling back to the environment.

    Order: keyring(service, name) -> os.environ[name] (if ``env_fallback``).
    Empty strings are treated as "not set". Returns None when unresolved unless
    ``required`` is True, in which case a KeyError is raised. Never logs values.
    """
    value = _from_keyring(service, name)
    if not value and env_fallback:
        value = os.environ.get(name) or None
    if not value and required:
        raise KeyError(
            f"secret {name!r} not found (keyring service={service!r}"
            f"{'; env fallback' if env_fallback else ''})"
        )
    return value
