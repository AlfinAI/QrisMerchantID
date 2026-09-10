"""Store discovery: cursor-paged ``get-store-list`` with an unfiltered retry.

Ports ``ShopeeMerchantClient.listStores`` (merchantid ``merchantClient.ts``):
page with the ``[1, 10]`` service filter first, and when that yields zero
stores retry with the filter key omitted entirely (not an empty array) so
stores without a service still show up.
"""

from __future__ import annotations

from typing import Any

from qrismerchantid.core.exceptions import QmidException
from qrismerchantid.shopee import constants as C
from qrismerchantid.shopee.client import ShopeePayClient


class StoresService:
    """List the merchant's stores (each has the numeric ``id`` the feed needs)."""

    def __init__(self, client: ShopeePayClient) -> None:
        self._client = client

    def list_stores(self, *, max_pages: int = 10) -> list[dict[str, Any]]:
        """Return ``[{id, name, status}, ...]`` across all pages.

        Args:
            max_pages: page-fetch ceiling (exhausting it raises
                :class:`QmidException` instead of looping forever).
        """
        stores = self._fetch(max_pages, list(C.STORE_SERVICES))
        if stores:
            return stores
        return self._fetch(max_pages, None)

    def _fetch(self, max_pages: int, service_list: list[int] | None) -> list[dict[str, Any]]:
        pages = max(1, max_pages)
        stores: dict[str, dict[str, Any]] = {}
        seen_cursors = {0}
        last_store_id = 0
        for _ in range(pages):
            inner: dict[str, Any] = {
                "storeName": "",
                "lastStoreId": last_store_id,
                "pageSize": C.STORE_PAGE_SIZE,
            }
            if service_list is not None:
                inner["serviceList"] = service_list
            data = self._client.post_payment(C.ENDPOINT_STORES, inner)
            raw_batch = data.get("list", [])
            batch = raw_batch if isinstance(raw_batch, list) else []
            for raw in batch:
                store = _normalize_store(raw)
                if store is not None:
                    stores[store["id"]] = store
            total = data.get("storeCount")
            total_reached = isinstance(total, int) and total >= 0 and len(stores) >= total
            if not batch or len(batch) < C.STORE_PAGE_SIZE or total_reached:
                return list(stores.values())
            next_cursor = _cursor_of(batch[-1])
            if next_cursor is None or next_cursor in seen_cursors:
                raise QmidException("Shopee store cursor did not advance")
            seen_cursors.add(next_cursor)
            last_store_id = next_cursor
        raise QmidException("Shopee store pagination limit was reached")


def _normalize_store(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    store_id = raw.get("storeId")
    if isinstance(store_id, bool) or not isinstance(store_id, (int, str)) or str(store_id) == "":
        return None
    status = raw.get("status")
    return {
        "id": str(store_id),
        "name": str(raw.get("storeName", "")),
        "status": status if isinstance(status, int) and not isinstance(status, bool) else 0,
    }


def _cursor_of(raw: Any) -> int | None:
    if not isinstance(raw, dict):
        return None
    value = raw.get("storeId")
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None
