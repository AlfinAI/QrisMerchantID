"""qris: TLV parse, CRC16 vector, dynamic-nominal injection (pure, offline)."""

import pytest

from qrismerchantid.gopay import qris

# Real-format static QRIS (public .env.example of a reference gateway — structure only).
STATIC = (
    "00020101021126610016ID.CO.SHOPEE.WWW0118936009180022761567020822761567"
    "0303UMI51440014ID.CO.QRIS.WWW0215ID10264876014560303UMI520457225303360"
    "5802ID5911NUXYS STORE6009TANGERANG61051511262070703A0163047034"
)


def test_parse_and_get_tag():
    tags = dict(qris.parse(STATIC))
    assert tags["00"] == "01"
    assert qris.get_tag(STATIC, "59") == "NUXYS STORE"
    assert qris.get_tag(STATIC, "60") == "TANGERANG"
    assert qris.get_tag(STATIC, "54") is None  # static: no nominal tag
    assert qris.get_tag(STATIC, "99") is None


def test_crc16_ccitt_standard_vector():
    assert qris.crc16_ccitt("123456789") == "29B1"  # canonical CCITT-FALSE check


def test_inject_amount_adds_tag_54_with_valid_crc():
    dynamic = qris.inject_amount(STATIC, 50000)
    assert qris.get_tag(dynamic, "54") == "50000"
    assert qris.get_tag(dynamic, "59") == "NUXYS STORE"  # untouched tags survive
    assert qris.crc16_ccitt(dynamic[:-4]) == dynamic[-4:]  # CRC self-verifies


def test_inject_amount_replaces_existing_tag_54():
    once = qris.inject_amount(STATIC, 50000)
    twice = qris.inject_amount(once, 75000)
    assert qris.get_tag(twice, "54") == "75000"
    assert qris.crc16_ccitt(twice[:-4]) == twice[-4:]


def test_inject_amount_places_tag_54_after_53():
    tags = [t for t, _ in qris.parse(qris.inject_amount(STATIC, 50000))]
    assert tags.index("54") == tags.index("53") + 1  # numeric order, like the ref gateway
    assert tags[-1] == "63"


def test_inject_amount_rejects_bad_amounts():
    for bad in (0, -5, "50000", 50.0, True, None):
        with pytest.raises(ValueError):
            qris.inject_amount(STATIC, bad)


def test_parse_rejects_malformed_payloads():
    for bad in ("00", "00ZZ", "0215AB", "0002010"):
        with pytest.raises(ValueError):
            qris.parse(bad)
