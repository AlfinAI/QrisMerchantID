"""GoPayClient: split headers, retries, error mapping (all offline)."""

import httpx
import pytest

from qrismerchantid.core.exceptions import ApiException
from qrismerchantid.gopay.client import GoPayClient
from tests.conftest import FakeHttpClient, ScriptedTransport


def test_auth_headers_use_full_device_set():
    client = GoPayClient()
    headers = client.auth_headers()
    assert headers["Authentication-Type"] == "go-id"
    assert headers["X-User-Type"] == "merchant"
    assert headers["x-appId"] == "go-biz-web-dashboard"
    assert headers["X-Platform"] == "Web"
    assert headers["Accept-Language"] == "id"
    assert headers["Authorization"] == "Bearer"  # no token yet
    assert "x-uniqueid" in headers
    client.close()


def test_api_headers_are_slimmer_and_carry_token():
    client = GoPayClient(access_token="tok")
    headers = client.api_headers()
    assert headers["Authorization"] == "Bearer tok"
    assert headers["Authentication-Type"] == "go-id"
    assert "x-appId" not in headers
    assert "X-User-Type" not in headers
    assert "x-uniqueid" not in headers
    client.close()


def test_set_access_token_updates_both_header_sets():
    client = GoPayClient()
    client.set_access_token("abc")
    assert client.auth_headers()["Authorization"] == "Bearer abc"
    assert client.api_headers()["Authorization"] == "Bearer abc"
    client.set_access_token(None)
    assert client.api_headers()["Authorization"] == "Bearer"
    client.close()


def test_post_uses_auth_headers_for_auth_calls():
    fake = FakeHttpClient((201, {"access_token": "t"}))
    GoPayClient(transport=fake).post("/goid/token", {"a": 1}, auth_call=True)
    assert fake.last_url == "https://api.gobiz.co.id/goid/token"
    assert fake.last_json == {"a": 1}
    assert fake.last_headers["x-appId"] == "go-biz-web-dashboard"


def test_post_uses_api_headers_by_default():
    fake = FakeHttpClient((200, {"success": True}))
    GoPayClient(transport=fake).post("/v1/merchants/search", {"from": 0})
    assert "x-appId" not in fake.last_headers


def test_get_builds_query_string():
    fake = FakeHttpClient((200, {}))
    GoPayClient(transport=fake).get("/v1/x", {"page": "1", "per": "10"})
    assert fake.last_url == "https://api.gobiz.co.id/v1/x?page=1&per=10"


def test_201_counts_as_success():
    fake = FakeHttpClient((201, {"ok": True}))
    assert GoPayClient(transport=fake).post("/goid/token", {}) == {"ok": True}


def test_retries_transport_errors_then_succeeds():
    script = ScriptedTransport([httpx.ConnectError("down"), (200, {"ok": True})])
    assert GoPayClient(transport=script, backoff_base=0).get("/v1/users/me") == {"ok": True}
    assert len(script.calls) == 2


def test_retry_budget_exhausted_reraises():
    script = ScriptedTransport([httpx.ConnectError("x"), httpx.TimeoutException("y")])
    with pytest.raises(httpx.TransportError):
        GoPayClient(transport=script, max_retries=1, backoff_base=0).get("/v1/users/me")
    assert len(script.calls) == 2  # 1 initial + 1 retry


def test_http_error_raises_without_retry_and_extracts_code():
    fake = FakeHttpClient((401, {"errors": [{"message": "Token expired", "code": "E1"}]}))
    with pytest.raises(ApiException) as exc_info:
        GoPayClient(transport=fake).get("/v1/users/me")
    err = exc_info.value
    assert err.http_status == 401
    assert str(err) == "Token expired"
    assert err.code == "E1"
    assert err.payload["errors"][0]["code"] == "E1"
    assert len(fake.calls) == 1


def test_http_error_without_errors_array_uses_message():
    fake = FakeHttpClient((500, {"message": "boom"}))
    with pytest.raises(ApiException) as exc_info:
        GoPayClient(transport=fake).get("/v1/users/me")
    assert (str(exc_info.value), exc_info.value.code) == ("boom", None)


def test_http_error_without_any_message_falls_back_to_status():
    fake = FakeHttpClient((502, {"weird": 1}))
    with pytest.raises(ApiException) as exc_info:
        GoPayClient(transport=fake).get("/v1/users/me")
    assert str(exc_info.value) == "GoBiz HTTP 502"


def test_invalid_and_non_object_json_raise():
    for text in ("not-json{{{", "[1, 2]"):
        fake = FakeHttpClient((200, text))
        with pytest.raises(ApiException):
            GoPayClient(transport=fake).get("/v1/users/me")


def test_close_is_noop_with_injected_transport():
    GoPayClient(transport=FakeHttpClient()).close()  # must not raise
