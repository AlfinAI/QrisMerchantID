"""GoBiz API constants.

Sources: live portal capture (HAR, Sep 2026 — research §9) + kavionn/gobiz-payment.
Defaults mirror a desktop-Chrome portal session (the shape ecosystem gateways use
and the user has tested); override ``app_version``/``user_agent`` on the client
if the portal moves on.
"""

from __future__ import annotations

BASE_URL = "https://api.gobiz.co.id"
ANALYTICS_BASE_URL = "https://api.gojekapi.com"
CLIENT_ID = "go-biz-web-new"
APP_ID = "go-biz-web-dashboard"
APP_VERSION = "platform-v3.122.0-72edb090"  # observed live 2026-09-19 (GOTO.har §9.4)
PORTAL_ORIGIN = "https://portal.gofoodmerchant.co.id"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
)
PHONE_MAKE = "Windows 10 64-bit"
PHONE_MODEL = "Chrome 149.0.0.0 on Windows 10 64-bit"

# Exact values the live portal sends (HAR §9.1).
DEFAULT_STATUSES = "SETTLEMENT,CAPTURE,REFUND,PARTIAL_REFUND"
DEFAULT_PAYMENT_TYPES = "QRIS,GOPAY,OFFLINE_CREDIT_CARD,OFFLINE_DEBIT_CARD,CREDIT_CARD"

# Extra headers the journals endpoint requires (HAR §9.2).
JOURNAL_HEADERS = {
    "Accept": "application/json, text/plain, */*, application/vnd.journal.v1+json",
    "X-Client-Id": "gobiz-web",
}
