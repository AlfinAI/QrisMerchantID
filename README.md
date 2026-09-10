# QrisMerchantID — Unofficial Indonesian QRIS merchant API client for Python

[![Tests](https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml/badge.svg)](https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/QrisMerchantID.svg)](https://pypi.org/project/QrisMerchantID/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

One Python package for Indonesia's QRIS merchant APIs. Provider lineup:

| Provider | Status | Scope |
|---|---|---|
| GoPay / GoBiz merchant | 🚧 building (FASE A1–A2) | login (password + OTP), merchants, transactions, payouts, QRIS helpers, payment watcher |
| ShopeePay partner | 🗺️ roadmap (FASE B) | login, stores, transactions — see `research/RESEARCH_GOPAY_SHOPEEPAY.md` §4 |

> Research/educational use only. Not affiliated with GoTo/GoPay/GoBiz or
> Shopee/Sea Group. Read-only by design in v0.1.0 — it only *reads* your own
> merchant data (login + history + payouts) and never moves money.

## Installation

```bash
pip install QrisMerchantID
```

Requires Python 3.10+ and one dependency: [`httpx`](https://www.python-httpx.org/).

## Quick start (GoPay — lands in FASE A1)

```python
from qrismerchantid import GoPayMerchant

gopay = GoPayMerchant()
gopay.auth.login_with_otp("+62812xxxxxxx")  # SMS code, then:
# gopay.auth.verify_otp(code)  -> session cached to disk
merchants = gopay.merchants.search()
txns = gopay.transactions.analytics(merchant_id=..., days=7)
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
