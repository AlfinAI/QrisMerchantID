"""money.to_rupiah(): int (analytics) and decimal-string (payouts) inputs."""

from qrismerchantid.gopay.money import to_rupiah


def test_minor_units_to_rupiah():
    assert to_rupiah(10600000) == 106000.0
    assert to_rupiah("10600000.0") == 106000.0
    assert to_rupiah(0) == 0.0
