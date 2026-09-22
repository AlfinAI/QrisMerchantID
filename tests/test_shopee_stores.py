"""StoresService: cursor paging, unfiltered retry, guards (all offline)."""

import pytest

from qrismerchantid import ShopeePayPartner
from qrismerchantid.core.exceptions import QmidException
from tests.conftest import FakeHttpClient, ScriptedTransport


def _page(stores, total=None, last_id=0):
    data = {"list": [{"storeId": i, "storeName": f"s{i}", "status": 1} for i in stores]}
    if total is not None:
        data["storeCount"] = total
    return (200, {"code": 0, "msg": "ok", "data": data})


def _partner(transport):
    return ShopeePayPartner(token="B:t", transport=transport)


def test_single_short_page_returns_normalized_stores():
    sp = _partner(FakeHttpClient(_page([3, 9])))
    assert sp.stores.list_stores() == [
        {"id": "3", "name": "s3", "status": 1},
        {"id": "9", "name": "s9", "status": 1},
    ]


def test_cursor_paging_until_short_batch():
    full = [{"storeId": i, "storeName": f"s{i}", "status": 1} for i in range(1, 31)]
    script = ScriptedTransport(
        [
            (200, {"code": 0, "msg": "ok", "data": {"list": full}}),
            _page([31, 32]),
        ]
    )
    stores = _partner(script).stores.list_stores()
    assert [s["id"] for s in stores] == [str(i) for i in range(1, 33)]
    assert len(script.calls) == 2
    assert script.calls[0]["body"] and '"lastStoreId": 0' in script.calls[0]["body"]
    assert '"lastStoreId": 30' in script.calls[1]["body"]


def test_store_count_stops_early():
    full = [{"storeId": i, "storeName": f"s{i}", "status": 1} for i in range(1, 31)]
    script = ScriptedTransport([(200, {"code": 0, "msg": "ok", "data": {"list": full, "storeCount": 30}})])
    assert len(_partner(script).stores.list_stores()) == 30


def test_unfiltered_retry_when_filtered_is_empty():
    script = ScriptedTransport(
        [
            (200, {"code": 0, "msg": "ok", "data": {"list": []}}),  # filtered: nothing
            _page([5]),  # unfiltered: found
        ]
    )
    stores = _partner(script).stores.list_stores()
    assert [s["id"] for s in stores] == ["5"]
    assert '"serviceList": [1, 10]' in script.calls[0]["body"]
    assert "serviceList" not in script.calls[1]["body"]  # key omitted, not emptied


def test_empty_everywhere_returns_empty_list():
    script = ScriptedTransport(
        [
            (200, {"code": 0, "msg": "ok", "data": {"list": []}}),
            (200, {"code": 0, "msg": "ok", "data": {"list": []}}),
        ]
    )
    assert _partner(script).stores.list_stores() == []


def test_cursor_must_advance():
    full = [{"storeId": 7, "storeName": "same", "status": 1} for _ in range(30)]
    script = ScriptedTransport([(200, {"code": 0, "msg": "ok", "data": {"list": full}})] * 2)
    with pytest.raises(QmidException, match="cursor did not advance"):
        _partner(script).stores.list_stores()


def test_pagination_limit_raises():
    batch1 = [{"storeId": 100 + i, "storeName": "x", "status": 1} for i in range(30)]
    batch2 = [{"storeId": 200 + i, "storeName": "x", "status": 1} for i in range(30)]
    script = ScriptedTransport(
        [
            (200, {"code": 0, "msg": "ok", "data": {"list": batch1}}),
            (200, {"code": 0, "msg": "ok", "data": {"list": batch2}}),
        ]
    )
    with pytest.raises(QmidException, match="pagination limit"):
        _partner(script).stores.list_stores(max_pages=2)


def _full_batch(last):
    batch = [{"storeId": i, "storeName": f"s{i}", "status": 1} for i in range(1, 30)]
    batch.append(last)
    return (200, {"code": 0, "msg": "ok", "data": {"list": batch}})


def test_string_cursor_advances_paging():
    script = ScriptedTransport([_full_batch({"storeId": "130"}), _page([131])])
    stores = _partner(script).stores.list_stores()
    assert [s["id"] for s in stores][-2:] == ["130", "131"]
    assert '"lastStoreId": 130' in script.calls[1]["body"]


@pytest.mark.parametrize("bad_last", ["junk", None, {"storeId": True}, {"storeId": "abc"}, {}])
def test_unusable_cursor_raises(bad_last):
    script = ScriptedTransport([_full_batch(bad_last)])
    with pytest.raises(QmidException, match="cursor did not advance"):
        _partner(script).stores.list_stores()


def test_malformed_rows_and_shapes_tolerated():
    body = {
        "code": 0,
        "msg": "ok",
        "data": {"list": [{"storeName": "no-id"}, "junk", None, {"storeId": 11}]},
    }
    stores = _partner(FakeHttpClient((200, body))).stores.list_stores()
    assert stores == [{"id": "11", "name": "", "status": 0}]
    fake = FakeHttpClient((200, {"code": 0, "msg": "ok", "data": {"list": {}}}))
    assert _partner(fake).stores.list_stores() == []
