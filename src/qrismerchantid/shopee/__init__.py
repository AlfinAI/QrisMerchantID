"""ShopeePay partner provider (FASE B1: manual-token stores, transactions, watcher).

API knowledge: alhifnywahid/merchantid (primary — full provider port),
ahmadzakiyox/shoppepay-api-gateway (gateway shapes, manual-token recipe).
Runtime verification against a live partner account is TODO-S1.

B1 uses a manually pasted ``B:...`` token (see ``docs/shopee/token.md``) — no
login flow yet. Programmatic OTP login arrives in B2.
"""

from __future__ import annotations

from qrismerchantid.core.transport import HttpTransport
from qrismerchantid.shopee import constants as C
from qrismerchantid.shopee.client import ShopeePayClient
from qrismerchantid.shopee.stores import StoresService
from qrismerchantid.shopee.transactions import TransactionsService
from qrismerchantid.shopee.watcher import ShopeePayWatcher


class ShopeePayPartner:
    """Facade: services sharing one :class:`ShopeePayClient`, plus a watcher factory.

    Args:
        token: manual ``B:...`` merchant token (see ``docs/shopee/token.md``).
        transport: injectable transport (fakes in tests keep everything offline).
        timeout: seconds for the internally created httpx client.
        max_retries: transport-error retries only — HTTP errors never retry.
        backoff_base: exponential backoff base in seconds.
        language/timezone: ``data.metadata`` locale.
        user_agent: ``User-Agent`` header.
    """

    def __init__(
        self,
        token: str | None = None,
        transport: HttpTransport | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        language: str = C.DEFAULT_LANGUAGE,
        timezone: str = C.DEFAULT_TIMEZONE,
        user_agent: str = C.USER_AGENT,
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


__all__ = ["ShopeePayPartner", "ShopeePayWatcher"]
