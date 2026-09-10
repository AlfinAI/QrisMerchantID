"""parse_id_amount: Indonesian grouped strings -> whole rupiah (offline)."""

import pytest

from qrismerchantid.shopee.money import parse_id_amount


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1008", 1008),
        ("0", 0),
        ("409.662", 409662),
        ("1.000.000", 1000000),
        ("  50.000  ", 50000),  # surrounding whitespace is trimmed
    ],
)
def test_valid_amounts(raw, expected):
    assert parse_id_amount(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "409,662",  # commas are never thousand separators here
        "409.66",  # bad grouping
        "4096.62",  # bad grouping
        "40.96.62",  # bad grouping
        "409.662.5",
        "Rp50.000",
        "50.000 IDR",
        "-5",
        "+5",
        "50 000",  # inner whitespace
        "abc",
        "12.34.56.78",
    ],
)
def test_malformed_amounts_rejected(raw):
    assert parse_id_amount(raw) is None
