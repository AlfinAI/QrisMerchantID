"""ShopeePay Partner wire constants — every value observed from the partner web clients.

Sources: ``alhifnywahid/merchantid`` v0.1.1 (``src/providers/shopee/``:
``constants.ts``, ``api.ts``, ``httpClient.ts``, ``transactionFeed.ts``,
``merchantClient.ts``) + ``ahmadzakiyox/shoppepay-api-gateway`` README +
deobfuscated ``server.js`` (token shape, endpoint paths, status map, issuer
detail shape). Runtime re-verification against a live partner account
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
ENDPOINT_TRANSACTION_DETAIL = "/merchant/v1/partner-web/get-transaction-detail"

# Verified caps: transaction pages larger than 10 are clamped by the client.
TRANSACTION_PAGE_SIZE = 10
STORE_PAGE_SIZE = 30
TRANSACTION_SERVICES = (1, 3)
STORE_SERVICES = (1, 10)

# The only completed status observed in the wild (merchantid + zaki gateway).
COMPLETED_STATUS = 3
# Full status map from the deobfuscated `server.js` `f` display functions
# (pending/failed/success/refunded/expired) — needs live re-verification (TODO-S1).
STATUS_NAMES = {1: "pending", 2: "failed", 3: "success", 4: "refunded", 5: "expired"}

# Payment-envelope codes meaning "this session is dead, renew it" (terminal —
# never retry; the caller needs a fresh ``B:`` token or a new login).
INVALID_TOKEN_CODES = frozenset({"200020", "2010000"})

DEFAULT_LANGUAGE = "id"
DEFAULT_TIMEZONE = "Asia/Jakarta"

# Desktop-browser identity the reference client presents on every call.
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0"
ACCEPT = "application/json"
ACCEPT_LANGUAGE = "id,en-US;q=0.9,en;q=0.8"

# --- B2: programmatic OTP login (authClient.ts / shopeeProvider.ts) ---

ACCOUNT_BASE_URL = "https://partner.business.accounts.shopee.co.id"
PARTNER_API_BASE_URL = "https://api.partner.shopee.co.id"
DEVICE_FINGERPRINT_REPORT_URL = "https://df.infra.sz.shopee.co.id/v2/shpsec/web/report"
SZ_SDK_VERSION = "1.12.26-user.1"

ACCOUNT_CLIENT_ID = "5"
BUSINESS_CLIENT_ID = "1"
PARTNER_LOGIN_FROM = "12"

ENDPOINT_CHECK_PASSWORD_MIGRATE = "/api/v4/account/business/check_password_migrate"
ENDPOINT_CHECK_ACCOUNT_EXISTS = "/api/v4/account/business/check_account_exist_by_password"
ENDPOINT_AUTHENTICATE_BY_PASSWORD = "/api/v4/account/business/authenticate_toc_by_password"
ENDPOINT_OTP_SETTINGS = "/api/v4/account/business/get_otp_settings"
ENDPOINT_SEND_OTP = "/api/v4/account/business/send_otp"
ENDPOINT_VERIFY_OTP = "/api/v4/account/business/verify_otp"
ENDPOINT_AUTHENTICATE_BY_OTP = "/api/v4/account/business/authenticate_toc_by_otp"
ENDPOINT_LOGIN_TOC = "/api/v4/account/business/login_toc"
ENDPOINT_LOGIN_STATUS = "/api/v4/account/business/login_status"
ENDPOINT_MERCHANT_DETECT = "/nb/mss/mer-detect-api/PartnerMerchantDetectServer/MerchantDetect"
ENDPOINT_USER_INFO = "/nb/mss/web-api/PartnerAccountServer/GetUserInfo"
ENDPOINT_ACCOUNT_LOGIN = "/account/login/auth"
ENDPOINT_ACCOUNT_LOGIN_TOKEN = "/authenticate/login/token/"
ENDPOINT_ACCOUNT_TOB_AUTH = "/account/login/tob/auth"
ENDPOINT_PARTNER_LOGIN_AUTH = "/login/auth"
ENDPOINT_AUTHENTICATE_LOGIN = "/authenticate/login/"

OTP_OPERATION = 50001
OTP_CHANNELS = (1, 2, 3, 5)  # SMS, voice, WhatsApp, Zalo
SEND_OTP_CHANNELS = (1, 2, 3, 5, 4)  # ... + email
DEFAULT_OTP_CHANNEL = 3  # WhatsApp (reference capture default)

NEED_OTP_CODE = 48401102  # password accepted — OTP second factor required
NOT_LOGIN_CODE = 48500102  # account session dead — fresh OTP required

LIVE_TOKEN_COOKIE = "__shopee_partner_website_x_token_live"
CLIENT_ID_COOKIE = "SPC_CLIENTID"
CSRF_COOKIE = "csrftoken"
