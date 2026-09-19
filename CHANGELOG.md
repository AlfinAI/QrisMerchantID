# Changelog

## [Unreleased]

## [0.3.0] - 2026-09-19

### Fixed

- GoPay: OTP `request_otp()` follows the live portal again (2026-09-19 capture): `X-AppVersion`
  bumped to `platform-v3.122.0-72edb090`, and phone numbers are normalized to the bare national
  format the portal sends (`0851…`/`+62851…` → `851…`); non-dialable input now raises `ValueError`
  instead of failing server-side. Full analysis: `research/REPORT_GOBIZ_OTP_2026-09-19.md`.
- GoPay: `login_with_password()` verified against live traffic (email HAR 2026-09-19, closes
  TODO-R1) — validates email format + non-blank password locally; prerequisite documented (merchant
  must have email+password set in the portal, else the server rejects). OTP vs email is now an
  explicit either-or login choice.

### Added

- GoPay: `auth.login(method="otp"|"email", ...)` — one entry point with an explicit login-method
  choice (OTP stays two-step, email is one step).
- ShopeePay: `transactions.transaction_detail(order_sn)` — issuer lookup via
  `get-transaction-detail` (shape deobfuscated from the zaki gateway `server.js`); normalized rows
  gain `status_name` (`{1:pending, 2:failed, 3:success, 4:refunded, 5:expired}`); research
  TODO-S2/S4 closed (`ANALYSIS_SHOPEEPAY_PHASE_B.md`). Runtime proof stays TODO-S1.

### Added (previous)

- FASE A0: project scaffold — `core` (transport, exceptions, token cache), offline test harness, CI
  (test + trusted-publish workflows), governance docs.
- FASE A1: GoPay provider — `GoPayMerchant` facade with `auth` (password + OTP login, HAR-verified
  shapes), `users.me()`, `merchants.search()/detail()`; split auth/data header sets; transport-only
  retries; offline tests.
- FASE A2: `transactions.analytics()/journals()/qris_issuer_breakdown()`,
  `payouts.list()/payable_detail()` (HAR-discovered endpoints), `money.to_rupiah()`, `qris` EMVCo
  helpers (parse/inject/CRC16), `PaymentWatcher` + `watch()` factory.
- FASE A3: detailed GoPay README guide, `docs/gopay/` service pages, runnable `examples/`.
- Docs: repo logo (`assets/logo.png`) + mermaid merchant-flow diagrams in README (GoPay login, GoPay
  payment, ShopeePay roadmap).
- README: full unofficial-research disclaimer (EN + ID) — use at own risk.
- `research/RESEARCH_GOPAY_SHOPEEPAY.md`: endpoint research + anonymized HAR verification.
- FASE B1: ShopeePay provider — `ShopeePayPartner` facade (manual `B:` token) with
  `stores.list_stores()` (cursor paging + unfiltered retry), `transactions.list_recent()` (cursor
  feed, whole-rupiah normalization, store/merchant scope checks), `money.parse_id_amount()`,
  `ShopeePayWatcher` + `watch()` factory; `docs/shopee/`, `examples/06–08`, offline tests. Runtime
  verification vs a live partner account is TODO-S1 (programmatic OTP login arrives in B2).
- FASE B2: ShopeePay programmatic OTP login — `AuthService` (`request_otp()`, `verify_otp()`,
  `complete_login()`, `login_with_otp()` with the merchant-selection flow, `refresh_session()`,
  `select_merchant()`/ `select_store()`, `account_session_alive()`), stateless JSON-serializable
  challenge/verification/session dicts, `docs/shopee/auth.md` + `docs/shopee/device-risk.md`,
  `examples/09_shopee_login_otp.py`, offline tests (httpx.MockTransport). Runtime verification vs a
  live partner account is TODO-S1.
- Docs: README refresh (badges, roadmap, contributing), GitHub Discussions enabled, issue templates
  hardened (provider field, no-credentials checklist, contact links); `*-session.json` git-ignored
  so example session files can never leak.
- Docs: README split — tidy main README + per-merchant guides (`docs/gopay/README.md`,
  `docs/shopee/README.md` with flow diagrams); Telegram contact (@JoestarMojo) added.
