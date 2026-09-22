"""TransactionsService: analytics + journals (offline; shapes per HAR, research §9)."""

import json
from urllib.parse import parse_qs, urlparse

from qrismerchantid import GoPayMerchant
from tests.conftest import FakeHttpClient

TX = {
    "id": "t1",
    "order_id": "QRIS-x",
    "transaction_status": "SETTLEMENT",
    "payment_type": "QRIS",
    "gross_amount": 10600000,
    "currency": "IDR",
}


def test_analytics_explicit_range_hits_analytics_host():
    fake = FakeHttpClient((200, {"transactions": [TX], "total": 1}))
    body = GoPayMerchant(transport=fake).transactions.analytics(
        "G1", start_time="2026-08-31T17:00:00.000Z", end_time="2026-09-30T16:59:59.999Z"
    )
    assert body["total"] == 1
    url = urlparse(fake.last_url)
    assert url.netloc == "api.gojekapi.com"
    assert url.path == "/merchant-analytics/v2/merchants/transactions"
    query = parse_qs(url.query)
    assert query["merchant_ids"] == ["G1"]
    assert query["statuses"] == ["SETTLEMENT,CAPTURE,REFUND,PARTIAL_REFUND"]
    assert "QRIS" in query["payment_types"][0]
    assert (query["size"], query["from"]) == (["20"], ["0"])
    assert query["start_time"] == ["2026-08-31T17:00:00.000Z"]


def test_analytics_days_computes_range_and_joins_merchant_list():
    fake = FakeHttpClient((200, {"transactions": [], "total": 0}))
    GoPayMerchant(transport=fake).transactions.analytics(["G1", "G2"], days=1, size=5)
    query = parse_qs(urlparse(fake.last_url).query)
    assert query["merchant_ids"] == ["G1,G2"]
    assert query["size"] == ["5"]
    assert query["start_time"][0] < query["end_time"][0]


def test_journals_listing_query_shape_and_special_headers():
    fake = FakeHttpClient((200, {"success": True, "hits": []}))
    GoPayMerchant(transport=fake).transactions.journals(
        "G9", "2026-09-01T00:00:00.000Z", "2026-09-02T00:00:00.000Z"
    )
    assert fake.last_url == "https://api.gobiz.co.id/journals/search"
    assert fake.last_headers["X-Client-Id"] == "gobiz-web"
    assert "journal.v1" in fake.last_headers["Accept"]
    body = json.loads(fake.calls[0]["body"])
    assert body["size"] == 50
    assert body["sort"] == {"time": {"order": "desc"}}
    flat = json.dumps(body["query"])
    assert "metadata.transaction.merchant_id" in flat and "G9" in flat
    assert "settlement" in flat and "qris" in flat and "GOSAVE_ONLINE" in flat


def test_qris_issuer_breakdown_aggregation_shape():
    fake = FakeHttpClient((200, {"success": True, "aggregations": {}}))
    GoPayMerchant(transport=fake).transactions.qris_issuer_breakdown("A", "B")
    body = json.loads(fake.calls[0]["body"])
    assert body["size"] == 0
    assert body["time_range"] == {"gte": "A", "lt": "B"}
    terms = body["aggs"]["by_qris_issuer"]["terms"]
    assert terms == {"field": "metadata.provider_metadata.aspi.issuer", "size": 50}
    assert fake.last_headers["X-Client-Id"] == "gobiz-web"
