# QRIS helpers

`qrismerchantid.gopay.qris` contains pure, offline EMVCo/QRIS helpers. It does
not call a provider, register a merchant, or verify whether a bank will accept
a modified payload.

## What the helper changes

A QRIS payload is a sequence of TLV fields:

```text
TAG (2 characters) + LENGTH (2 digits) + VALUE
```

`inject_amount()` preserves the merchant account fields and merchant identity,
adds or replaces tag `54`, removes the old tag `63`, and calculates a new
CRC16-CCITT-FALSE checksum. It does **not** rewrite tag `59` or `60`, and it
does not change tag `01` from static (`11`) to dynamic (`12`). Those provider
rules must be handled by the payment/acquirer integration, not assumed from a
locally valid CRC.

```python
from qrismerchantid.gopay import qris

qris.parse(static)             # [(tag, value), ...]
qris.get_tag(static, "59")     # merchant name
qris.crc16_ccitt("123456789")  # "29B1"
payload = qris.inject_amount(static, 50000)
assert qris.get_tag(payload, "54") == "50000"
```

`inject_amount()` accepts a positive integer rupiah amount. It raises
`ValueError` for malformed TLV input or an invalid amount. The helper is useful
for offline experiments and integrations that explicitly support this
transformation; a valid checksum alone is not proof that every bank or wallet
will accept the result.

## Rendering

Render the returned payload with a QR library such as `qrcode` or `segno`:

```python
import qrcode

image = qrcode.make(payload)
image.save("payment-qr.png")
```

Always test with the actual payment channels used by your customers. If a
provider returns a merchant-not-found error, restore the provider-issued
merchant identity and use a provider-supported dynamic QR flow instead of
repeatedly changing tags `59` and `60`.

## Matching and double claims

When two buyers can pay the same amount at the same time, add a unique amount
or reference only when the provider supports it. On your side, deduplicate by
the provider transaction ID or order ID and expire invoices explicitly.

## Attribution

The QRIS helper is part of the independent QrisMerchantID research project.
Related open-source research references are listed in the repository README and
`reference/MANIFEST.md`, including
[`lintangtimur/ovoid`](https://github.com/lintangtimur/ovoid).
