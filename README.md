# QrisMerchantID — Unofficial Indonesian QRIS merchant API client for Python

[![Tests](https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml/badge.svg)](https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/QrisMerchantID.svg)](https://pypi.org/project/QrisMerchantID/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One Python package for Indonesia's QRIS merchant APIs. Provider lineup:

| Provider | Status | Scope |
|---|---|---|
| GoPay / GoBiz merchant | ✅ A1 auth + users + merchants · 🚧 A2 transactions/payouts/QRIS/watcher | login (password + OTP), merchants, transactions, payouts, QRIS helpers, payment watcher |
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

## Installation

```bash
pip install QrisMerchantID
```

Requires Python 3.10+ and one dependency: [`httpx`](https://www.python-httpx.org/).

## Quick start — GoPay login

```python
from qrismerchantid import GoPayMerchant

gopay = GoPayMerchant()

# Login once via SMS OTP (4 digits, ~12 min window):
otp = gopay.auth.request_otp("0812xxxxxxx")
session = gopay.auth.login_with_otp(input("OTP: "), otp["otp_token"])
# ...or with a password: gopay.auth.login_with_password("you@shop.id", "secret")

me = gopay.users.me()
merchants = gopay.merchants.search()  # -> {"total", "success", "hits"}
detail = gopay.merchants.detail(merchants["hits"][0]["id"])
```

Cache the session to skip OTP next time (GoBiz sessions carry no server expiry —
revalidate cheaply and re-login on 401):

```python
from qrismerchantid.core import token_cache

token_cache.save(".gopay-session.json", session)
session = token_cache.load(".gopay-session.json")
gopay = GoPayMerchant(access_token=session["access_token"]) if session else GoPayMerchant()
```

## Development

```bash
pip install -e ".[dev]"
pytest          # 100% offline — never hits the real API
ruff check src tests && ruff format --check src tests
mypy src        # strict
python -m build
```

## Research

Full endpoint research (repos surveyed + anonymized HAR verification):
`research/RESEARCH_GOPAY_SHOPEEPAY.md`.

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
