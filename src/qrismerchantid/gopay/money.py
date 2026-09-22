"""Minor-unit (sen) amounts: analytics answers ints, payouts answer decimal strings."""

from __future__ import annotations


def to_rupiah(amount: int | str) -> float:
    """Convert minor units to rupiah (``10600000`` / ``"10600000.0"`` → ``106000.0``)."""
    return float(amount) / 100
