"""Transaction history: merchant-analytics (primary) + journals (detail/agg).

Query shapes verified against the live portal capture (HAR, Sep 2026 —
research §9.1). Amounts come back in MINOR units — see :mod:`gopay.money`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from qrismerchantid.gopay import constants as C
from qrismerchantid.gopay.client import GoPayClient


class TransactionsService:
    """Read-only mutasi: analytics listing, journals listing, QRIS issuer breakdown."""

    def __init__(self, client: GoPayClient) -> None:
        self._client = client

    def analytics(
        self,
        merchant_id: str | list[str],
        *,
        days: int = 7,
        start_time: str | None = None,
        end_time: str | None = None,
        size: int = 20,
        from_: int = 0,
        statuses: str = C.DEFAULT_STATUSES,
        payment_types: str = C.DEFAULT_PAYMENT_TYPES,
    ) -> dict[str, Any]:
        """GET the merchant-analytics transaction feed.

        Args:
            merchant_id: one ID or a list (sent comma-separated).
            days: lookback window when ``start_time``/``end_time`` are omitted
                (UTC ``…T…:….000Z``, portal style).
            start_time/end_time: explicit ISO range (overrides ``days``).
            size/from_: pagination. ``statuses``/``payment_types``: exact portal
                defaults, overridable.

        Returns ``{"from", "size", "total", "transactions": [...]}``. Each tx
        carries ``gross_amount`` as an int in minor units (÷100 → rupiah).
        """
        end = end_time or _utc_zulu(datetime.now(timezone.utc))
        if start_time is None and end_time is None:
            start = _utc_zulu(datetime.now(timezone.utc).replace(microsecond=0))
            # recompute honestly from `days` (kept readable over clever)
            start = _days_ago_zulu(days)
        else:
            start = start_time or end
        mids = ",".join(merchant_id) if isinstance(merchant_id, list) else merchant_id
        params = {
            "from": str(from_),
            "size": str(size),
            "statuses": statuses,
            "payment_types": payment_types,
            "start_time": start,
            "end_time": end,
            "merchant_ids": mids,
        }
        return self._client.get("/merchant-analytics/v2/merchants/transactions", params, C.ANALYTICS_BASE_URL)

    def journals(
        self, merchant_id: str, start_time: str, end_time: str, *, size: int = 50, from_: int = 0
    ) -> dict[str, Any]:
        """POST ``/journals/search`` — detailed listing query (DSL per gobiz.js).

        Time range is ISO (e.g. ``2026-09-01T00:00:00.000Z``). Sends the journals
        special headers (research §9.2).
        """
        body = {
            "from": from_,
            "size": size,
            "sort": {"time": {"order": "desc"}},
            "included_categories": {"incoming": ["transaction_share", "action"]},
            "query": [
                {
                    "op": "and",
                    "clauses": [
                        {
                            "op": "not",
                            "clauses": [
                                {
                                    "op": "or",
                                    "clauses": [
                                        {
                                            "field": "metadata.source",
                                            "op": "in",
                                            "value": ["GOSAVE_ONLINE", "GoSave", "GODEALS_ONLINE"],
                                        },
                                        {
                                            "field": "metadata.gopay.source",
                                            "op": "in",
                                            "value": ["GOSAVE_ONLINE", "GoSave", "GODEALS_ONLINE"],
                                        },
                                    ],
                                }
                            ],
                        },
                        {
                            "field": "metadata.transaction.status",
                            "op": "in",
                            "value": ["settlement", "capture", "refund", "partial_refund"],
                        },
                        {
                            "field": "metadata.transaction.payment_type",
                            "op": "in",
                            "value": [
                                "qris",
                                "gopay",
                                "offline_credit_card",
                                "offline_debit_card",
                                "credit_card",
                            ],
                        },
                        {"field": "metadata.transaction.transaction_time", "op": "gte", "value": start_time},
                        {"field": "metadata.transaction.transaction_time", "op": "lte", "value": end_time},
                        {"field": "metadata.transaction.merchant_id", "op": "equal", "value": merchant_id},
                    ],
                }
            ],
        }
        return self._client.post("/journals/search", body, extra_headers=C.JOURNAL_HEADERS)

    def qris_issuer_breakdown(self, start_time: str, end_time: str) -> dict[str, Any]:
        """POST ``/journals/search`` — aggregation variant (HAR-verified).

        Returns ``{"success", "total", "aggregations": {"by_qris_issuer": {"buckets"...}}}``.
        NOTE: only ``time_range`` + ``aggs`` were fully observed; the inner
        ``query`` clause shape is TODO-R6, so none is sent.
        """
        body = {
            "size": 0,
            "included_categories": {"incoming": []},
            "time_range": {"gte": start_time, "lt": end_time},
            "aggs": {
                "by_qris_issuer": {"terms": {"field": "metadata.provider_metadata.aspi.issuer", "size": 50}}
            },
        }
        return self._client.post("/journals/search", body, extra_headers=C.JOURNAL_HEADERS)


def _utc_zulu(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _days_ago_zulu(days: int) -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return _utc_zulu(datetime.fromtimestamp(now.timestamp() - days * 86400, tz=timezone.utc))
