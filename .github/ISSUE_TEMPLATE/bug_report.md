---
name: Bug report
about: Something in the SDK behaves incorrectly
labels: bug
---

## Provider

<!-- GoPay or ShopeePay — and the method, e.g. transactions.analytics / auth.refresh_session -->

## Description

<!-- What happened, and what did you expect? -->

## Reproduction (offline, no credentials!)

```python
# Minimal snippet using a fake transport — NEVER paste tokens, passwords, PINs, or OTPs.
```

## Environment

- QrisMerchantID version:
- Python version:
- httpx version:

## Response details (sanitized)

<!-- e.http_status, e.code, and the redacted e.payload if relevant.

For ShopeePay auth: which step failed (request_otp / verify_otp / complete_login / refresh_session)?
-->

## Checklist

- [ ] I searched existing issues and discussions.
- [ ] My report contains NO credentials, tokens, or personal data.
