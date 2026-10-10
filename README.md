<p align="center">
  <img src="assets/logo.png" alt="QrisMerchantID logo" width="140" />
</p>

<h1 align="center">QrisMerchantID</h1>

<p align="center">
  Unofficial Indonesian QRIS merchant API client for Python — GoPay/GoBiz + ShopeePay
</p>

<p align="center">
  <a href="https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml"><img src="https://github.com/AlfinAI/QrisMerchantID/actions/workflows/test.yml/badge.svg" alt="Tests" /></a>
  <a href="https://pypi.org/project/QrisMerchantID/"><img src="https://img.shields.io/pypi/v/QrisMerchantID.svg" alt="PyPI" /></a>
  <a href="https://pypi.org/project/QrisMerchantID/"><img src="https://img.shields.io/pypi/pyversions/QrisMerchantID.svg" alt="Python" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" /></a>
  <a href="https://t.me/JoestarMojo"><img src="https://img.shields.io/badge/Telegram-@JoestarMojo-26A5E4?logo=telegram" alt="Telegram" /></a>
  <a href="https://github.com/AlfinAI/QrisMerchantID/discussions"><img src="https://img.shields.io/github/discussions/AlfinAI/QrisMerchantID?label=discussions" alt="Discussions" /></a>
</p>

> ⚠️ **Unofficial research project.** Not affiliated with, endorsed by, or supported by GoTo,
> GoPay, GoBiz, Shopee, Sea Group, or any reference-repo author. For **research and educational
> purposes only** — unofficial APIs may violate providers' Terms of Service and can lead to rate
> limits, suspension, or termination of your accounts. **Use entirely at your own risk.**
> <details><summary>Full disclaimer (English + Bahasa Indonesia)</summary>
>
> **English.** This is an **unofficial, independent research project**. It is provided without
> warranty of any kind. The author (AlfinAI) shall not be liable for any loss, damage, account
> action, or legal consequence arising from its use. Credentials and tokens you enter stay on your
> machine (they are only ever sent to the providers' own official servers) — never commit `.env`,
> `*.har`, or token/OTP cache files to any repository.
>
> **Bahasa Indonesia.** Ini adalah **proyek riset independen yang tidak resmi (unofficial)**.
> TIDAK berafiliasi, didukung, atau disetujui oleh GoTo, GoPay, GoBiz, Shopee, Sea Group, maupun
> author repo referensi mana pun. Disediakan **hanya untuk riset dan edukasi**, tanpa jaminan apa
> pun. **Segala risiko dan akibat yang timbul sepenuhnya menjadi tanggung jawab pengguna.**
> Kredensial/token hanya tersimpan di mesin Anda — jangan pernah commit file `.env`, `*.har`,
> atau cache token/OTP ke repo mana pun.
> </details>

One Python package for Indonesia's QRIS merchant APIs — read your own merchant data with typed,
tested, offline-friendly code.

## Features

| Provider          | Capabilities                                                                                 |
| ----------------- | -------------------------------------------------------------------------------------------- |
| 🧾 GoPay / GoBiz  | OTP or email+password login · merchants · transactions · payouts · dynamic QRIS · payment watcher |
| 🛍️ ShopeePay      | OTP login or manual `B:` token · stores · normalized feed with issuer lookup · payment watcher |

- 🔬 **Researched, not guessed** — every endpoint traced to a traffic capture or a reference repo;
  unknowns are marked `TODO`, never shipped as fact.
- 🧪 **Offline-first** — the full test suite runs without network access or credentials.

## Contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Documentation](#documentation)
- [Core concepts](#core-concepts) — money · sessions · errors
- [Configuration](#configuration) — portal compatibility & environment variables
- [Examples](#examples)
- [Development](#development)
- [Research](#research)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Credits](#credits) · [Contact](#contact) · [Sponsor](#sponsor)
- [License](#license)

## Installation

```bash
pip install QrisMerchantID
```

Requires **Python 3.10+** and one dependency: [`httpx`](https://www.python-httpx.org/).

## Quickstart

```python
from qrismerchantid import GoPayMerchant, ShopeePayPartner

# --- GoPay: pick OTP or email login, then read your history ---
gopay = GoPayMerchant()
otp = gopay.auth.login(method="otp", phone_number="0812xxxxxxx")
session = gopay.auth.login(method="otp", otp=input("OTP: "), otp_token=otp["otp_token"])
# ...or one step: gopay.auth.login(method="email", email="you@shop.id", password="secret")
txns = gopay.transactions.analytics("G...", days=7)
print(txns["total"], "transactions")

# --- ShopeePay: token (or sp.auth OTP login), then watch a store ---
sp = ShopeePayPartner(token="B:...")   # token how-to: docs/shopee/token.md
print(sp.stores.list_stores())
watcher = sp.watch(7)
watcher.seed()
paid = watcher.wait_for_payment(409662, timeout=300)  # Rp409.662
print("PAID:", paid["id"])
```

## Documentation

Each provider has its own guide with the full tutorial and flow diagrams:

| Provider          | Guide                      | Status                                                            |
| ----------------- | -------------------------- | ----------------------------------------------------------------- |
| GoPay / GoBiz     | [docs/gopay/](docs/gopay/)   | ✅ auth, users, merchants, transactions, payouts, QRIS, watcher    |
| ShopeePay partner | [docs/shopee/](docs/shopee/) | ✅ OTP login, stores, transactions + issuer, watcher (`B:` or OTP) |

Start at the [docs index](docs/README.md). APK research knowledge base: [KB index](docs/KB_QRIS_MERCHANT_INDEX.md).

## Core concepts

Three things to understand before anything else:

1. **Money differs per provider — never mix them.**
   - GoPay answers minor units (sen): `gross_amount: 10600000` = Rp106.000 → convert with
     `gopay.money.to_rupiah()`.
   - ShopeePay answers whole rupiah as grouped strings: `"409.662"` = Rp409.662 → parse with
     `shopee.money.parse_id_amount()`.
2. **Sessions are yours to keep.**
   - GoPay: cache the `access_token` and revalidate cheaply (`merchants.search()`). The client
     automatically refreshes once on an expired-token response when both access and refresh tokens
     are configured; if refresh is rejected, stop polling and log in again.
   - ShopeePay: log in with OTP and `refresh_session()` without re-OTP, or paste a manual `B:`
     token; on codes `200020` / `2010000`, renew it.
3. **Every HTTP error raises `ApiException`.** It carries `.http_status`, `.code` (when the
   provider sent one), `.payload` (full body), and a readable message. Transport errors
   (DNS/connect/timeout) retry with backoff; HTTP errors never retry.

## Configuration

### GoPay OTP portal compatibility

The current browser portal uses `https://portal.gofoodmerchant.co.id` for `/goid/login/request`
and `/goid/token`; merchant/data APIs remain on `https://api.gobiz.co.id`. The default browser
build is `platform-v3.125.0-e1923971` with Chrome 148 metadata. If GoBiz rolls a new build,
override it without editing code:

```bash
export QRISMERCHANTID_GOPAY_APP_VERSION="platform-v3.xxxxx"
```

Read `otp_length` from the `request_otp()` response; do not assume the OTP is six digits.

### Client options

Both facades accept the same tuning knobs:

```python
gopay = GoPayMerchant(
    access_token=session["access_token"],
    refresh_token=session["refresh_token"],
    timeout=30.0,      # seconds
    max_retries=2,     # transport errors only — never HTTP errors
    backoff_base=0.5,  # exponential: 0.5s, 1s, 2s, ...
)
```

Need HTTP/2, a proxy, or a custom CA? Pass your own transport
(`qrismerchantid.core.transport.HttpxTransport`). Full per-provider options:
[GoPay config](docs/gopay/README.md#8-configuration) ·
[ShopeePay config](docs/shopee/README.md#5-configuration).

## Examples

Runnable flows in [`examples/`](examples/) (need real merchant credentials via env, except QRIS):

| #  | File                      | What it does              |
| -- | ------------------------- | ------------------------- |
| 01 | `01_login_otp.py`         | GoPay OTP login           |
| 02 | `02_merchants.py`         | GoPay merchants           |
| 03 | `03_transactions.py`      | GoPay transactions        |
| 04 | `04_qris_dynamic.py`      | Dynamic QRIS (offline)    |
| 05 | `05_watch_payment.py`     | GoPay payment watcher     |
| 06 | `06_shopee_stores.py`     | ShopeePay stores          |
| 07 | `07_shopee_transactions.py` | ShopeePay transactions  |
| 08 | `08_shopee_watch.py`      | ShopeePay payment watcher |
| 09 | `09_shopee_login_otp.py`  | ShopeePay OTP login       |

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
[`research/RESEARCH_GOPAY_SHOPEEPAY.md`](research/RESEARCH_GOPAY_SHOPEEPAY.md) · ShopeePay deep-dive
[`research/ANALYSIS_SHOPEEPAY_PHASE_B.md`](research/ANALYSIS_SHOPEEPAY_PHASE_B.md) · GoBiz OTP
incident report [`research/REPORT_GOBIZ_OTP_2026-09-19.md`](research/REPORT_GOBIZ_OTP_2026-09-19.md).

**APK research knowledge base** (GoPay Merchant 2.3.0 + GoFood Merchant 5.49.0 — ±240 endpoints,
hosts, deeplinks, masked security findings):

- 📚 Start here: [KB index](docs/KB_QRIS_MERCHANT_INDEX.md) · machine-readable data in
  [`reference/`](reference/) · [agent guide](docs/KB_QRIS_MERCHANT_AGENT_GUIDE.md)
- 🔁 Reproduce it yourself / port to another language: [APK research reproduction
  guide](docs/APK_RESEARCH_REPRODUCTION_GUIDE.md)
- 🛡️ Security researchers & vendors: [responsible disclosure](docs/SECURITY_DISCLOSURE.md) (also
  see [SECURITY.md](SECURITY.md))

## Roadmap

- [x] GoPay provider — auth (OTP + email), merchants, transactions, payouts, QRIS, watcher.
- [x] ShopeePay provider — OTP login, stores, feed + issuer lookup, watcher.
- [ ] Live verification against real partner accounts (TODO-S1, TODO-R3) — field reports welcome in
      [Discussions](https://github.com/AlfinAI/QrisMerchantID/discussions).
- [x] `v0.3.0` source release.
- [x] `v0.3.2` GoPay browser OTP compatibility release.
- [ ] PyPI publication — prepare-only until a clean secret scan and release review are complete.
- [ ] Your idea here — open a Discussion or a feature request.

## Contributing

- 🐞 Found a bug? [Open a bug
  report](https://github.com/AlfinAI/QrisMerchantID/issues/new?template=bug_report.md) — offline
  repro snippets get fixed fastest.
- 💡 Want an endpoint? [Request
  it](https://github.com/AlfinAI/QrisMerchantID/issues/new?template=feature_request.md) with a
  traffic sample or upstream link as evidence.
- 💬 Questions, ideas, show-and-tell →
  [Discussions](https://github.com/AlfinAI/QrisMerchantID/discussions).
- 🔒 Security issue? See [SECURITY.md](SECURITY.md) — never file it publicly.
- 🤝 Pull requests welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

API knowledge: [kavionn/gobiz-payment](https://github.com/kavionn/gobiz-payment),
[warungerik/API-GOPAY-MERCHANT](https://github.com/warungerik/API-GOPAY-MERCHANT),
[alhifnywahid/merchantid](https://github.com/alhifnywahid/merchantid),
[lintangtimur/ovoid](https://github.com/lintangtimur/ovoid) (attribution/reference),
[ahmadzakiyox/gopay-api-gateaway](https://github.com/ahmadzakiyox/gopay-api-gateaway),
[ahmadzakiyox/shoppepay-api-gateway](https://github.com/ahmadzakiyox/shoppepay-api-gateway),
[namtxs/gopay-api](https://github.com/namtxs/gopay-api). Python package maintained by AlfinAI.

## Contact

Questions, bug reports, or research collaboration — Telegram:
**[@JoestarMojo](https://t.me/JoestarMojo)**.

## Sponsor

If this project saves you time, consider sponsoring — it keeps the research going:

[![Sponsor](https://img.shields.io/badge/Sponsor-AlfinAI-ea4aaa?logo=githubsponsors)](https://github.com/sponsors/AlfinAI)

🇮🇩 Indonesia: [Saweria](https://saweria.co/JoestarMojoTele)

## License

MIT — see [LICENSE](LICENSE).
