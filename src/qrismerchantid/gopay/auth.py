"""GoID login flows. Request/response shapes verified against the live portal
capture (HAR, Sep 2026 — research §9), except ``login_with_password()``, which
follows kavionn/gobiz-payment and is BELUM TERVERIFIKASI live (TODO-R1)."""

from __future__ import annotations

from typing import Any

from qrismerchantid.gopay import constants as C
from qrismerchantid.gopay.client import GoPayClient


class AuthService:
    """Password + OTP login. Successful logins set the client's bearer token."""

    def __init__(self, client: GoPayClient) -> None:
        self._client = client

    def login_with_password(self, email: str, password: str) -> dict[str, Any]:
        """Log in with a GoBiz email + password.

        Returns the session (``access_token``, ``refresh_token``, ...) and sets
        it on the client. NOTE: password flow follows the reference repos; the
        HAR captured the OTP flow only (TODO-R1: verify live).
        """
        self._client.post(
            "/goid/login/request",
            {"email": email, "login_type": "password", "client_id": C.CLIENT_ID},
            auth_call=True,
        )
        session = self._client.post(
            "/goid/token",
            {
                "client_id": C.CLIENT_ID,
                "grant_type": "password",
                "data": {"email": email, "password": password},
            },
            auth_call=True,
        )
        self._client.set_access_token(str(session["access_token"]))
        return session

    def request_otp(self, phone_number: str, country_code: str = "62") -> dict[str, Any]:
        """Request an SMS OTP code (4 digits, ~12 min window per HAR).

        Returns the ``data`` object: ``otp_token`` (pass to :meth:`login_with_otp`),
        ``otp_expires_in``, ``otp_length``, ``next_state``. NOTE: the live portal
        sends NO ``login_type`` field here (research §9.2) — neither do we.
        """
        phone = phone_number.strip().replace(" ", "").replace("-", "")
        resp = self._client.post(
            "/goid/login/request",
            {"client_id": C.CLIENT_ID, "phone_number": phone, "country_code": country_code},
            auth_call=True,
        )
        data = resp.get("data")
        return data if isinstance(data, dict) else resp

    def login_with_otp(self, otp: str, otp_token: str) -> dict[str, Any]:
        """Verify the SMS code and return the session (sets it on the client)."""
        session = self._client.post(
            "/goid/token",
            {
                "client_id": C.CLIENT_ID,
                "grant_type": "otp",
                "data": {"otp": otp.strip(), "otp_token": otp_token},
            },
            auth_call=True,
        )
        self._client.set_access_token(str(session["access_token"]))
        return session
