# GoPay transactions — analytics, journals, issuer breakdown

## `analytics()` — the primary feed

`GET https://api.gojekapi.com/merchant-analytics/v2/merchants/transactions`
(query shape verified 1:1 against the portal):

```python
txns = gopay.transactions.analytics(merchant_id, days=7)
txns = gopay.transactions.analytics(merchant_id, start_time=..., end_time=...)  # ISO range
txns = gopay.transactions.analytics(["G1", "G2"], days=1, size=50)               # multi-outlet
```

| Param | Default | Notes |
|---|---|---|
| `days` | 7 | UTC `…T…:….000Z` window; ignored when explicit range given |
| `size` / `from_` | 20 / 0 | pagination |
| `statuses` | `SETTLEMENT,CAPTURE,REFUND,PARTIAL_REFUND` | portal-exact |
| `payment_types` | `QRIS,GOPAY,OFFLINE_CREDIT_CARD,OFFLINE_DEBIT_CARD,CREDIT_CARD` | portal-exact |

Response: `{"from", "size", "total", "transactions": [...]}`. Each tx has 23 keys:
`id`, `wallstreet_transaction_id`, `merchant_id`, `order_id` (`QRIS-…`),
`transaction_status`, `payment_type`, `transaction_time`, `settlement_time`,
`gross_amount` (**int, minor units**), `real_gross_amount`, `currency` (`IDR`),
`service_type`, `channel_type` (`STATIC_QR`), `transaction_source`
(`GOPAY_INSTORE`), `qris_provider_retrieval_reference_number`, `qris_on_us`,
`qris_provider_aspi_issuer` / `…_acquirer`, `merchant_cross_reference_id`,
`shares[]`, `promo_details{}`, `transaction_history[]`, `version`.

## `journals()` — detailed listing

`POST https://api.gobiz.co.id/journals/search` with the DSL query (statuses,
payment types, time range, merchant clause, GoSave exclusions — per gobiz.js).
Special journal headers are attached automatically:

```python
journal = gopay.transactions.journals(merchant_id, start_iso, end_iso, size=50)
```

## `qris_issuer_breakdown()` — aggregation variant

HAR-verified aggregation query (our unique feature — no reference repo has it):

```python
by_issuer = gopay.transactions.qris_issuer_breakdown(start_iso, end_iso)
by_issuer["aggregations"]["by_qris_issuer"]["buckets"]  # per-ASPI-issuer counts
```

NOTE: only `time_range` + `aggs` were fully observed; no `query` clause is sent
(TODO-R6: capture the inner clause shape).

## Money

Analytics amounts are ints in minor units; convert with
`money.to_rupiah()` (`10600000` → `106000.0`). Never display raw values.
