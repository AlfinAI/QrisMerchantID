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
- Sessions carry **no server expiry** — cache with `token_cache.save/load`, probe with
  `merchants.search()`, re-login on 401.

## Errors

Wrong OTP / bad password surface as `ApiException` (HTTP 401, message from `errors[0].message`).
HTTP errors never retry — handle 401 by re-logging in.
