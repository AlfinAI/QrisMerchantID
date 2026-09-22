# GoPay auth — GoID login (password + OTP)

Source of truth: live portal HAR (Sep 2026, research §9). Both login endpoints answer **HTTP 201**
and require the full device header set (handled by the client).

## Endpoints

| Call                                  | Request body                                                                    | Response                                                                                   |
| ------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `POST /goid/login/request` (OTP)      | `{client_id, phone_number, country_code}` — NO `login_type` (portal sends none) | `{data: {otp_token, otp_expires_in: 720, otp_length: 4, next_state}, success, errors: []}` |
| `POST /goid/token` (OTP)              | `{client_id, grant_type: "otp", data: {otp, otp_token}}`                        | `{access_token, refresh_token, dbl_enabled}`                                               |
| `POST /goid/login/request` (password) | `{email, login_type: "password", client_id}`                                    | 201 `{data: {}, success, errors: []}` ✅ verified live (§9.5)                               |
| `POST /goid/token` (password)         | `{client_id, grant_type: "password", data: {email, password}}`                  | session, same shape                                                                        |

## SDK

```python
# Unified: pick method="otp" (2 steps) or method="email" (1 step)
otp = gopay.auth.login(method="otp", phone_number="0812xxxxxxx")
session = gopay.auth.login(method="otp", otp=code, otp_token=otp["otp_token"])
session = gopay.auth.login(method="email", email=email, password=password)

# Granular (same steps, individual calls):
otp = gopay.auth.request_otp("0812xxxxxxx")          # -> data object (not full body)
session = gopay.auth.login_with_otp(code, otp["otp_token"])
session = gopay.auth.login_with_password(email, password)
```

- Success sets the bearer token on the shared client automatically.
- Either flow works — pick OTP (no password stored) or email+password (needs both set in the portal;
  unset-email error shape is TODO-R3).
- Phone input is normalized to bare national format (`0812…`/`+62812…` → `812…`, `country_code="62"`
  default); garbage raises `ValueError` before any API call.
- OTP is 4 digits via SMS with a ~12 min window; keep `otp_token` server-side (or
  `token_cache.save_pending_otp()`) between the two calls.
- Sessions carry server-side expiry. Persist both `access_token` and `refresh_token` with
  `token_cache.save/load`. The client automatically refreshes once on an expired-token
  response when a refresh token is configured; `gopay.auth.refresh_session()` is also
  available for an explicit refresh. The portal HAR verifies `POST /goid/token` with
  `grant_type: "refresh_token"` and `data.refresh_token`. Persist the returned session
  because the refresh token rotates.
- A cached session must be passed as both tokens:
  `GoPayMerchant(access_token=session["access_token"], refresh_token=session["refresh_token"])`.
- If refresh fails because the refresh token is revoked or expired, stop polling and perform a fresh login.
  The refresh flow is intended to prevent unnecessary logout/login cycles; it cannot keep an account
  permanently connected after GoBiz revokes the session. The provider's account-suspension policy,
  including whether repeated login alone causes suspension, is **BELUM TERVERIFIKASI**.

## Errors

Wrong OTP / bad password surface as `ApiException` (HTTP 401, message from `errors[0].message`).
HTTP errors never retry — handle 401 by re-logging in.
