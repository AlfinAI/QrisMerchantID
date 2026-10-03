"""GoBiz API constants.

Sources: live portal capture (HAR, Sep 2026 — research §9),
the public GoFood Merchant portal bootstrap, and kavionn/gobiz-payment.
Defaults mirror a desktop-Chrome portal session. Override ``app_version`` /
``user_agent`` on the client, or set ``QRISMERCHANTID_GOPAY_APP_VERSION``,
when the portal moves on.
"""

from __future__ import annotations

BASE_URL = "https://api.gobiz.co.id"
# The 2026-10-03 browser HAR sends GoID auth to the portal host, while
# merchant/data APIs remain on api.gobiz.co.id.
AUTH_BASE_URL = "https://portal.gofoodmerchant.co.id"
ANALYTICS_BASE_URL = "https://api.gojekapi.com"
CLIENT_ID = "go-biz-web-new"
APP_ID = "go-biz-web-dashboard"
# Current portal build discovered from the public GoFood Merchant portal bootstrap.
# Override with QRISMERCHANTID_GOPAY_APP_VERSION when GoBiz rolls the build again.
APP_VERSION = "platform-v3.125.0-e1923971"  # portal build observed 2026-10-03

PORTAL_ORIGIN = "https://portal.gofoodmerchant.co.id"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/148.0.0.0 Safari/537.36"
)
PHONE_MAKE = "Windows 10 64-bit"
PHONE_MODEL = "Chrome 148.0.0.0 on Windows 10 64-bit"

# Exact values the live portal sends (HAR §9.1).
DEFAULT_STATUSES = "SETTLEMENT,CAPTURE,REFUND,PARTIAL_REFUND"
DEFAULT_PAYMENT_TYPES = "QRIS,GOPAY,OFFLINE_CREDIT_CARD,OFFLINE_DEBIT_CARD,CREDIT_CARD"

# Extra headers the journals endpoint requires (HAR §9.2).
JOURNAL_HEADERS = {
    "Accept": "application/json, text/plain, */*, application/vnd.journal.v1+json",
    "X-Client-Id": "gobiz-web",
}
