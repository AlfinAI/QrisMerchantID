# ShopeePay Partner guide

[← Documentation home](../README.md) · [← Main README](../../README.md)

This guide covers the `ShopeePayPartner` facade. It supports a manual `B:` token and programmatic OTP login, then exposes stores, a normalized transaction feed, and a payment watcher.

```python
from qrismerchantid import ShopeePayPartner

sp = ShopeePayPartner(token="B:...")
# sp.auth, sp.stores, sp.transactions
```

## Before you start

- Use a token or account you own or are authorized to test.
- The fastest path is [a manual token](token.md); use [OTP login](auth.md) when you need a repeatable login flow.
- Normalized transaction amounts are **whole rupiah**. `409_662` means Rp409.662.
- Store IDs are numeric strings and are required by the feed and watcher.

## Common workflow

### 1. Authenticate

Manual token:

```python
sp = ShopeePayPartner(token="B:...")
```

Programmatic OTP:

```python
challenge = sp.auth.request_otp("0812xxxxxxx", password="...")
outcome = sp.auth.login_with_otp(challenge, input("OTP: "))
session = outcome["session"]
sp.set_token(session["token"])
```

A multi-merchant account returns `merchant-selection-required` instead of guessing. Follow [auth.md](auth.md) to select a merchant and renew a session without requesting another OTP.

> OTP delivery may require device-risk telemetry from your own browser. The project does not ship a shared device fingerprint or risk blob; see [device-risk.md](device-risk.md).

### 2. Discover a store and read transactions

```python
stores = sp.stores.list_stores()
store_id = stores[0]["id"]
feed = sp.transactions.list_recent(store_id, minutes=15)
print(len(feed["transactions"]))
```

The normalized feed uses epoch seconds for time filters and removes rows belonging to another store. See [stores.md](stores.md) and [transactions.md](transactions.md).

### 3. Optional: watch a payment

```python
watcher = sp.watch(store_id)
watcher.seed()  # call before displaying the QR
paid = watcher.wait_for_payment(409_662, timeout=300)
```

Use [watcher.md](watcher.md) for polling, deduplication, and replay handling. The QRIS helper is provider-agnostic and local-only; the GoPay page documents it in [qris.md](../gopay/qris.md).

## Configuration

```python
sp = ShopeePayPartner(
    token="B:...",
    timeout=30.0,
    max_retries=2,      # transport errors only
    backoff_base=0.5,
    language="id",
    timezone="Asia/Jakarta",
)
```

## Pages

- [Authentication and session renewal](auth.md)
- [Manual token](token.md)
- [Stores](stores.md)
- [Transactions](transactions.md)
- [Payment watcher](watcher.md)
- [Device-risk telemetry](device-risk.md)
