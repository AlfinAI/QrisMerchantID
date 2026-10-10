# Documentation

Public provider guides and APK research notes for QrisMerchantID.

## Start here

| Guide | Covers |
| ----- | ------ |
| [Main README](../README.md) | Installation, quickstart, scope, safety notes |
| [GoPay / GoBiz guide](gopay/README.md) | Auth, merchants, transactions, QRIS helpers, payouts, payment watcher |
| [ShopeePay guide](shopee/README.md) | OTP/manual-token login, stores, transactions, payment watcher |
| [QRIS merchant research index](KB_QRIS_MERCHANT_INDEX.md) | Evidence status and open questions from the APK research |

## Provider pages

Each provider guide is split into a short overview and focused pages so the README stays readable:

| Provider | Overview | Focused pages |
| -------- | -------- | ------------- |
| GoPay / GoBiz | [`gopay/README.md`](gopay/README.md) | [auth](gopay/auth.md) · [merchants](gopay/merchants.md) · [transactions](gopay/transactions.md) · [payouts](gopay/payouts.md) · [qris](gopay/qris.md) · [watcher](gopay/watcher.md) |
| ShopeePay | [`shopee/README.md`](shopee/README.md) | [auth](shopee/auth.md) · [token](shopee/token.md) · [stores](shopee/stores.md) · [transactions](shopee/transactions.md) · [device-risk](shopee/device-risk.md) · [watcher](shopee/watcher.md) |

## Research and security

- [APK research reproduction guide](APK_RESEARCH_REPRODUCTION_GUIDE.md) — reproduce the APK
  inspection without committing APKs, HAR files, or credentials.
- [Research agent guide](KB_QRIS_MERCHANT_AGENT_GUIDE.md) — evidence rules and terminology used
  in the knowledge base.
- [Responsible disclosure](SECURITY_DISCLOSURE.md) — how security findings from the APK research
  are handled.
- [Security policy](../SECURITY.md) — report a suspected vulnerability privately.

## Reference data

Machine-readable inventories in [`../reference/`](../reference/):

| File | Contents |
| ---- | -------- |
| `hosts.csv` | Hosts observed in the analyzed applications |
| `endpoints.csv` | Strings and endpoint candidates extracted from the APKs |
| `temuan_keamanan.csv` | Masked security observations and their TODOs |
| `MANIFEST.md` | Inventory and provenance of the research artifacts |

A row marked `BELUM TERVERIFIKASI` is an observation or candidate, not a claim that the endpoint
is live or usable. See the research index before relying on it.

## Documentation rules

- Keep examples offline-testable unless a page explicitly says live credentials are required.
- Mark unknowns as `BELUM TERVERIFIKASI` and link the evidence or TODO.
- Never include real tokens, OTPs, phone numbers, passwords, HAR files, or session caches in
  documentation.
- Keep provider-specific units explicit: GoPay may use minor units; ShopeePay uses whole rupiah in
  the normalized feed.
