"""ShopeePay partner provider (FASE B1: manual-token stores, transactions, watcher).

API knowledge: alhifnywahid/merchantid (primary — full provider port),
ahmadzakiyox/shoppepay-api-gateway (gateway shapes, manual-token recipe).
Runtime verification against a live partner account is TODO-S1.

B1 uses a manually pasted ``B:...`` token (see ``docs/shopee/token.md``); B2 adds
programmatic OTP login (see ``docs/shopee/auth.md``) — use whichever fits.
"""

from __future__ import annotations

import httpx

from qrismerchantid.core.transport import HttpTransport
from qrismerchantid.shopee import constants as C
from qrismerchantid.shopee.auth import AuthService
from qrismerchantid.shopee.client import ShopeePayClient
from qrismerchantid.shopee.stores import StoresService
from qrismerchantid.shopee.transactions import TransactionsService
from qrismerchantid.shopee.watcher import ShopeePayWatcher


class ShopeePayPartner:
    """Facade: services sharing one :class:`ShopeePayClient`, plus auth + watcher.

    Args:
        token: manual ``B:...`` merchant token (see ``docs/shopee/token.md``).
            Ignored once :meth:`auth` logs in (login mints its own token).
        transport: injectable transport (fakes in tests keep everything offline).
        auth_transport: optional ``httpx.BaseTransport`` the login flow runs
            on (pass ``httpx.MockTransport`` in tests to stay offline).
        timeout: seconds for the internally created httpx clients.
        max_retries: transport-error retries only — HTTP errors never retry.
        backoff_base: exponential backoff base in seconds.
        language/timezone: locale for metadata + account/partner calls.
        user_agent: ``User-Agent`` header.
        device_report: default fraud-SDK telemetry blob for OTP delivery (see
            ``docs/shopee/device-risk.md``).
    """

    def __init__(
        self,
        token: str | None = None,
        transport: HttpTransport | None = None,
        auth_transport: httpx.BaseTransport | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        language: str = C.DEFAULT_LANGUAGE,
        timezone: str = C.DEFAULT_TIMEZONE,
        user_agent: str = C.USER_AGENT,
        device_report: str | None = None,
    ) -> None:
        self.client = ShopeePayClient(
            token,
            transport=transport,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            language=language,
            timezone=timezone,
            user_agent=user_agent,
        )
        self.stores = StoresService(self.client)
        self.transactions = TransactionsService(self.client)
        self.auth = AuthService(
            transport=auth_transport,
            data_client=self.client,
            timeout=timeout,
            max_retries=max_retries,
            backoff_base=backoff_base,
            language=language,
            timezone=timezone,
            user_agent=user_agent,
            device_report=device_report,
        )

    def set_token(self, token: str | None) -> None:
        """Set (or clear) the ``B:...`` token used by subsequent calls."""
        self.client.set_token(token)

    def watch(
        self,
        store_id: str | int,
        merchant_id: str | int | None = None,
        poll_interval: float = 10.0,
    ) -> ShopeePayWatcher:
        """Create a :class:`ShopeePayWatcher` bound to this instance's token."""
        return ShopeePayWatcher(
            self.transactions, store_id, merchant_id=merchant_id, poll_interval=poll_interval
        )

    def close(self) -> None:
        """Close the internally created httpx clients (no-op for injected fakes)."""
        self.client.close()
        self.auth.close()


__all__ = ["AuthService", "ShopeePayPartner", "ShopeePayWatcher"]
