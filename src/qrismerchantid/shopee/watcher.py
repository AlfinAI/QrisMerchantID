"""Poll-based payment watcher for one ShopeePay store.

Same seed → poll → match-nominal shape as the GoPay watcher, but amounts are
WHOLE RUPIAH (ShopeePay has no minor units) and every poll is store-scoped so
one store's sales can never settle another store's invoice.
"""

from __future__ import annotations

import time
from typing import Any

from qrismerchantid.shopee.transactions import TransactionsService

_SEEN_CAP = 500


class ShopeePayWatcher:
    """Poll ``list_recent()`` and wait for an incoming payment.

    Args:
        transactions: bound :class:`TransactionsService` (shares the token).
        store_id: store to watch.
        merchant_id: forwarded as an extra scope check when known.
        poll_interval: seconds between polls (10.0 mirrors the reference
            gateway's per-checkout cadence).
        minutes: feed lookback per poll.
    """

    def __init__(
        self,
        transactions: TransactionsService,
        store_id: str | int,
        merchant_id: str | int | None = None,
        poll_interval: float = 10.0,
        minutes: int = 15,
    ) -> None:
        self._transactions = transactions
        self._store_id = store_id
        self._merchant_id = merchant_id
        self._poll_interval = poll_interval
        self._minutes = minutes
        self._seen: set[str] = set()

    @staticmethod
    def _tx_id(tx: dict[str, Any]) -> str:
        found = tx.get("id") or tx.get("order_id")
        if found:
            return str(found)
        return f"{tx.get('create_time')}_{tx.get('amount_idr')}"

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
        self, amount_idr: int, *, timeout: float = 300.0, tolerance: int = 0
    ) -> dict[str, Any]:
        """Block until a new tx of ``amount_idr`` (± ``tolerance``, rupiah) arrives.

        Only ``completed`` transactions match. Returns the normalized
        transaction dict. Raises:
            TimeoutError: nothing matching arrived within ``timeout`` seconds.
        """
        deadline = time.monotonic() + timeout
        while True:
            for tx in self.poll_once():
                amount = tx.get("amount_idr")
                if (
                    tx.get("completed") is True
                    and isinstance(amount, int)
                    and abs(amount - amount_idr) <= tolerance
                ):
                    return tx
            if time.monotonic() >= deadline:
                raise TimeoutError(f"No payment of Rp{amount_idr:,} within {timeout}s")
            time.sleep(self._poll_interval)

    def _fetch(self) -> list[dict[str, Any]]:
        body = self._transactions.list_recent(
            self._store_id, merchant_id=self._merchant_id, minutes=self._minutes
        )
        txns = body.get("transactions", [])
        return txns if isinstance(txns, list) else []
