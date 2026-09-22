"""Payout history + payable balance (HAR-discovered endpoints, research §9.3 —
absent from every reference repo). Amounts are decimal strings in minor units.
"""

from __future__ import annotations

from typing import Any

from qrismerchantid.gopay.client import GoPayClient


class PayoutsService:
    """Read-only settlement: payout list and current payable detail."""

    def __init__(self, client: GoPayClient) -> None:
        self._client = client

    def list(self, page: int = 1, per: int = 10) -> dict[str, Any]:
        """GET ``/v1/merchants/payouts`` — ``{"payouts": [...], "current_page", "per", "next_page"}``."""
        return self._client.get("/v1/merchants/payouts", {"page": str(page), "per": str(per)})

    def payable_detail(self, merchant_id: str) -> dict[str, Any]:
        """GET ``/v1/merchants/payouts/payable_detail`` — ``{"payable_detail": {...}}``."""
        return self._client.get("/v1/merchants/payouts/payable_detail", {"merchant_id": merchant_id})
