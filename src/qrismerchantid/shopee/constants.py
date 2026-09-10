"""ShopeePay Partner wire constants — every value observed from the partner web clients.

Sources: ``alhifnywahid/merchantid`` v0.1.1 (``src/providers/shopee/``:
``constants.ts``, ``api.ts``, ``httpClient.ts``, ``transactionFeed.ts``,
``merchantClient.ts``) + ``ahmadzakiyox/shoppepay-api-gateway`` README (token
shape, endpoint paths). Runtime re-verification against a live partner account
is TODO-S1.
"""

from __future__ import annotations

PROVIDER_ID = "shopee"

PAY_BASE_URL = "https://shopeepay.shopee.co.id"
PARTNER_BASE_URL = "https://partner.shopee.co.id"
PARTNER_ORIGIN = "https://partner.shopee.co.id"
PARTNER_REFERER = "https://partner.shopee.co.id/"

ENDPOINT_STORES = "/merchant/v1/partner-web/get-store-list"
ENDPOINT_TRANSACTIONS = "/merchant/v1/partner-web/get-transaction-list"

# Verified caps: transaction pages larger than 10 are clamped by the client.
TRANSACTION_PAGE_SIZE = 10
STORE_PAGE_SIZE = 30
TRANSACTION_SERVICES = (1, 3)
STORE_SERVICES = (1, 10)

# The only completed status observed in the wild (merchantid + zaki gateway).
COMPLETED_STATUS = 3

# Payment-envelope codes meaning "this session is dead, renew it" (terminal —
# never retry; the caller needs a fresh ``B:`` token or a new login).
INVALID_TOKEN_CODES = frozenset({"200020", "2010000"})

DEFAULT_LANGUAGE = "id"
DEFAULT_TIMEZONE = "Asia/Jakarta"

# Desktop-browser identity the reference client presents on every call.
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0"
ACCEPT = "application/json"
ACCEPT_LANGUAGE = "id,en-US;q=0.9,en;q=0.8"
