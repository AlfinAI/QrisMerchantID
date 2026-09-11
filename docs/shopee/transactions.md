# Transactions — cursor-paged, normalized feed

```python
feed = sp.transactions.list_recent(7, minutes=15)
feed = sp.transactions.list_recent(7, start_time=1784050000, end_time=1784053600)
# -> {"transactions": [...], "pages_fetched": 1, "truncated": False}
```

Each transaction is normalized:

```python
{
    "id": "264693445089687719",   # 18-digit transactionId
    "order_id": "EXT-1",          # external -> display -> transactionId fallback
    "amount_idr": 409662,         # WHOLE rupiah (see below!)
    "create_time": 1784050000,    # epoch seconds
    "create_time_iso": "2026-07-14T17:26:40.000Z",
    "store_id": "7",
    "merchant_id": "42",
    "status": 3,
    "status_name": "success",   # {1:pending, 2:failed, 3:success, 4:refunded, 5:expired}
    "completed": True,            # only status == 3 counts
    "payment_type": "shopee:1",
    "raw": {...},                 # untouched wire row
}
```

## Issuer lookup

```python
detail = sp.transactions.transaction_detail("DSP-1")  # displayTransactionId, or transactionId
# -> {"order_sn": "DSP-1", "issuer": "SeaBank", "raw": {...}}
```

Resolves the paying channel via `get-transaction-detail` (`issuer` is `None`
when the wire omits it). Enriches a feed row after a watcher match.

## Money: whole rupiah, Indonesian grouping

The wire sends amounts as grouped strings — `"409.662"` means Rp409.662 (dots
are thousand separators). `parse_id_amount()` converts them; malformed values
yield `None` and the row is skipped. **Never mix with GoPay's minor units.**

## Scope, dedup, cursors

- Rows from other stores are dropped (`merchant_id=` adds a second scope check).
- `transactionId` dedupes across pages; malformed rows are skipped, never guessed.
- `page_size` clamps to the verified 1–10 cap; a non-advancing `next_position`
  raises `QmidException`; `truncated=True` means `max_pages` ran out mid-feed.
