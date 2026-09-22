"""ShopeePay Partner HTTP client: payment envelope, retries, error mapping.

B1 covers the payment envelope (``{code, msg, data}``) used by the store and
transaction feeds: the ``B:`` token travels in the body
(``data.metadata.token``) while the ``X-Token`` header stays intentionally
empty — exactly as the partner web client does (merchantid ``api.ts``). The
partner envelope (``GetUserInfo`` profile) arrives with the B2 login flow.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

from qrismerchantid.core.exceptions import ApiException, QmidException
from qrismerchantid.core.transport import HttpTransport, HttpxTransport
from qrismerchantid.shopee import constants as C

_AUTH_WORDS = re.compile(r"token|auth|login|session", re.IGNORECASE)


class ShopeePayClient:
    """Low-level ShopeePay client shared by all ShopeePay services.

    Args:
        token: manual ``B:...`` merchant token (see ``docs/shopee/token.md``).
            ``None`` until set — calls without one raise :class:`QmidException`.
        transport: injectable transport (fakes in tests keep everything offline).
        timeout: seconds for the internally created httpx client.
        max_retries: transport-error retries (connect/DNS/timeout) — HTTP error
            statuses are never retried.
        backoff_base: exponential backoff base in seconds (0.5s, 1s, 2s, ...).
        language/timezone: ``data.metadata`` locale; defaults follow the
            reference web client.
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
        self._transport: HttpTransport = transport or HttpxTransport(timeout=timeout)
        self._token = token
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._language = language
        self._timezone = timezone
        self._user_agent = user_agent

    def set_token(self, token: str | None) -> None:
        """Set (or clear) the ``B:...`` token used by subsequent calls."""
        self._token = token

    def payment_headers(self) -> dict[str, str]:
        """Headers the partner web client sends on payment-envelope calls."""
        return {
            "Accept": C.ACCEPT,
            "Accept-Language": C.ACCEPT_LANGUAGE,
            "Content-Type": "application/json",
            "Origin": C.PARTNER_ORIGIN,
            "Referer": C.PARTNER_REFERER,
            "User-Agent": self._user_agent,
            "X-Timestamp-Ms": str(int(time.time() * 1000)),
            "X-Token": "",
        }

    def payment_metadata(self) -> dict[str, str]:
        """``data.metadata`` for payment-envelope bodies (carries the token)."""
        if not self._token:
            raise QmidException("No ShopeePay token set — pass token='B:...' (see docs/shopee/token.md).")
        return {"token": self._token, "language": self._language, "timezone": self._timezone}

    def post_payment(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST ``{data: {metadata, ...data}}``; return the unwrapped ``data``.

        Raises:
            ApiException: the envelope answered ``code != 0`` (invalid-token
                codes ``200020``/``2010000`` mean the session is dead — renew
                the token, don't retry) or HTTP signalled an error.
        """
        body = {"data": {"metadata": self.payment_metadata(), **data}}
        payload = json.dumps(body)
        headers = self.payment_headers()
        url = C.PAY_BASE_URL + path
        attempt = 0
        while True:
            try:
                status, text = self._transport.request("POST", url, payload, headers)
            except httpx.TransportError:
                if attempt >= self._max_retries:
                    raise
                time.sleep(self._backoff_base * (2**attempt))
                attempt += 1
                continue
            return self._handle_response(status, text, path)

    @staticmethod
    def _handle_response(status: int, text: str, endpoint: str) -> dict[str, Any]:
        try:
            body = json.loads(text)
        except ValueError:
            raise ApiException(
                f"ShopeePay {endpoint} answered HTTP {status} with invalid JSON", None, {}, status
            ) from None
        if not isinstance(body, dict):
            raise ApiException(
                f"ShopeePay {endpoint} answered HTTP {status} with non-object JSON", None, {}, status
            )
        code_raw = body.get("code")
        code = str(code_raw) if code_raw is not None else None
        reason = str(body.get("msg", "")) or f"HTTP {status}"
        if 200 <= status < 300 and code_raw in (0, "0") and body.get("data") is not None:
            data = body["data"]
            if not isinstance(data, dict):
                raise ApiException(f"ShopeePay {endpoint} answered with non-object data", code, body, status)
            return data
        message = f"ShopeePay {endpoint} failed (error {code}): {reason}"
        if (code is not None and code in C.INVALID_TOKEN_CODES) or _AUTH_WORDS.search(reason):
            message = (
                f"Shopee rejected the saved session on {endpoint} (error {code}); "
                "paste a fresh B: token — retrying the dead one never helps"
            )
        raise ApiException(message, code, body, status)

    def close(self) -> None:
        """Close the internally created httpx client (no-op for injected fakes)."""
        if isinstance(self._transport, HttpxTransport):
            self._transport.close()
