"""GoPay/GoBiz HTTP client: split headers, retries, error mapping.

Header shapes were captured from the live merchant portal (HAR, Sep 2026 —
research §9): the full device header set goes on ``/goid/*`` auth calls only,
data calls use a slimmer set. ``X-AppVersion`` defaults to the observed live value.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any
from urllib.parse import urlencode

import httpx

from qrismerchantid.core.exceptions import ApiException
from qrismerchantid.core.transport import HttpTransport, HttpxTransport
from qrismerchantid.gopay import constants as C


class GoPayClient:
    """Low-level GoBiz client shared by all GoPay services.

    Args:
        access_token: GoID bearer token (``None`` until login).
        transport: injectable transport (fakes in tests keep everything offline).
        timeout: seconds for the internally created httpx client.
        max_retries: transport-error retries (connect/DNS/timeout) — HTTP error
            statuses are never retried.
        backoff_base: exponential backoff base in seconds (0.5s, 1s, 2s, ...).
        app_version: ``X-AppVersion`` header; follows the analyzed portal.
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
        self._transport: HttpTransport = transport or HttpxTransport(timeout=timeout)
        self._access_token = access_token
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._app_version = app_version
        self._user_agent = user_agent
        self._unique_id = str(uuid.uuid4())

    def set_access_token(self, token: str | None) -> None:
        """Set (or clear) the GoID bearer token used by subsequent calls."""
        self._access_token = token

    def auth_headers(self) -> dict[str, str]:
        """Full device header set — for ``/goid/*`` calls only (per HAR)."""
        headers = self._base_headers()
        headers.update(
            {
                "Accept-Language": "id",
                "Gojek-Country-Code": "ID",
                "Gojek-Timezone": "Asia/Jakarta",
                "X-AppVersion": self._app_version,
                "X-PhoneMake": C.PHONE_MAKE,
                "X-PhoneModel": C.PHONE_MODEL,
                "X-Platform": "Web",
                "X-User-Locale": "en-US",
                "X-User-Type": "merchant",
                "x-DeviceOS": "Web",
                "x-appId": C.APP_ID,
                "x-uniqueid": self._unique_id,
            }
        )
        return headers

    def api_headers(self) -> dict[str, str]:
        """Slim header set — for data calls (per HAR: no ``X-*`` device headers)."""
        return self._base_headers()

    def _base_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Authentication-Type": "go-id",
            "Authorization": f"Bearer {self._access_token}" if self._access_token else "Bearer",
            "Content-Type": "application/json",
            "Origin": C.PORTAL_ORIGIN,
            "Referer": C.PORTAL_ORIGIN + "/",
            "User-Agent": self._user_agent,
        }

    def request(
        self,
        method: str,
        url: str,
        body: dict[str, Any] | None = None,
        *,
        auth_call: bool = False,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a request, retrying transport errors; 2xx (incl. 201) succeeds."""
        headers = self.auth_headers() if auth_call else self.api_headers()
        if extra_headers:
            headers.update(extra_headers)
        payload = json.dumps(body) if body is not None else None
        attempt = 0
        while True:
            try:
                status, text = self._transport.request(method, url, payload, headers)
            except httpx.TransportError:
                if attempt >= self._max_retries:
                    raise
                time.sleep(self._backoff_base * (2**attempt))
                attempt += 1
                continue
            return self._handle_response(status, text)

    @staticmethod
    def _handle_response(status: int, text: str) -> dict[str, Any]:
        try:
            data = json.loads(text)
        except ValueError:
            raise ApiException(f"GoBiz answered HTTP {status} with invalid JSON", None, {}, status) from None
        if not isinstance(data, dict):
            raise ApiException(f"GoBiz answered HTTP {status} with non-object JSON", None, {}, status)
        if 200 <= status < 300:
            return data
        errors = data.get("errors")
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            message = str(errors[0].get("message", f"GoBiz HTTP {status}"))
            code = errors[0].get("code")
            code = code if isinstance(code, (str, int)) else None
        else:
            message = str(data.get("message", f"GoBiz HTTP {status}"))
            code = None
        raise ApiException(message, code, data, status)

    def get(
        self,
        path: str,
        params: dict[str, str] | None = None,
        base_url: str = C.BASE_URL,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """GET ``base_url + path`` with optional query params."""
        url = base_url + path
        if params:
            url += "?" + urlencode(params)
        return self.request("GET", url, extra_headers=extra_headers)

    def post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        *,
        auth_call: bool = False,
        base_url: str = C.BASE_URL,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """POST a JSON ``data`` body to ``base_url + path``."""
        return self.request("POST", base_url + path, data, auth_call=auth_call, extra_headers=extra_headers)

    def close(self) -> None:
        """Close the internally created httpx client (no-op for injected fakes)."""
        if isinstance(self._transport, HttpxTransport):
            self._transport.close()
