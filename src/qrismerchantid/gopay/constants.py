"""GoBiz API constants.

Sources: live portal capture (HAR, Sep 2026 — research §9) + kavionn/gobiz-payment.
Defaults mirror a desktop-Chrome portal session (the shape ecosystem gateways use
and the user has tested); override ``app_version``/``user_agent`` on the client
if the portal moves on.
"""

from __future__ import annotations

BASE_URL = "https://api.gobiz.co.id"
ANALYTICS_BASE_URL = "https://api.gojekapi.com"  # FASE A2: merchant-analytics
CLIENT_ID = "go-biz-web-new"
APP_ID = "go-biz-web-dashboard"
APP_VERSION = "platform-v3.119.0-eab7f749"  # observed live Sep 2026 (HAR §9.2)
PORTAL_ORIGIN = "https://portal.gofoodmerchant.co.id"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
)
PHONE_MAKE = "Windows 10 64-bit"
PHONE_MODEL = "Chrome 149.0.0.0 on Windows 10 64-bit"
