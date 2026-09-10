"""Poll-based payment watcher — ports the ``GoPayWatcher`` pattern from gobiz.js.

Seed the currently visible transactions, then poll for new ones; block until a
payment with the expected nominal (minor units) arrives or the timeout lapses.
"""

from __future__ import annotations

import time
from typing import Any

from qrismerchantid.gopay.transactions import TransactionsService

_SEEN_CAP = 500


class PaymentWatcher:
    """Poll ``analytics()`` and wait for an incoming payment.

    Args:
        transactions: bound :class:`TransactionsService` (shares the login).
        merchant_id: merchant to watch.
        poll_interval: seconds between polls (6.0 mirrors the references).
        days: analytics lookback per poll. ``size``: txs fetched per poll.
    """

    def __init__(
        self,
        transactions: TransactionsService,
        merchant_id: str,
        poll_interval: float = 6.0,
        days: int = 1,
        size: int = 30,
    ) -> None:
        self._transactions = transactions
        self._merchant_id = merchant_id
        self._poll_interval = poll_interval
        self._days = days
        self._size = size
        self._seen: set[str] = set()

    @staticmethod
    def _tx_id(tx: dict[str, Any]) -> str:
        found = tx.get("transaction_id") or tx.get("id") or tx.get("order_id")
        return str(found) if found else f"{tx.get('transaction_time')}_{tx.get('gross_amount')}"

    def seed(self) -> int:
        """Mark all currently visible transactions as seen. Returns the count."""
        for tx in self._fetch():
            self._seen.add(self._tx_id(tx))
        return len(self._seen)

    def poll_once(self) -> list[dict[str, Any]]:
        """Return transactions never seen before (and remember them)."""
        fresh: list[dict[str, Any]] = []
        for tx in self._fetch():
            tx_id = self._tx_id(tx)
            if tx_id in self._seen:
                continue
            self._seen.add(tx_id)
            fresh.append(tx)
        if len(self._seen) > _SEEN_CAP:
            self._seen = set(list(self._seen)[-_SEEN_CAP:])
        return fresh

    def wait_for_payment(
        self, amount_minor: int, *, timeout: float = 300.0, tolerance: int = 0
    ) -> dict[str, Any]:
        """Block until a new tx of ``amount_minor`` (± ``tolerance``) arrives.

        Returns the raw transaction dict. Raises:
            TimeoutError: nothing matching arrived within ``timeout`` seconds.
        """
        deadline = time.monotonic() + timeout
        while True:
            for tx in self.poll_once():
                gross = tx.get("gross_amount")
                if isinstance(gross, (int, float)) and abs(gross - amount_minor) <= tolerance:
                    return tx
            if time.monotonic() >= deadline:
                raise TimeoutError(f"No payment of {amount_minor} minor units within {timeout}s")
            time.sleep(self._poll_interval)

    def _fetch(self) -> list[dict[str, Any]]:
        body = self._transactions.analytics(self._merchant_id, days=self._days, size=self._size)
        txns = body.get("transactions", [])
        return txns if isinstance(txns, list) else []
