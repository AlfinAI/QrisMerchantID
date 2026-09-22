"""Merchant search + detail (research §9.1/§9.3). ``search()`` doubles as a cheap
token-validity probe: it is the call every reference gateway uses to detect 401s."""

from __future__ import annotations

from typing import Any

from qrismerchantid.gopay.client import GoPayClient


class MerchantsService:
    """Merchant discovery (list) and full detail (KYC/outlet/bank/payment settings)."""

    def __init__(self, client: GoPayClient) -> None:
        self._client = client

    def search(self, from_: int = 0, size: int = 20) -> dict[str, Any]:
        """POST ``/v1/merchants/search`` — body shape ``{from, size}`` per live HAR.

        Returns ``{"total", "success", "hits": [...]}``.
        """
        return self._client.post("/v1/merchants/search", {"from": from_, "size": size})

    def detail(self, merchant_id: str) -> dict[str, Any]:
        """GET ``/v1/merchants/{id}`` — full merchant object (IDs look like ``G…``)."""
        return self._client.get(f"/v1/merchants/{merchant_id}")
