# Payment watcher — seed, poll, wait for nominal

Ports the `GoPayWatcher` pattern from `gobiz.js`: poll `analytics()`, remember what was seen,
surface only new transactions, block until the expected nominal (minor units!) arrives.

## API

```python
watcher = gopay.watch(merchant_id)   # poll_interval=6.0 like the references
watcher.seed()                       # mark current history seen -> count
fresh = watcher.poll_once()          # only never-seen txs (seen cache capped at 500)

paid = watcher.wait_for_payment(5_000_000, timeout=300)              # Rp50.000
paid = watcher.wait_for_payment(5_000_000, timeout=300, tolerance=100)
# -> raw tx dict; raises TimeoutError when the invoice lapses
```

Dedup keys: `transaction_id` → `id` → `order_id` → `time_gross` fallback.

## Gateway recipe

1. `inject_amount(static_qris, bill)` (+ unique code Rp1–99) → show QR.
2. `watcher.seed()` when the checkout opens.
3. `wait_for_payment(bill_minor, timeout=300)` → on success, record the `transaction_id`/`order_id`
   in YOUR database and reject replays; on `TimeoutError`, expire the invoice.

## Etiquette

Poll only while a checkout is active and keep ~6s intervals — hammering the feed is how accounts get
rate-limited. The stateless alternative (client-polled checks, like the ShopeePay reference gateway)
applies here too: no buyers, no requests.
