"""HTTP transport abstraction (one dependency: httpx)."""

from __future__ import annotations

from typing import Protocol

import httpx


class HttpTransport(Protocol):
    """Minimal transport. Inject a fake in tests to stay offline."""

    def request(self, method: str, url: str, body: str | None, headers: dict[str, str]) -> tuple[int, str]:
        """Send a request. Returns ``(http_status, response_body_text)``."""
        ...


class HttpxTransport:
    """Default :class:`HttpTransport` backed by ``httpx``.

    Args:
        client: optional pre-configured ``httpx.Client`` (e.g. ``http2=True``,
            custom proxy/verify). When omitted, one is created with ``timeout``.
        timeout: default timeout (seconds) for the internally created client.

    Transport-level failures (connect errors, timeouts) propagate as
    ``httpx.TransportError`` so provider clients can retry them.
    """

    def __init__(self, client: httpx.Client | None = None, timeout: float = 30.0) -> None:
        self._client = client or httpx.Client(timeout=timeout)
        self._owns_client = client is None

    def request(self, method: str, url: str, body: str | None, headers: dict[str, str]) -> tuple[int, str]:
        response = self._client.request(method, url, content=body, headers=headers)
        return response.status_code, response.text

    def close(self) -> None:
        """Close the internally created client (no-op for user-supplied clients)."""
        if self._owns_client:
            self._client.close()
