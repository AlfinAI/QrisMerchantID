"""Exception hierarchy. Provider-agnostic; providers reuse these directly."""

from __future__ import annotations

from typing import Any


class QmidException(Exception):
    """Base exception for everything this package raises."""


class ApiException(QmidException):
    """A provider API answered with an HTTP error status.

    Attributes:
        code: machine-readable provider code (e.g. GoBiz ``errors[0]`` text or
            Shopee ``200020``), if one could be extracted.
        payload: full decoded JSON response body.
        http_status: HTTP status code.
    """

    def __init__(
        self,
        message: str,
        code: str | int | None,
        payload: dict[str, Any],
        http_status: int,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.payload = payload
        self.http_status = http_status
