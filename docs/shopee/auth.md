# OTP login — programmatic (B2)

Three steps, mirroring the passport web client: `request_otp()` (7-call chain:
bootstrap → device-risk → migration → exists → password → settings → send) →
`verify_otp()` (code → account session → merchant list) → `complete_login()`
(SSO exchange → `B:` token → profile → stores). Or `login_with_otp()` for
verify + complete in one call.

```python
challenge = sp.auth.request_otp("0812xxxxxxx", password="...")  # WA default (ch 3)
# challenge -> {version, phone_number, channel, available_channels,
#               device_fingerprint, risk_token, has_password, cookies, requested_at}

outcome = sp.auth.login_with_otp(challenge, input("OTP: "))
# -> {"status": "complete", "session": {...}}
# ...or {"status": "merchant-selection-required", "verification", "merchants"}

session = outcome["session"]
# session -> {version, cookies, token, account_id, merchant, merchants,
#             switch_credential, stores, store_id?, profile, created_at, expires_at?}
```

Channels: 1 SMS, 2 voice, 3 WhatsApp (default), 4 email, 5 Zalo. Password is
required for password-protected accounts — without it `send_otp` reports
success but the code is silently withheld (the SDK raises instead of hanging
you out to dry). Manual-token users are unaffected: see [token.md](token.md).

## Multi-merchant picker

When several usable merchants exist and no `merchant_id` was given, the login
stops instead of guessing:

```python
outcome = sp.auth.login_with_otp(challenge, otp)
if outcome["status"] == "merchant-selection-required":
    for m in outcome["merchants"]:
        print(m["id"], m["name"], "active=" , m["is_active"])
    session = sp.auth.complete_login(outcome["verification"], merchant_id=input("ID: "))
```

The verification is reusable — no second OTP. Helpers
`usable_merchants()` / `resolve_single_merchant()` are importable from
`qrismerchantid.shopee.auth` for your own pickers.

## Session persistence + renewal

Challenge, verification, and session are plain JSON dicts — persist them with
`json.dump` (NOT `token_cache`, which expects GoPay-shaped sessions):

```python
import json

json.dump(session, open(".shopee-session.json", "w"))
...
session = json.load(open(".shopee-session.json"))
if not sp.auth.account_session_alive(session):
    session = fresh_login_again()          # only a new OTP recovers from here
else:
    session = sp.auth.refresh_session(session)  # re-mints the token, no OTP
    json.dump(session, open(".shopee-session.json", "w"))  # persist AGAIN (it rotated!)
sp.set_token(session["token"])
```

`refresh_session()` / `select_merchant()` replay the SSO exchange
(`login_toc` → `tob/auth`) using the `switch_credential` — never the
headless-rejected `SwitchMerchant` endpoint. Liveness comes ONLY from
`login_status`: the JWT `exp` (~1000 days) says nothing about the server-side
session. `select_store(session, id)` is pure (no network) and just re-points.

## Errors

| Failure | Exception |
|---|---|
| Bad phone / OTP shape / unknown ids / version mismatch | `ValueError` |
| Dead account session on refresh (`48500102`) | `ApiException` (only a fresh OTP recovers) |
| Dead token on feeds (`200020`/`2010000`) | `ApiException` (refresh or re-login) |
| Captcha demanded | `ApiException` (`captcha…` — solve in a browser, retry) |
| No renewal credential / missing JWT / contract violation | `QmidException` |

## Security

Challenge, verification, and session objects embed cookies — treat them like
passwords: never log, never commit, `chmod 600` the session file.
