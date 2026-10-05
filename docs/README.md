# Documentation

This is the documentation hub for QrisMerchantID. If you are new to the project, read this page first, then choose one provider guide.

## Recommended path

1. Read the [main README](../README.md) for installation, scope, safety, and a first example.
2. Choose a provider:
   - [GoPay / GoBiz](gopay/README.md)
   - [ShopeePay Partner](shopee/README.md)
3. Read the provider's authentication page before using a live account.
4. Read the transactions page before interpreting amounts or timestamps.
5. Add QRIS generation and payment watching only after the basic read-only flow works.

## Provider guides

| Provider | Overview | Authentication | Data | Optional features |
| --- | --- | --- | --- | --- |
| GoPay / GoBiz | [Guide](gopay/README.md) | [Auth](gopay/auth.md) | [Merchants](gopay/merchants.md), [transactions](gopay/transactions.md) | [Payouts](gopay/payouts.md), [QRIS](gopay/qris.md), [watcher](gopay/watcher.md) |
| ShopeePay Partner | [Guide](shopee/README.md) | [Auth](shopee/auth.md), [manual token](shopee/token.md) | [Stores](shopee/stores.md), [transactions](shopee/transactions.md) | [Watcher](shopee/watcher.md), [device risk](shopee/device-risk.md) |

## Research and security

Research notes describe observations, not a promise that an endpoint is public, stable, or suitable for production:

- [Research index](../research/README.md)
- [APK research index](KB_QRIS_MERCHANT_INDEX.md)
- [APK reproduction guide](APK_RESEARCH_REPRODUCTION_GUIDE.md)
- [Research agent guide](KB_QRIS_MERCHANT_AGENT_GUIDE.md)
- [Responsible disclosure](SECURITY_DISCLOSURE.md)
- [Security policy](../SECURITY.md)

`BELUM TERVERIFIKASI` means **not verified**. Treat that item as a hypothesis and do not probe a provider without authorization.

## Reference data

The machine-readable inventories are in [`../reference/`](../reference/):

- `hosts.csv` — hosts observed in analyzed applications.
- `endpoints.csv` — endpoint strings and candidates.
- `temuan_keamanan.csv` — masked security observations and follow-up TODOs.
- `MANIFEST.md` — provenance and inventory of research artifacts.

These files are for research and review. They are not a list of supported public APIs.

## Documentation conventions

- Examples use placeholders and must not contain real credentials, tokens, OTPs, cookies, or HAR files.
- Provider-specific units and time formats are always stated near the example.
- Unknown or unverified claims are labelled and linked to evidence or a TODO.
- Keep network behaviour conservative: use the documented polling interval and only poll during an active checkout.
- When an API changes, update the provider page, an example if needed, and `CHANGELOG.md` together.
