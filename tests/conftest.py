"""Shared fakes & fixtures. Everything offline — no test may touch the network."""

import json

import pytest


class FakeHttpClient:
    """Canned-response transport with URL routing + full call recording."""

    def __init__(self, default=(200, {})):
        status, body = default
        self.default = (status, body if isinstance(body, str) else json.dumps(body))
        self.routes: list = []
        self.calls: list = []
        self.last_method = self.last_url = self.last_body = None
        self.last_headers = None

    def add_route(self, method, url_contains, status, body):
        text = body if isinstance(body, str) else json.dumps(body)
        self.routes.append((method, url_contains, status, text))
        return self

    def request(self, method, url, body, headers):
        self.calls.append({"method": method, "url": url, "body": body, "headers": dict(headers)})
        self.last_method, self.last_url = method, url
        self.last_body, self.last_headers = body, dict(headers)
        for m, contains, status, text in self.routes:
            if m == method and contains in url:
                return status, text
        return self.default

    @property
    def last_json(self):
        return json.loads(self.last_body) if self.last_body else None


class ScriptedTransport:
    """Returns/raises queued items in order (for retry tests)."""

    def __init__(self, script):
        self.script = list(script)
        self.calls: list = []

    def request(self, method, url, body, headers):
        self.calls.append({"method": method, "url": url, "body": body, "headers": dict(headers)})
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        status, body = item
        return status, body if isinstance(body, str) else json.dumps(body)


@pytest.fixture()
def fake():
    return FakeHttpClient()
