"""HttpxTransport: offline round trip (MockTransport) + client ownership."""

import httpx

from qrismerchantid.core.transport import HttpxTransport


def test_round_trip_without_network():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["body"] = request.content.decode()
        seen["headers"] = dict(request.headers)
        return httpx.Response(200, json={"success": True})

    transport = HttpxTransport(httpx.Client(transport=httpx.MockTransport(handler)))
    status, text = transport.request(
        "POST", "https://api.gobiz.co.id/v1/merchants/search", '{"from":0}', {"Content-Type": "x"}
    )
    assert (status, text) == (200, '{"success":true}')
    assert seen["method"] == "POST"
    assert seen["url"] == "https://api.gobiz.co.id/v1/merchants/search"
    assert seen["body"] == '{"from":0}'
    transport.close()


def test_close_only_owns_internal_client():
    external = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, text="{}")))
    HttpxTransport(external).close()
    assert not external.is_closed  # user-supplied client left alone
    internal = HttpxTransport()
    internal.close()
    assert internal._client.is_closed
