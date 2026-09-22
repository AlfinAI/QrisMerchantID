"""Whole-rupiah amounts: ShopeePay answers Indonesian grouped strings, NOT minor units.

``"409.662"`` means Rp409.662 — the dots are thousand separators. This is the
opposite of GoPay (minor units), so the two providers' money helpers must never
be mixed.
"""

from __future__ import annotations

import re

_PLAIN = re.compile(r"^\d+$")
_GROUPED = re.compile(r"^\d{1,3}(?:\.\d{3})+$")


def parse_id_amount(value: str) -> int | None:
    """Parse ``"409.662"`` → ``409662`` (whole rupiah). ``None`` when malformed.

    Mirrors ``parseShopeeAmount`` in merchantid (``transactionFeed.ts``): plain
    digits or strict ``d{1,3}(.ddd)+`` grouping only. Anything else (commas,
    decimals, signs, inner whitespace) is rejected instead of guessed, so a
    poll loop never matches money it cannot prove.
    """
    text = value.strip()
    if not _PLAIN.match(text) and not _GROUPED.match(text):
        return None
    amount = int(text.replace(".", ""))
    return amount if amount >= 0 else None
