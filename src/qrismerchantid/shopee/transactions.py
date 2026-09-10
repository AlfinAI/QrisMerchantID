"""Transaction feed: cursor-paged ``get-transaction-list`` + normalization.

Ports ``ShopeeTransactionFeed.listRecent`` (merchantid ``transactionFeed.ts``):
epoch-second filters, ``[1, 3]`` services, ``createTime`` descending sort, and
``next_position`` cursoring with a non-advance guard. Rows are normalized to a
stable shape — the wire's Indonesian grouped amounts (``"409.662"``) become
whole-rupiah ints (see :mod:`shopee.money`), and only ``status == 3`` counts
as completed (the sole completed status observed).
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any

from qrismerchantid.core.exceptions import QmidException
from qrismerchantid.shopee import constants as C
from qrismerchantid.shopee.client import ShopeePayClient
from qrismerchantid.shopee.money import parse_id_amount


class TransactionsService:
    """Read-only mutasi for one store (scope-checked, deduped, normalized)."""

    def __init__(self, client: ShopeePayClient) -> None:
        self._client = client

    def list_recent(
        self,
        store_id: str | int,
        *,
        merchant_id: str | int | None = None,
        minutes: int = 15,
        start_time: int | None = None,
        end_time: int | None = None,
        page_size: int = C.TRANSACTION_PAGE_SIZE,
        max_pages: int = 20,
    ) -> dict[str, Any]:
        """Fetch recent transactions for ``store_id``.

        Args:
            store_id: store to scope to (rows from other stores are dropped).
            merchant_id: also enforce the merchant scope when known (B1 has no
                profile call yet, so this stays optional until B2).
            minutes: lookback window when ``start_time``/``end_time`` are
                omitted (epoch seconds, server style).
            start_time/end_time: explicit epoch-second range (overrides
                ``minutes``). Reversed ranges raise :class:`ValueError`.
            page_size: rows per page (clamped to 1–10, the verified cap).
            max_pages: page-fetch ceiling.

        Returns ``{"transactions", "pages_fetched", "truncated"}``. Each
        transaction is ``{id, order_id, amount_idr, create_time, create_time_iso,
        store_id, merchant_id, status, completed, payment_type, raw}``.
        Malformed or out-of-scope rows are skipped, never guessed.
        """
        end = end_time if end_time is not None else int(time.time())
        start = start_time if start_time is not None else end - minutes * 60
        if start > end:
            raise ValueError("Shopee transaction time range is invalid")
        size = min(C.TRANSACTION_PAGE_SIZE, max(1, page_size))
        pages = max(1, max_pages)
        want_store = str(store_id)
        want_merchant = str(merchant_id) if merchant_id is not None else None

        transactions: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        cursors: set[str] = set()
        next_position = ""
        pages_fetched = 0
        for _ in range(pages):
            data = self._client.post_payment(
                C.ENDPOINT_TRANSACTIONS,
                {
                    "pageSize": size,
                    "filter": {
                        "startTime": start,
                        "endTime": end,
                        "serviceList": list(C.TRANSACTION_SERVICES),
                    },
                    "sorter": {"field": "createTime", "order": "descend"},
                    "next_position": next_position,
                },
            )
            pages_fetched += 1
            raw_list = data.get("list", [])
            for raw in raw_list if isinstance(raw_list, list) else []:
                tx = _normalize(raw, want_store, want_merchant)
                if tx is None or tx["id"] in seen_ids:
                    continue
                seen_ids.add(tx["id"])
                transactions.append(tx)
            cursor = data.get("next_position") or ""
            cursor = cursor if isinstance(cursor, str) else ""
            if not cursor:
                return {"transactions": transactions, "pages_fetched": pages_fetched, "truncated": False}
            if cursor == next_position or cursor in cursors:
                raise QmidException("Shopee transaction cursor did not advance")
            cursors.add(cursor)
            next_position = cursor
        return {
            "transactions": transactions,
            "pages_fetched": pages_fetched,
            "truncated": bool(next_position),
        }


def _normalize(raw: Any, want_store: str, want_merchant: str | None) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    tx_id = raw.get("transactionId")
    tx_id = tx_id.strip() if isinstance(tx_id, str) else ""
    amount_raw = raw.get("amount")
    amount = parse_id_amount(amount_raw) if isinstance(amount_raw, str) else None
    created = raw.get("createTime")
    moment = (
        created
        if isinstance(created, (int, float)) and not isinstance(created, bool) and math.isfinite(created)
        else None
    )
    if not tx_id or amount is None or moment is None:
        return None
    try:
        iso = datetime.fromtimestamp(int(moment), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except (OverflowError, OSError, ValueError):
        return None
    if str(raw.get("storeId")) != want_store:
        return None
    merchant = str(raw.get("merchantId"))
    if want_merchant is not None and merchant != want_merchant:
        return None
    status = raw.get("status")
    status = status if isinstance(status, int) and not isinstance(status, bool) else -1
    completed = status == C.COMPLETED_STATUS
    service = raw.get("service", raw.get("transactionType", "unknown"))
    order_id = raw.get("externalTransactionId") or raw.get("displayTransactionId") or tx_id
    return {
        "id": tx_id,
        "order_id": str(order_id),
        "amount_idr": amount,
        "create_time": int(moment),
        "create_time_iso": iso,
        "store_id": want_store,
        "merchant_id": merchant,
        "status": status,
        "completed": completed,
        "payment_type": f"shopee:{service}",
        "raw": raw,
    }
