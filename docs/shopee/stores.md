# Stores — discover storefronts

```python
stores = sp.stores.list_stores()
# -> [{"id": "7", "name": "My Shop", "status": 1}, ...]
```

`list_stores()` walks the `lastStoreId` cursor until the batch runs short (or `storeCount` is
reached). When the `[1, 10]` service filter yields zero stores, it retries once with the filter
omitted entirely — stores without a service still show up. Guards: a non-advancing cursor and an
exhausted `max_pages` raise `QmidException` instead of looping forever.

Keep the numeric `id` — the transaction feed and the watcher are store-scoped.
