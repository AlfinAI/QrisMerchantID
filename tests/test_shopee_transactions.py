"""TransactionsService: feed shape, normalization, scope, cursors (all offline)."""

import pytest

from qrismerchantid import ShopeePayPartner
from qrismerchantid.core.exceptions import QmidException
from tests.conftest import FakeHttpClient, ScriptedTransport

ROW = {
    "transactionId": "264693445089687719",
    "externalTransactionId": "EXT-1",
    "displayTransactionId": "DSP-1",
    "createTime": 1784050000,
    "storeId": 7,
    "service": 1,
    "amount": "409.662",
    "status": 3,
    "transactionType": 3,
    "merchantId": 42,
}


def _feed(rows, cursor=""):
    return (200, {"code": 0, "msg": "ok", "data": {"list": rows, "next_position": cursor}})


def _partner(transport):
    return ShopeePayPartner(token="B:t", transport=transport)


def test_normalized_shape():
    body = _partner(FakeHttpClient(_feed([ROW]))).transactions.list_recent(7, merchant_id=42)
    assert body["pages_fetched"] == 1
    assert body["truncated"] is False
    (tx,) = body["transactions"]
    assert tx["id"] == "264693445089687719"
    assert tx["order_id"] == "EXT-1"  # external wins
    assert tx["amount_idr"] == 409662
    assert tx["create_time"] == 1784050000
    assert tx["create_time_iso"] == "2026-07-14T17:26:40.000Z"
    assert tx["store_id"] == "7"
    assert tx["merchant_id"] == "42"
    assert tx["status"] == 3
    assert tx["completed"] is True
    assert tx["payment_type"] == "shopee:1"
    assert tx["raw"] is ROW or tx["raw"] == ROW


def test_order_id_fallback_chain():
    no_ext = {**ROW, "externalTransactionId": None}
    (tx,) = _partner(FakeHttpClient(_feed([no_ext]))).transactions.list_recent(7)["transactions"]
    assert tx["order_id"] == "DSP-1"
    bare = {k: v for k, v in ROW.items() if k not in ("externalTransactionId", "displayTransactionId")}
    (tx,) = _partner(FakeHttpClient(_feed([bare]))).transactions.list_recent(7)["transactions"]
    assert tx["order_id"] == "264693445089687719"


def test_non_completed_status_kept_but_flagged():
    feed = _feed([{**ROW, "status": 1}])
    (tx,) = _partner(FakeHttpClient(feed)).transactions.list_recent(7)["transactions"]
    assert tx["status"] == 1
    assert tx["completed"] is False


def test_out_of_scope_and_malformed_rows_dropped():
    rows = [
        {**ROW, "storeId": 8},  # wrong store
        {**ROW, "transactionId": "  "},  # blank id
        {**ROW, "transactionId": "b", "amount": "nope"},  # bad amount
        {**ROW, "transactionId": "c", "amount": 500},  # non-string amount
        {**ROW, "transactionId": "d", "createTime": "soon"},  # bad time
        {**ROW, "transactionId": "e", "createTime": 10**20},  # unrepresentable time
        "junk",
        None,
        ROW,
    ]
    txns = _partner(FakeHttpClient(_feed(rows))).transactions.list_recent(7)["transactions"]
    assert [t["id"] for t in txns] == ["264693445089687719"]


def test_merchant_scope_enforced_when_given():
    txns = _partner(FakeHttpClient(_feed([ROW]))).transactions.list_recent(7, merchant_id=43)["transactions"]
    assert txns == []


def test_cursor_pages_merge_and_dedupe():
    script = ScriptedTransport(
        [
            _feed([ROW], cursor="c1"),
            _feed([ROW, {**ROW, "transactionId": "264693445089687720", "amount": "1.000"}], cursor=""),
        ]
    )
    body = _partner(script).transactions.list_recent(7)
    assert [t["id"] for t in body["transactions"]] == ["264693445089687719", "264693445089687720"]
    assert body["pages_fetched"] == 2
    assert body["truncated"] is False
    assert '"next_position": "c1"' in script.calls[1]["body"]


def test_cursor_must_advance():
    script = ScriptedTransport([_feed([ROW], cursor="stuck")] * 2)
    with pytest.raises(QmidException, match="cursor did not advance"):
        _partner(script).transactions.list_recent(7)


def test_repeated_cursor_from_history_raises():
    script = ScriptedTransport([_feed([ROW], cursor="a"), _feed([ROW], cursor="b"), _feed([ROW], cursor="a")])
    with pytest.raises(QmidException, match="cursor did not advance"):
        _partner(script).transactions.list_recent(7)


def test_max_pages_truncates():
    script = ScriptedTransport([_feed([ROW], cursor="c1"), _feed([ROW], cursor="c2")])
    body = _partner(script).transactions.list_recent(7, max_pages=2)
    assert body["pages_fetched"] == 2
    assert body["truncated"] is True


def test_non_list_feed_tolerated():
    body = _partner(FakeHttpClient(_feed({"nope": 1}))).transactions.list_recent(7)
    assert body["transactions"] == []
    assert body["truncated"] is False


def test_reversed_range_rejected_and_page_size_clamped():
    sp = _partner(FakeHttpClient(_feed([])))
    with pytest.raises(ValueError, match="time range"):
        sp.transactions.list_recent(7, start_time=200, end_time=100)
    fake = FakeHttpClient(_feed([]))
    _partner(fake).transactions.list_recent(7, page_size=99)
    assert fake.last_json["data"]["pageSize"] == 10
    _partner(fake).transactions.list_recent(7, page_size=0)
    assert fake.last_json["data"]["pageSize"] == 1
