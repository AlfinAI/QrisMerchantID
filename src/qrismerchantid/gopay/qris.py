"""EMVCo QRIS helpers: parse TLV, inject a dynamic nominal, CRC16-CCITT.

Pure functions — no network. The algorithm mirrors every reference gateway:
parse the static QRIS → set tag ``54`` → strip tag ``63`` → recompute CRC.
"""

from __future__ import annotations


def parse(payload: str) -> list[tuple[str, str]]:
    """Parse EMVCo TLV into ``[(tag, value), ...]`` (tags/lengths are 2 chars each).

    Raises:
        ValueError: truncated payload, non-numeric length, or short value.
    """
    tags: list[tuple[str, str]] = []
    i = 0
    while i < len(payload):
        if i + 4 > len(payload):
            raise ValueError(f"Truncated TLV header at offset {i}")
        tag, length = payload[i : i + 2], payload[i + 2 : i + 4]
        if not length.isdigit():
            raise ValueError(f"Non-numeric TLV length {length!r} at offset {i}")
        (n,) = (int(length),)
        value = payload[i + 4 : i + 4 + n]
        if len(value) != n:
            raise ValueError(f"Truncated TLV value for tag {tag} at offset {i}")
        tags.append((tag, value))
        i += 4 + n
    return tags


def get_tag(payload: str, tag_id: str) -> str | None:
    """Return the first value for ``tag_id`` (e.g. ``"59"`` merchant name), else ``None``."""
    for tag, value in parse(payload):
        if tag == tag_id:
            return value
    return None


def crc16_ccitt(data: str) -> str:
    """CRC16-CCITT-FALSE (poly ``0x1021``, init ``0xFFFF``) as 4-char UPPER hex."""
    crc = 0xFFFF
    for byte in data.encode("ascii"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def inject_amount(static_payload: str, amount_idr: int) -> str:
    """Build a dynamic QRIS: set tag ``54`` to ``amount_idr`` and recompute the CRC.

    Args:
        static_payload: the merchant's static QRIS string.
        amount_idr: positive int rupiah (no decimals, e.g. ``50000``).

    Raises:
        ValueError: bad amount or unparseable payload.
    """
    if not isinstance(amount_idr, int) or isinstance(amount_idr, bool) or amount_idr <= 0:
        raise ValueError("amount_idr must be a positive int (rupiah, no decimals)")
    tags = [(t, v) for t, v in parse(static_payload) if t != "63"]
    amount = str(amount_idr)
    for i, (tag, _) in enumerate(tags):
        if tag == "54":
            tags[i] = ("54", amount)
            break
    else:
        tags.append(("54", amount))
        tags.sort(key=lambda kv: kv[0])
    body = "".join(f"{tag}{len(value):02d}{value}" for tag, value in tags) + "6304"
    return body + crc16_ccitt(body)
