# GoPay / GoBiz guide

[← Documentation home](../README.md) · [← Main README](../../README.md)

This guide covers the `GoPayMerchant` facade. It uses one shared client for authentication, merchant data, transactions, payouts, QRIS helpers, and payment watching.

```python
from qrismerchantid import GoPayMerchant

gopay = GoPayMerchant()
# gopay.auth, gopay.users, gopay.merchants, gopay.transactions, gopay.payouts
```

## Before you start

- Use an account you own or are authorized to test.
- Start with [authentication](auth.md), then verify the session with [merchants](merchants.md).
- GoPay transaction and payout amounts are in **minor units**. `5_000_000` means Rp50.000.
- Keep polling conservative and only while an active checkout is open.

## Common workflow

### 1. Authenticate

```python
challenge = gopay.auth.login(method="otp", phone_number="0812xxxxxxx")
session = gopay.auth.login(
    method="otp",
    otp=input("OTP: "),
    otp_token=challenge["otp_token"],
)
```

The portal returns `otp_length`; do not assume that every OTP has the same number of digits. Email/password login is also supported. See [auth.md](auth.md) for session persistence and refresh.

### 2. Find a merchant and read transactions

```python
result = gopay.merchants.search()
merchant_id = result["hits"][0]["id"]

feed = gopay.transactions.analytics(merchant_id, days=7)
print(feed["total"])
```

See [merchants.md](merchants.md) and [transactions.md](transactions.md) for filters, journals, and issuer breakdowns.

### 3. Optional: create a QRIS payload and watch a payment

```python
from qrismerchantid.gopay import qris

dynamic_qris = qris.inject_amount(static_qris, 50_000)
watcher = gopay.watch(merchant_id)
watcher.seed()  # call before displaying the QR
paid = watcher.wait_for_payment(5_000_000, timeout=300)
```

The QRIS helper is local-only; it does not initiate or confirm a payment. Read [qris.md](qris.md) and [watcher.md](watcher.md) before using these helpers.

## Configuration

```python
gopay = GoPayMerchant(
    access_token="...",
    refresh_token="...",
    timeout=30.0,
    max_retries=2,      # transport errors only
    backoff_base=0.5,
)
```

For HTTP/2, a proxy, or a custom CA, pass an `HttpxTransport`; see the focused pages for details.

## Pages

- [Authentication and sessions](auth.md)
- [Users and merchants](merchants.md)
- [Transactions](transactions.md)
- [Payouts](payouts.md)
- [QRIS helpers](qris.md)
- [Payment watcher](watcher.md)

## Compatibility note

The OTP browser portal can change independently of the data APIs. The current compatibility defaults are configurable through `QRISMERCHANTID_GOPAY_APP_VERSION`; if the provider changes its browser build, update the value rather than editing package code. See [auth.md](auth.md).
