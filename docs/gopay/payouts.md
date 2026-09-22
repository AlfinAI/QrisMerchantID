# GoPay payouts — history + payable balance

HAR-discovered endpoints (research §9.3) — absent from every reference repo. Amounts are **decimal
strings in minor units** (`"11610000.0"` = Rp116.000).

## `list()` — `GET /v1/merchants/payouts?page&per`

```python
page = gopay.payouts.list()               # page=1, per=10
page = gopay.payouts.list(page=2, per=25)
page  # {"payouts": [{"payout_id", "merchant_id", "net_amount", "gross_amount",
      #   "refund_amount", fee/mdr breakdown, "status": "paid",
      #   "created_at", "paid_at", "account_no", ...}],
      #  "current_page", "per", "next_page"}
```

## `payable_detail()` — `GET /v1/merchants/payouts/payable_detail?merchant_id=`

```python
payable = gopay.payouts.payable_detail(merchant_id)
payable  # {"payable_detail": {"payable", "net_amount", "total_settlement",
         #   "total_mdr", "transaction_fee", "adjustments": [], ...}}
```

Convert with `money.to_rupiah()` — it accepts both ints and decimal strings.
