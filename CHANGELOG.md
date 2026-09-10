# Changelog

## [Unreleased]

### Added
- FASE A0: project scaffold — `core` (transport, exceptions, token cache),
  offline test harness, CI (test + trusted-publish workflows), governance docs.
- FASE A1: GoPay provider — `GoPayMerchant` facade with `auth` (password + OTP
  login, HAR-verified shapes), `users.me()`, `merchants.search()/detail()`;
  split auth/data header sets; transport-only retries; offline tests.
- README: full unofficial-research disclaimer (EN + ID) — use at own risk.
- `research/RESEARCH_GOPAY_SHOPEEPAY.md`: endpoint research + anonymized HAR verification.
