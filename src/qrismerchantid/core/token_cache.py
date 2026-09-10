"""File-based caches for provider sessions and in-flight OTP requests.

GoBiz sessions carry no server expiry (``/goid/token`` answers
``{access_token, refresh_token, dbl_enabled}``), so :func:`load` treats a
missing ``expires_at`` as "ask the server" — the provider revalidates with a
cheap call and re-logs in on 401. When callers *do* know an expiry (e.g. the
``otp_expires_in`` window, or a self-imposed TTL), they store it as an absolute
epoch in ``expires_at`` and :func:`load` enforces it.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def _read_json(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.is_file():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def load(path: str | Path) -> dict[str, Any] | None:
    """Load a cached session dict (needs a non-empty ``access_token``).

    Returns ``None`` when the file is missing/invalid, ``access_token`` is
    empty, or ``expires_at`` is present and ``time.time() >= expires_at``
    (absolute epoch comparison, NOT a duration).
    """
    cached = _read_json(path)
    if cached is None or not cached.get("access_token"):
        return None
    if cached.get("expires_at") is not None:
        try:
            expired = time.time() >= int(cached["expires_at"])
        except (TypeError, ValueError):
            return None
        if expired:
            return None
    return cached


def save(path: str | Path, session: dict[str, Any]) -> None:
    """Persist a provider session dict as pretty JSON."""
    Path(path).write_text(json.dumps(session, indent=2), encoding="utf-8")


def load_pending_otp(path: str | Path, ignore_expiry: bool = False) -> dict[str, Any] | None:
    """Load a cached in-flight OTP dict (needs ``otp_token``, GoBiz-style).

    Args:
        ignore_expiry: return the value even past ``expires_at`` — useful when
            the server, not a local guess, should judge validity.
    """
    cached = _read_json(path)
    if cached is None or not cached.get("otp_token"):
        return None
    if not ignore_expiry and cached.get("expires_at") is not None:
        try:
            if time.time() >= int(cached["expires_at"]):
                return None
        except (TypeError, ValueError):
            return None
    return cached


def save_pending_otp(path: str | Path, otp: dict[str, Any]) -> None:
    """Persist an in-flight OTP dict as pretty JSON."""
    Path(path).write_text(json.dumps(otp, indent=2), encoding="utf-8")
