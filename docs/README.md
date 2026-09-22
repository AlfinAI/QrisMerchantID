# Documentation

This directory contains the public provider guides and the APK research notes for
QrisMerchantID.

## Start here

- [Main README](../README.md) — installation, quick start, scope, and safety notes.
- [GoPay / GoBiz guide](gopay/README.md) — authentication, merchants, transactions,
  QRIS helpers, payouts, and the payment watcher.
- [ShopeePay guide](shopee/README.md) — OTP/manual-token login, stores, transactions,
  and the payment watcher.
- [QRIS merchant research index](KB_QRIS_MERCHANT_INDEX.md) — evidence status and
  open questions from the APK research.

## Research and security

- [Research reproduction guide](APK_RESEARCH_REPRODUCTION_GUIDE.md) — reproduce the
  APK inspection without committing APKs, HAR files, or credentials.
- [Research agent guide](KB_QRIS_MERCHANT_AGENT_GUIDE.md) — evidence rules and
  terminology used in the knowledge base.
- [Security disclosure](SECURITY_DISCLOSURE.md) — responsible handling of findings.
- [Security policy](../SECURITY.md) — report a suspected vulnerability privately.

## Reference data

The machine-readable inventories live in [`../reference/`](../reference/):

- `hosts.csv` — hosts observed in the analyzed applications.
- `endpoints.csv` — strings and endpoint candidates extracted from the APKs.
- `temuan_keamanan.csv` — masked security observations and their TODOs.
- `MANIFEST.md` — inventory and provenance of the research artifacts.

A row marked `BELUM TERVERIFIKASI` is an observation or candidate, not a claim
that the endpoint is live or usable. See the research index before relying on it.

## Provider pages

Each provider guide is split into a short overview and focused pages so that the
README stays readable:

| Provider | Overview | Focused pages |
| --- | --- | --- |
| GoPay / GoBiz | [`gopay/README.md`](gopay/README.md) | auth, merchants, transactions, payouts, QRIS, watcher |
| ShopeePay | [`shopee/README.md`](shopee/README.md) | auth, token, stores, transactions, device risk, watcher |

## Documentation rules

- Keep examples offline-testable unless a page explicitly says that live credentials
  are required.
- Mark unknowns as `BELUM TERVERIFIKASI` and link the evidence or TODO.
- Never include real tokens, OTPs, phone numbers, passwords, HAR files, or session
  caches in documentation.
- Keep provider-specific units explicit: GoPay may use minor units; ShopeePay uses
  whole rupiah in the normalized feed.
