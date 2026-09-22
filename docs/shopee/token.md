# ShopeePay token — paste a manual `B:...` token (B1)

B1 has no login flow yet (programmatic OTP arrives in B2), so you paste the merchant token from your
own logged-in partner portal session — the same recipe the `shoppepay-api-gateway` reference uses.

## Grab the token (2 minutes, your browser)

1. Log in to `https://partner.shopee.co.id` as usual.
2. Open DevTools → Network tab.
3. Open the ShopeePay transaction history page (fires `get-transaction-list`).
4. Click that request → Request Payload → `data` → `metadata` → `token`.
5. Copy the value (starts with `B:`).
```python
from qrismerchantid import ShopeePayPartner

sp = ShopeePayPartner(token="B:paste-yours-here")
print(sp.stores.list_stores())
```

## Rules

- The token lives in YOUR `.env` (`SHOPEE_TOKEN=...`) — it is only ever sent to Shopee's own
  servers. Never commit it.
- Tokens rotate when the portal session refreshes: when calls start failing with `200020`/`2010000`
  ("Shopee rejected the saved session"), paste a fresh one. B2 will automate renewal.
- Multi-store: each storefront session has its own token — construct one `ShopeePayPartner` per
  token.

Prefer zero copy-paste? Log in programmatically instead — [auth.md](auth.md).
