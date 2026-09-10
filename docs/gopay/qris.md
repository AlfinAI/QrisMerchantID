# QRIS helpers — EMVCo parse, dynamic nominal, CRC16

Pure offline functions in `qrismerchantid.gopay.qris` (no network, no creds).

## Background

A QRIS string is EMVCo TLV: repeating `TAG(2) + LENGTH(2) + VALUE`. A *static*
QRIS has no nominal (tag `54` absent); a *dynamic* one sets tag `54` to the bill
and recomputes the trailing CRC (tag `63`, `CRC16-CCITT-FALSE`: poly `0x1021`,
init `0xFFFF`). This is exactly what every reference gateway does.

## API

```python
from qrismerchantid.gopay import qris

qris.parse(static)            # [(tag, value), ...]; ValueError if malformed
qris.get_tag(static, "59")    # merchant name, e.g. "NUXYS STORE"
qris.crc16_ccitt("123456789") # "29B1" (canonical check vector)
qris.inject_amount(static, 50000)  # dynamic QRIS, Tag 54 + valid CRC
```

`inject_amount` replaces tag `54` in place when present, else inserts it in tag
order; it strips any existing tag `63` first. Amounts are positive-int rupiah
(no decimals); anything else raises `ValueError`.

## Rendering & double-claims

Render the returned string with any QR library (`qrcode`, `segno`). When two
buyers pay the same nominal simultaneously, prevent double-claims the standard
way: add a unique code (Rp1–99) to the bill and dedupe by `transaction_id` /
`order_id` from the watcher on your side.
