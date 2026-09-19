"""GoID login flows (OTP or email+password — the caller picks one).

Request/response shapes verified against live portal captures (HARs, Sep 2026 —
research §9): the OTP flow (§9.1) and the email/password flow (§9.5, which fully
closes TODO-R1).
"""

from __future__ import annotations

from typing import Any

from qrismerchantid.gopay import constants as C
from qrismerchantid.gopay.client import GoPayClient


class AuthService:
    """Password + OTP login. Successful logins set the client's bearer token."""

    def __init__(self, client: GoPayClient) -> None:
        self._client = client

    def login_with_password(self, email: str, password: str) -> dict[str, Any]:
        """Log in with a GoBiz email + password (alternative to the OTP flow).

        Shapes verified against the live portal (email HAR, 19 Sep 2026 —
        research §9.5; TODO-R1 fully closed). Prerequisite: the merchant account
        MUST already have an email + password set in the portal — otherwise the
        server rejects the login (the exact unset-email error shape is TODO-R3).

        Returns the session (``access_token``, ``refresh_token``, ...) and sets
        it on the client. Raises ``ValueError`` when the email is blank/malformed
        or the password is blank (local check — no API call is made).
        """
        clean_email = email.strip()
        if "@" not in clean_email or "." not in clean_email.rsplit("@", 1)[-1] or " " in clean_email:
            raise ValueError(f"Email {email!r} is not a valid merchant email")
        if not password.strip():
            raise ValueError("Password must not be blank")
        self._client.post(
            "/goid/login/request",
            {"email": clean_email, "login_type": "password", "client_id": C.CLIENT_ID},
            auth_call=True,
        )
        session = self._client.post(
            "/goid/token",
            {
                "client_id": C.CLIENT_ID,
                "grant_type": "password",
                "data": {"email": clean_email, "password": password},
            },
            auth_call=True,
        )
        self._client.set_access_token(str(session["access_token"]))
        return session

    def request_otp(self, phone_number: str, country_code: str = "62") -> dict[str, Any]:
        """Request an SMS OTP code (4 digits, ~12 min window per HAR).

        ``phone_number`` is normalized to the bare national format the live portal
        sends (``851...`` — no ``+``, no ``62``/``0`` prefix): spaces, dashes, dots
        and parentheses are stripped, then a leading ``+``, ``country_code`` or a
        single ``0`` is removed. Raises ``ValueError`` when nothing dialable
        (7+ digits) remains, instead of failing server-side.

        Returns the ``data`` object: ``otp_token`` (pass to :meth:`login_with_otp`),
        ``otp_expires_in``, ``otp_length``, ``next_state``. NOTE: the live portal
        sends NO ``login_type`` field here (research §9.2) — neither do we.
        """
        phone = (
            phone_number.strip()
            .replace(" ", "")
            .replace("-", "")
            .replace(".", "")
            .replace("(", "")
            .replace(")", "")
            .removeprefix("+")
        )
        if country_code and phone.startswith(country_code) and len(phone) > len(country_code) + 5:
            phone = phone[len(country_code) :]
        phone = phone.removeprefix("0")
        if not phone.isdigit() or len(phone) < 7:
            raise ValueError(f"Phone number {phone_number!r} is not a dialable {country_code} number")
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
