# GoPay users & merchants — profile, search, detail

## `users.me()` — `GET /v1/users/me`

Portal profile of the logged-in user:

```python
me = gopay.users.me()
me["user"]  # {id, email, full_name, phone, language, merchant_id,
            #  roles: ["verified_admin"], scopes: {...60+...}, ...}
```

## `merchants.search()` — `POST /v1/merchants/search`

Body shape `{from, size}` exactly as the portal sends (NOT `{from, to, _source}` as older reference
code does — both work, we mirror the browser):

```python
found = gopay.merchants.search()              # from_=0, size=20
found = gopay.merchants.search(from_=40, size=5)
found  # {"total", "success", "hits": [{"id": "G…", "merchant_name", ...}]}
```

Doubles as the **token-validity probe**: the cheapest authenticated call, used by every reference
gateway to detect 401s.

## `merchants.detail()` — `GET /v1/merchants/{id}`

```python
detail = gopay.merchants.detail("G8277…")
# KYC, outlet (name/address/coordinates), bank, active_payment_channels,
# payment_settings (VA/retail per provider), settlement/cutoff config…
```

Merchant IDs look like `G` + 9 digits. The object is large — read the keys you need; nothing is
dropped or renamed by the SDK.
