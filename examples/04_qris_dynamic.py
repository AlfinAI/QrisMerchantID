"""Build a dynamic QRIS offline (no login needed). Needs: QRIS_STATIC + AMOUNT_IDR env."""

import os

from qrismerchantid.gopay import qris


def main() -> None:
    static = os.environ.get("QRIS_STATIC")
    amount = os.environ.get("AMOUNT_IDR")
    if not static or not amount:
        raise SystemExit("Set QRIS_STATIC and AMOUNT_IDR, e.g. AMOUNT_IDR=50000")
    dynamic = qris.inject_amount(static, int(amount))
    assert qris.crc16_ccitt(dynamic[:-4]) == dynamic[-4:]
    print(f"Merchant : {qris.get_tag(dynamic, '59')}")
    print(f"Nominal  : Rp{int(qris.get_tag(dynamic, '54')):,}")
    print(f"Dynamic  : {dynamic}")
    print("Render the string above with any QR library (qrcode, segno).")


if __name__ == "__main__":
    main()
