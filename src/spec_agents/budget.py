"""Machine-fit budget helpers: pool sizing and a way for a process to step aside.

Library-mode: no state, nothing here runs at import. :func:`workers` sizes a
fan-out pool to the box; :func:`below_normal` lowers the current process's own
priority. Nothing inside ``spec_agents`` calls :func:`below_normal`; consumers
opt in.
"""

from __future__ import annotations

import os
import sys

WORKERS_ENV = "SPEC_AGENTS_WORKERS"

# Cores left free for the rest of the machine when sizing from cpu_count.
_RESERVED_CORES = 4

_WIN_IDLE = 0x40
_WIN_BELOW_NORMAL = 0x4000
_WIN_AT_OR_BELOW = frozenset({_WIN_IDLE, _WIN_BELOW_NORMAL})

_POSIX_NICENESS = 10


def _parse_workers(value: object, source: str) -> int:
    if isinstance(value, (bool, float)):
        raise ValueError(f"{source} must be an integer >= 1, got {value!r}")
    try:
        n = int(value)  # type: ignore[call-overload]
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{source} must be an integer >= 1, got {value!r}") from None
    if n < 1:
        raise ValueError(f"{source} must be an integer >= 1, got {value!r}")
    return n


def workers(explicit: int | None = None) -> int:
    """Return a fan-out pool size for this machine.

    Precedence: ``explicit``, then the ``SPEC_AGENTS_WORKERS`` environment
    variable (when set and not blank), then ``max(1, os.cpu_count() - 4)``
    (1 when the CPU count is unknown). Read at call time, never at import.

    Raises:
        ValueError: an explicit value (argument or variable) that is not an
            integer >= 1; the message names its source.
    """
    if explicit is not None:
        return _parse_workers(explicit, "workers(explicit)")
    raw = os.environ.get(WORKERS_ENV)
    if raw is not None and raw.strip():
        return _parse_workers(raw.strip(), WORKERS_ENV)
    cpus = os.cpu_count()
    if cpus is None:
        return 1
    return max(1, cpus - _RESERVED_CORES)


def _below_normal_windows() -> bool:
    try:
        import psutil
    except ImportError:
        psutil = None
    if psutil is not None:
        proc = psutil.Process()
        current = int(proc.nice())
        if current in _WIN_AT_OR_BELOW:
            return True
        proc.nice(_WIN_BELOW_NORMAL)
        return True
    import ctypes

    kernel32 = ctypes.windll.kernel32
    # -1 is the current-process pseudo-handle; c_void_p keeps all 64 bits (a bare int is passed as a C int).
    handle = ctypes.c_void_p(-1)
    current = int(kernel32.GetPriorityClass(handle))
    if current in _WIN_AT_OR_BELOW:
        return True
    return bool(kernel32.SetPriorityClass(handle, _WIN_BELOW_NORMAL))


def below_normal() -> bool:
    """Lower the current process to below-normal priority; True on success.

    Windows: ``BELOW_NORMAL_PRIORITY_CLASS`` (0x4000), through psutil when it
    imports, else ctypes ``SetPriorityClass``. POSIX: a niceness of at least 10.
    A process already at or below that level is left alone (never raised), so a
    second call changes nothing. A refused or failed OS call, or an unknown
    platform, returns False and never raises.
    """
    try:
        if sys.platform == "win32":
            return _below_normal_windows()
        if sys.platform.startswith(("linux", "darwin", "freebsd", "openbsd", "netbsd")):
            # os.nice is POSIX-only; the sys.platform test above narrows it for pyright.
            current = os.nice(0)
            if current < _POSIX_NICENESS:
                os.nice(_POSIX_NICENESS - current)
            return True
    except Exception:
        return False
    return False
