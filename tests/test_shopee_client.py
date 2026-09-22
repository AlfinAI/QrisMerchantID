"""ShopeePayClient: envelope handling, headers, retries (all offline)."""

import httpx
import pytest

from qrismerchantid import ShopeePayPartner
from qrismerchantid.core.exceptions import ApiException, QmidException
from qrismerchantid.shopee import constants as C
from tests.conftest import FakeHttpClient, ScriptedTransport

OK = (200, {"code": 0, "msg": "success", "data": {"list": [], "next_position": ""}})


def _partner(transport, **kwargs):
    kwargs.setdefault("token", "B:test-token")
    return ShopeePayPartner(transport=transport, **kwargs)


def test_success_unwraps_data_and_sends_wire_shape():
    fake = FakeHttpClient(OK)
    data = _partner(fake).transactions.list_recent(7, minutes=5)
    assert data["transactions"] == []
    assert fake.last_method == "POST"
    assert fake.last_url == C.PAY_BASE_URL + C.ENDPOINT_TRANSACTIONS
    inner = fake.last_json["data"]
    assert inner["metadata"] == {"token": "B:test-token", "language": "id", "timezone": "Asia/Jakarta"}
    assert inner["filter"]["serviceList"] == [1, 3]
    assert inner["sorter"] == {"field": "createTime", "order": "descend"}
    assert inner["next_position"] == ""
    assert inner["filter"]["endTime"] - inner["filter"]["startTime"] == 300
    headers = fake.last_headers
    assert headers["Origin"] == C.PARTNER_ORIGIN
    assert headers["Referer"] == C.PARTNER_REFERER
    assert headers["X-Token"] == ""
    assert headers["X-Timestamp-Ms"].isdigit()


def test_missing_token_raises_before_network():
    fake = FakeHttpClient(OK)
    with pytest.raises(QmidException, match="No ShopeePay token"):
        ShopeePayPartner(transport=fake).stores.list_stores()
    assert fake.calls == []


def test_envelope_error_on_http_200_raises_api_exception():
    fake = FakeHttpClient((200, {"code": 500001, "msg": "busy", "data": {}}))
    with pytest.raises(ApiException) as exc:
        _partner(fake).stores.list_stores()
    assert exc.value.code == "500001"
    assert "get-store-list" in str(exc.value)
    assert exc.value.http_status == 200


@pytest.mark.parametrize("code", ["200020", "2010000", 200020])
def test_invalid_token_codes_are_terminal_with_renew_hint(code):
    fake = FakeHttpClient((200, {"code": code, "msg": "invalid", "data": {}}))
    with pytest.raises(ApiException, match="fresh B: token"):
        _partner(fake).stores.list_stores()


def test_auth_mention_in_message_also_hints_renewal():
    fake = FakeHttpClient((200, {"code": 999, "msg": "session expired, login again", "data": {}}))
    with pytest.raises(ApiException, match="fresh B: token"):
        _partner(fake).stores.list_stores()


def test_http_error_with_envelope_body():
    fake = FakeHttpClient((401, {"code": 200020, "msg": "not authorized"}))
    with pytest.raises(ApiException) as exc:
        _partner(fake).stores.list_stores()
    assert exc.value.code == "200020"
    assert exc.value.http_status == 401
    assert exc.value.payload["msg"] == "not authorized"


def test_invalid_and_non_object_bodies():
    with pytest.raises(ApiException, match="invalid JSON"):
        _partner(FakeHttpClient((200, "<html>nope"))).stores.list_stores()
    with pytest.raises(ApiException, match="non-object JSON"):
        _partner(FakeHttpClient((200, "[1,2]"))).stores.list_stores()
    with pytest.raises(ApiException, match="non-object data"):
        _partner(FakeHttpClient((200, {"code": 0, "msg": "ok", "data": [1]}))).stores.list_stores()


def test_transport_errors_retry_then_succeed():
    ok = (200, {"code": 0, "msg": "ok", "data": {"list": [{"storeId": 1}], "storeCount": 1}})
    script = ScriptedTransport([httpx.ConnectError("down"), ok])
    data = _partner(script, backoff_base=0).stores.list_stores()
    assert [s["id"] for s in data] == ["1"]
    assert len(script.calls) == 2


def test_transport_errors_exhaust_retries():
    script = ScriptedTransport([httpx.ConnectError("down")] * 3)
    with pytest.raises(httpx.ConnectError):
        _partner(script, backoff_base=0, max_retries=2).stores.list_stores()
    assert len(script.calls) == 3


def test_http_errors_never_retry():
    fake = FakeHttpClient((500, {"code": 1, "msg": "err"}))
    with pytest.raises(ApiException):
        _partner(fake).stores.list_stores()
    assert len(fake.calls) == 1


def test_set_token_and_close():
    fake = FakeHttpClient(OK)
    sp = ShopeePayPartner(transport=fake)
    sp.set_token("B:abc")
    assert sp.stores.list_stores() == []
    assert fake.last_json["data"]["metadata"]["token"] == "B:abc"
    sp.client.close()  # no-op for injected fakes
