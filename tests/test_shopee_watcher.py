"""ShopeePayWatcher: seed, fresh-only polls, completed-only matching (all offline)."""

import pytest

from qrismerchantid import ShopeePayPartner
from qrismerchantid.shopee.watcher import ShopeePayWatcher
from tests.conftest import FakeHttpClient, ScriptedTransport

TXA = {"id": "a", "order_id": "a", "amount_idr": 50000, "completed": True, "create_time": 1}
TXB = {"id": "b", "order_id": "b", "amount_idr": 409662, "completed": True, "create_time": 2}
PENDING = {"id": "p", "order_id": "p", "amount_idr": 409662, "completed": False, "create_time": 3}


def _feed(*rows):
    return (200, {"code": 0, "msg": "ok", "data": {"list": [], "next_position": ""}})


def _watcher(transport, **kwargs):
    sp = ShopeePayPartner(token="B:t", transport=transport)
    watcher = ShopeePayWatcher(sp.transactions, 7, **kwargs)
    return watcher


def _feed_transport(rows_list):
    """Each poll returns normalized txs by scripting raw rows through list_recent."""
    script = ScriptedTransport(
        [(200, {"code": 0, "msg": "ok", "data": {"list": rows, "next_position": ""}}) for rows in rows_list]
    )
    return script


def _raw(tx_id, amount, completed=True):
    return {
        "transactionId": tx_id,
        "createTime": 1784050000,
        "storeId": 7,
        "service": 1,
        "amount": f"{amount:,}".replace(",", "."),
        "status": 3 if completed else 1,
        "merchantId": 42,
    }


def test_seed_then_no_fresh_on_repeat():
    watcher = _watcher(_feed_transport([[_raw("a", 50000)]]))
    assert watcher.seed() == 1
    # second poll replays the same script exhaustion? no — fresh transport each call:
    watcher2 = _watcher(_feed_transport([[_raw("a", 50000)], [_raw("a", 50000)]]))
    assert watcher2.seed() == 1
    assert watcher2.poll_once() == []


def test_seed_counts_and_poll_returns_only_new():
    script = _feed_transport([[_raw("a", 50000)], [_raw("a", 50000), _raw("b", 409662)]])
    watcher = _watcher(script)
    assert watcher.seed() == 1
    assert [t["id"] for t in watcher.poll_once()] == ["b"]


def test_wait_for_payment_matches_completed_only():
    script = _feed_transport([[_raw("p", 409662, completed=False)], [_raw("b", 409662)]])
    watcher = _watcher(script, poll_interval=0)
    assert watcher.wait_for_payment(409662, timeout=5)["id"] == "b"


def test_wait_for_payment_tolerance():
    script = _feed_transport([[_raw("b", 409700)]])
    watcher = _watcher(script, poll_interval=0)
    assert watcher.wait_for_payment(409662, timeout=5, tolerance=100)["id"] == "b"


def test_wait_for_payment_timeout():
    fake = FakeHttpClient(
        (200, {"code": 0, "msg": "ok", "data": {"list": [_raw("a", 1)], "next_position": ""}})
    )
    watcher = _watcher(fake, poll_interval=0)
    with pytest.raises(TimeoutError, match="999"):
        watcher.wait_for_payment(999, timeout=0.05)


def test_seen_cache_capped_at_500():
    watcher = _watcher(_feed_transport([[]]))
    watcher._seen = {f"x{i}" for i in range(501)}
    watcher.poll_once()
    assert len(watcher._seen) <= 500


def test_id_fallback_chain_and_facade_factory():
    script = ScriptedTransport([(200, {"code": 0, "msg": "ok", "data": {"list": [], "next_position": ""}})])
    watcher = _watcher(script)
    assert watcher._tx_id({}) == "None_None"  # no ids -> time_amount fallback key
    assert watcher._tx_id({"order_id": "o"}) == "o"
    sp = ShopeePayPartner(token="B:t", transport=FakeHttpClient(_feed()))
    watcher = sp.watch(7)
    assert isinstance(watcher, ShopeePayWatcher)
    assert watcher._store_id == 7
