"""MerchantsService.search()/detail() (offline; shapes per HAR, research §9)."""

import json

from qrismerchantid import GoPayMerchant
from tests.conftest import FakeHttpClient


def test_search_defaults_match_live_portal():
    fake = FakeHttpClient((200, {"total": 1, "success": True, "hits": []}))
    gopay = GoPayMerchant(transport=fake)
    assert gopay.merchants.search()["total"] == 1
    assert json.loads(fake.calls[0]["body"]) == {"from": 0, "size": 20}
    assert fake.last_url == "https://api.gobiz.co.id/v1/merchants/search"


def test_search_accepts_pagination():
    fake = FakeHttpClient((200, {"total": 0, "success": True, "hits": []}))
    GoPayMerchant(transport=fake).merchants.search(from_=40, size=5)
    assert json.loads(fake.calls[0]["body"]) == {"from": 40, "size": 5}


def test_detail_gets_merchant_by_id():
    body = {"id": "G123", "merchant_name": "Shop"}
    fake = FakeHttpClient((200, body))
    assert GoPayMerchant(transport=fake).merchants.detail("G123") == body
    assert fake.last_url == "https://api.gobiz.co.id/v1/merchants/G123"
