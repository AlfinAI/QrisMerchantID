"""GoPay/GoBiz merchant provider (FASE A1: auth, users, merchants).

API knowledge: kavionn/gobiz-payment (primary), warungerik/API-GOPAY-MERCHANT,
alhifnywahid/merchantid + a live portal HAR capture (research §9).
"""

from __future__ import annotations

from qrismerchantid.core.transport import HttpTransport
from qrismerchantid.gopay import constants as C
from qrismerchantid.gopay.auth import AuthService
from qrismerchantid.gopay.client import GoPayClient
from qrismerchantid.gopay.merchants import MerchantsService
from qrismerchantid.gopay.users import UsersService


class GoPayMerchant:
    """Facade: ``auth``, ``users`` and ``merchants`` sharing one :class:`GoPayClient`.

    Args:
        access_token: reuse a cached GoID session (see ``core.token_cache``).
        transport: injectable transport (fakes in tests keep everything offline).
        timeout: seconds for the internally created httpx client.
        max_retries: transport-error retries only — HTTP errors never retry.
        backoff_base: exponential backoff base in seconds.
        app_version: ``X-AppVersion`` header; defaults to the analyzed portal.
        user_agent: ``User-Agent`` header.
    """

    def __init__(
        self,
        access_token: str | None = None,
        transport: HttpTransport | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        app_version: str = C.APP_VERSION,
        user_agent: str = C.USER_AGENT,
    ) -> None:
        self.client = GoPayClient(
            access_token,
            transport=transport,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            app_version=app_version,
            user_agent=user_agent,
        )
        self.auth = AuthService(self.client)
        self.users = UsersService(self.client)
        self.merchants = MerchantsService(self.client)


__all__ = ["GoPayMerchant"]
