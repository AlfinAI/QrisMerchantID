# Payment watcher — seed, poll, wait for nominal (whole rupiah!)

```python
watcher = sp.watch(7)   # store_id; poll_interval=10.0 like the reference gateway
watcher.seed()          # mark current history seen -> count
fresh = watcher.poll_once()  # only never-seen txs (seen cache capped at 500)

paid = watcher.wait_for_payment(409662, timeout=300)              # Rp409.662
paid = watcher.wait_for_payment(409662, timeout=300, tolerance=100)
# -> normalized tx dict (completed only); raises TimeoutError on lapse
```

Dedup keys: `id` → `order_id` → `time_amount` fallback. Only `completed` transactions match —
pending rows never settle an invoice.

## Gateway recipe

1. `qris.inject_amount(static_qris, bill)` (+ unique code Rp1–99) → show QR. (Reuse
   `qrismerchantid.gopay.qris` — EMVCo injection is provider-agnostic.)
2. `watcher.seed()` when the checkout opens.
3. `wait_for_payment(bill_idr, timeout=300)` → on success, record the `id` / `order_id` in YOUR
   database and reject replays; on `TimeoutError`, expire the invoice.

## Etiquette

Poll only while a checkout is active (~10s cadence) — the reference gateway scales requests with
active buyers and sends zero when the shop is quiet. Hammering the feed is how tokens get
rate-limited.
