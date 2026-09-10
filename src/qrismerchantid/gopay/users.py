"""Merchant-portal user profile (``GET /v1/users/me`` — research §9.1)."""

from __future__ import annotations

from typing import Any

from qrismerchantid.gopay.client import GoPayClient


class UsersService:
    """Profile of the logged-in portal user (roles, scopes, merchant link)."""

    def __init__(self, client: GoPayClient) -> None:
        self._client = client

    def me(self) -> dict[str, Any]:
        """Return the full body: ``{"user": {id, email, full_name, phone, roles, scopes, ...}}``."""
        return self._client.get("/v1/users/me")
