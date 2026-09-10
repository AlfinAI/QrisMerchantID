"""PaymentWatcher: seed, fresh-only polls, wait_for_payment (all offline)."""

import pytest

from qrismerchantid import GoPayMerchant
from qrismerchantid.gopay.watcher import PaymentWatcher
from tests.conftest import FakeHttpClient, ScriptedTransport

TXA = {"id": "a", "gross_amount": 5000000, "transaction_time": "t1"}
TXB = {"id": "b", "gross_amount": 10600000, "transaction_time": "t2"}


def _watcher(transport, **kwargs):
    return PaymentWatcher(GoPayMerchant(transport=transport).transactions, "G1", **kwargs)


def test_seed_then_no_fresh_on_repeat():
    watcher = _watcher(FakeHttpClient((200, {"transactions": [TXA], "total": 1})))
    assert watcher.seed() == 1
    assert watcher.poll_once() == []


def test_poll_once_returns_only_new():
    script = ScriptedTransport([(200, {"transactions": [TXA]}), (200, {"transactions": [TXA, TXB]})])
    watcher = _watcher(script)
    assert watcher.seed() == 1
    assert [t["id"] for t in watcher.poll_once()] == ["b"]


def test_wait_for_payment_matches_with_tolerance():
    script = ScriptedTransport([(200, {"transactions": []}), (200, {"transactions": [TXB]})])
    watcher = _watcher(script, poll_interval=0)
    assert watcher.wait_for_payment(10600100, timeout=5, tolerance=100)["id"] == "b"


def test_wait_for_payment_timeout():
    watcher = _watcher(FakeHttpClient((200, {"transactions": [TXA]})), poll_interval=0)
    with pytest.raises(TimeoutError, match="999"):
        watcher.wait_for_payment(999, timeout=0.05)


def test_seen_cache_capped_at_500():
    watcher = _watcher(FakeHttpClient((200, {"transactions": []})))
    watcher._seen = {f"x{i}" for i in range(501)}
    watcher.poll_once()
    assert len(watcher._seen) <= 500


def test_missing_or_malformed_transactions_tolerated():
    assert _watcher(FakeHttpClient((200, {"success": True}))).seed() == 0
    assert _watcher(FakeHttpClient((200, {"transactions": {}}))).seed() == 0


def test_id_fallback_chain_and_facade_factory():
    script = ScriptedTransport([(200, {"transactions": [{"gross_amount": 1, "transaction_time": "t"}]})])
    assert _watcher(script).seed() == 1  # no ids -> time_amount fallback key
    gopay = GoPayMerchant(transport=FakeHttpClient((200, {})))
    watcher = gopay.watch("G1")
    assert isinstance(watcher, PaymentWatcher)
    assert watcher._merchant_id == "G1"
