"""GoPay/GoBiz merchant provider (FASE A1–A2: auth, users, merchants, transactions,
payouts, QRIS helpers, payment watcher).

API knowledge: kavionn/gobiz-payment (primary), warungerik/API-GOPAY-MERCHANT,
alhifnywahid/merchantid + a live portal HAR capture (research §9).
"""

from __future__ import annotations

from qrismerchantid.core.transport import HttpTransport
from qrismerchantid.gopay import constants as C
from qrismerchantid.gopay.auth import AuthService
from qrismerchantid.gopay.client import GoPayClient
from qrismerchantid.gopay.merchants import MerchantsService
from qrismerchantid.gopay.payouts import PayoutsService
from qrismerchantid.gopay.transactions import TransactionsService
from qrismerchantid.gopay.users import UsersService
from qrismerchantid.gopay.watcher import PaymentWatcher


class GoPayMerchant:
    """Facade: services sharing one :class:`GoPayClient`, plus a watcher factory.

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
        refresh_token: str | None = None,
        transport: HttpTransport | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        app_version: str = C.APP_VERSION,
        user_agent: str = C.USER_AGENT,
    ) -> None:
        self.client = GoPayClient(
            access_token,
            refresh_token=refresh_token,
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
        self.transactions = TransactionsService(self.client)
        self.payouts = PayoutsService(self.client)

    def watch(self, merchant_id: str, poll_interval: float = 6.0) -> PaymentWatcher:
        """Create a :class:`PaymentWatcher` bound to this instance's login."""
        return PaymentWatcher(self.transactions, merchant_id, poll_interval=poll_interval)


__all__ = ["GoPayMerchant", "PaymentWatcher"]
