# QrisMerchantID — Unofficial Indonesian QRIS merchant API client for Python

[![Tests](https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml/badge.svg)](https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/QrisMerchantID.svg)](https://pypi.org/project/QrisMerchantID/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One Python package for Indonesia's QRIS merchant APIs. Provider lineup:

| Provider | Status | Scope |
|---|---|---|
| GoPay / GoBiz merchant | ✅ auth, users, merchants, transactions, payouts, QRIS, watcher | login (password + OTP), merchants, transactions, payouts, QRIS helpers, payment watcher |
| ShopeePay partner | 🗺️ roadmap (FASE B) | login, stores, transactions — see `research/RESEARCH_GOPAY_SHOPEEPAY.md` §4 |

> Research/educational use only. Not affiliated with GoTo/GoPay/GoBiz or
> Shopee/Sea Group. Read-only by design in v0.1.0 — it only *reads* your own
> merchant data (login + history + payouts) and never moves money.

## ⚠️ Disclaimer — harap dibaca dulu

**English.** This is an **unofficial, independent research project**. It is NOT
affiliated with, endorsed by, or supported by GoTo, GoPay, GoBiz, Shopee, Sea
Group, or any reference-repo author. It is provided for **research and
educational purposes only**, without warranty of any kind. Using unofficial
APIs may violate the providers' Terms of Service and can lead to rate limits,
suspension, or termination of your accounts. **You use this software entirely
at your own risk — the author (AlfinAI) shall not be liable for any loss,
damage, account action, or legal consequence arising from its use.** Credentials
and tokens you enter stay on your machine (they are only ever sent to the
providers' own official servers) — never commit `.env`, `*.har`, or token/OTP
cache files to any repository.

**Bahasa Indonesia.** Ini adalah **proyek riset independen yang tidak resmi
(unofficial)**. TIDAK berafiliasi, didukung, atau disetujui oleh GoTo, GoPay,
GoBiz, Shopee, Sea Group, maupun author repo referensi mana pun. Disediakan
**hanya untuk riset dan edukasi**, tanpa jaminan apa pun. Penggunaan API tidak
resmi dapat melanggar Syarat & Ketentuan penyedia dan berakibat akun dibatasi,
ditangguhkan, atau dihapus. **Segala risiko dan akibat yang timbul sepenuhnya
menjadi tanggung jawab pengguna — author (AlfinAI) tidak bertanggung jawab atas
kerugian, kerusakan, tindakan terhadap akun, atau konsekuensi hukum apa pun dari
penggunaan software ini.** Kredensial/token hanya tersimpan di mesin Anda (dan
hanya dikirim ke server resmi penyedia) — jangan pernah commit file `.env`,
`*.har`, atau cache token/OTP ke repo mana pun.

## Contents

- [Installation](#installation)
- [Core concepts](#core-concepts) (minor units · sessions · errors)
- [GoPay guide](#gopay-guide)
  - [Login](#1-login--otp--password) · [Session cache](#2-session-cache)
  - [Users & merchants](#3-users--merchants) · [Transactions](#4-transactions)
  - [Payouts](#5-payouts) · [QRIS dynamic](#6-qris-dynamic)
  - [Payment watcher](#7-payment-watcher) · [Configuration](#8-configuration)
- [Development](#development) · [Research](#research) · [Credits](#credits)

## Installation

```bash
pip install QrisMerchantID
```

Requires Python 3.10+ and one dependency: [`httpx`](https://www.python-httpx.org/).

## Core concepts

Three things to understand before anything else:

1. **Amounts are minor units (sen).** Analytics answers ints (`gross_amount:
   10600000`), payouts answer decimal strings (`"10600000.0"`) — both mean
   Rp106.000. Convert with `money.to_rupiah()`; never guess.
2. **Sessions carry no server expiry.** `/goid/token` answers
   `{access_token, refresh_token}` with no `expires_in`, so the SDK caches the
   session and you revalidate cheaply (`merchants.search()`); on HTTP 401,
   log in again.
3. **Every HTTP error raises `ApiException`.** It carries `.http_status`,
   `.code` (when the provider sent one), `.payload` (full body), and a readable
   message. Transport errors (DNS/connect/timeout) retry with backoff; HTTP
   errors never retry.

## GoPay guide

Everything lives on one facade sharing a single client:

```python
from qrismerchantid import GoPayMerchant

gopay = GoPayMerchant()
gopay.auth          # login: password + OTP
gopay.users         # portal profile
gopay.merchants     # search + detail
gopay.transactions  # analytics + journals + issuer breakdown
gopay.payouts       # payout history + payable balance
gopay.watch(...)    # payment watcher factory
```

### 1. Login — OTP & password

GoBiz (GoID) login answers **HTTP 201** on success. Two flows:

```python
# --- OTP (recommended: no password stored anywhere) ---
otp = gopay.auth.request_otp("0812xxxxxxx")  # SMS, 4 digits, ~12 min window
# otp -> {"otp_token", "otp_expires_in", "otp_length", "next_state"}
session = gopay.auth.login_with_otp(input("OTP: "), otp["otp_token"])

# --- Password (verified against reference code; live re-check is TODO-R1) ---
session = gopay.auth.login_with_password("you@shop.id", "secret")

session  # -> {"access_token", "refresh_token", ...} — also set on the client
```

Notes (all verified against a live portal capture, research §9):

- `request_otp()` sends **no `login_type` field** — the portal doesn't either.
  (Some reference repos send one; the server ignores it.)
- Phone numbers may carry spaces/dashes (`"0812 345-678"` is normalized);
  `country_code` defaults to `"62"`.
- Keep `otp_token` server-side between the two calls (or
  `token_cache.save_pending_otp()`); it expires with the code.

### 2. Session cache

Skip OTP on the next run by caching the session to disk:

```python
from qrismerchantid.core import token_cache

token_cache.save(".gopay-session.json", session)

session = token_cache.load(".gopay-session.json")  # None if missing/invalid
gopay = GoPayMerchant(access_token=session["access_token"]) if session else GoPayMerchant()
```

Recommended loop for long-running gateways: load cache → cheap
`merchants.search()` probe → on 401, login again and re-save. See
`examples/02_merchants.py`.

### 3. Users & merchants

```python
me = gopay.users.me()
# -> {"user": {"id", "email", "full_name", "phone", "roles", "scopes", ...}}

found = gopay.merchants.search()            # {"total", "success", "hits"}
found = gopay.merchants.search(from_=40, size=5)
merchant_id = found["hits"][0]["id"]        # IDs look like "G…"

detail = gopay.merchants.detail(merchant_id)
# -> full object: KYC, outlet, bank, active_payment_channels, payment_settings…
```

`search()` doubles as the token-validity probe used by every reference gateway.

### 4. Transactions

The primary feed is **merchant-analytics** (query shape verified 1:1):

```python
txns = gopay.transactions.analytics(merchant_id, days=7)
txns = gopay.transactions.analytics(
    merchant_id, start_time="2026-09-01T00:00:00.000Z", end_time="2026-09-08T00:00:00.000Z"
)
txns = gopay.transactions.analytics(["G111", "G222"], days=1, size=50)  # multi-outlet
# -> {"from", "size", "total", "transactions": [...]}
```

Each transaction carries 23 keys, including `order_id` (`QRIS-…`),
`transaction_status` (`SETTLEMENT`/`CAPTURE`/`REFUND`/`PARTIAL_REFUND`),
`payment_type`, `channel_type` (`STATIC_QR`), `transaction_source`
(`GOPAY_INSTORE`), `qris_provider_aspi_issuer`/`…_acquirer`, `shares`,
`promo_details`. Defaults mirror the portal exactly
(`statuses=SETTLEMENT,…`, `payment_types=QRIS,GOPAY,…`) and are overridable.

Two more reads on `/journals/search` (special journal headers handled for you):

```python
journal = gopay.transactions.journals(merchant_id, start, end, size=50)
by_issuer = gopay.transactions.qris_issuer_breakdown(start, end)
# -> {"aggregations": {"by_qris_issuer": {"buckets": [...]}}}
```

### 5. Payouts

HAR-discovered endpoints — absent from every reference repo:

```python
page = gopay.payouts.list()              # ?page=1&per=10
page = gopay.payouts.list(page=2, per=25)
# -> {"payouts": [{"payout_id", "net_amount", "gross_amount", "status": "paid",
#      "paid_at", "account_no", ...}], "current_page", "per", "next_page"}

payable = gopay.payouts.payable_detail(merchant_id)
# -> {"payable_detail": {"payable", "net_amount", "total_settlement", fees…}}
```

Amounts here are **decimal strings in minor units** — `to_rupiah("11610000.0")`.

### 6. QRIS dynamic

Pure offline helpers (`qrismerchantid.gopay.qris`): parse a static QRIS as EMVCo
TLV, set tag `54` to the bill, recompute **CRC16-CCITT**, done:

```python
from qrismerchantid.gopay import qris

qris.get_tag(static_qris, "59")          # merchant name, e.g. "NUXYS STORE"
dynamic = qris.inject_amount(static_qris, 50000)  # Rp50.000, CRC valid
qris.get_tag(dynamic, "54")              # "50000"
```

Render `dynamic` with any QR library (`qrcode`, `segno`) and display it at
checkout. **Anti double-claim** (when two buyers pay the same nominal at once):
add a unique code (Rp1–99) to the bill and dedupe by the watcher's
`transaction_id`/`order_id` on your side — the same recipe every gateway uses.

### 7. Payment watcher

The classic gateway loop, ported from `gobiz.js`: seed → poll → match nominal:

```python
watcher = gopay.watch(merchant_id)  # poll_interval=6.0 like the references
watcher.seed()                      # mark current history as seen, returns count

paid = watcher.wait_for_payment(5_000_000, timeout=300)  # Rp50.000 in minor units
paid = watcher.wait_for_payment(5_000_000, timeout=300, tolerance=100)
# -> raw transaction dict; raises TimeoutError when the invoice lapses
```

Lower-level: `watcher.poll_once()` returns only never-seen transactions (seen
cache capped at 500). Polling etiquette: keep the 6s interval, poll only while
a checkout is active — aggressive polling is how accounts get rate-limited.

### 8. Configuration

```python
gopay = GoPayMerchant(
    access_token="...",
    timeout=30.0,       # seconds
    max_retries=2,      # transport errors only — never HTTP errors
    backoff_base=0.5,   # exponential: 0.5s, 1s, 2s, ...
    app_version="platform-v3.119.0-eab7f749",  # default follows the analyzed portal
    user_agent="...",
)
```

Need HTTP/2, a proxy, or a custom CA? Pass your own transport:

```python
import httpx
from qrismerchantid.core.transport import HttpxTransport

transport = HttpxTransport(httpx.Client(http2=True, proxy="http://localhost:8080"))
gopay = GoPayMerchant(transport=transport)
```

## Development

```bash
pip install -e ".[dev]"
pytest          # 100% offline — never hits the real API
ruff check src tests && ruff format --check src tests
mypy src        # strict
python -m build
```

Runnable flows (need real merchant credentials via env, except QRIS):
`examples/` — `01_login_otp.py`, `02_merchants.py`, `03_transactions.py`,
`04_qris_dynamic.py`, `05_watch_payment.py`.

## Research

Full endpoint research (repos surveyed + anonymized HAR verification):
`research/RESEARCH_GOPAY_SHOPEEPAY.md`. Per-service pages: `docs/gopay/`.

## Credits

API knowledge: [kavionn/gobiz-payment](https://github.com/kavionn/gobiz-payment),
[warungerik/API-GOPAY-MERCHANT](https://github.com/warungerik/API-GOPAY-MERCHANT),
[alhifnywahid/merchantid](https://github.com/alhifnywahid/merchantid),
[ahmadzakiyox/gopay-api-gateaway](https://github.com/ahmadzakiyox/gopay-api-gateaway),
[ahmadzakiyox/shoppepay-api-gateway](https://github.com/ahmadzakiyox/shoppepay-api-gateway),
[namtxs/gopay-api](https://github.com/namtxs/gopay-api).
Python package maintained by AlfinAI.

## License

MIT — see [LICENSE](LICENSE).
