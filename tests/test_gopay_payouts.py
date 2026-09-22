"""PayoutsService.list()/payable_detail() (offline; HAR-discovered, research §9.3)."""

from qrismerchantid import GoPayMerchant
from tests.conftest import FakeHttpClient


def test_list_defaults_and_pagination():
    fake = FakeHttpClient((200, {"payouts": [], "current_page": 1, "per": 10, "next_page": None}))
    gopay = GoPayMerchant(transport=fake)
    assert gopay.payouts.list()["current_page"] == 1
    assert fake.last_url == "https://api.gobiz.co.id/v1/merchants/payouts?page=1&per=10"
    gopay.payouts.list(page=2, per=5)
    assert fake.last_url == "https://api.gobiz.co.id/v1/merchants/payouts?page=2&per=5"


def test_payable_detail_targets_merchant():
    body = {"payable_detail": {"payable": "11610000.0"}}
    fake = FakeHttpClient((200, body))
    assert GoPayMerchant(transport=fake).payouts.payable_detail("G1") == body
    assert fake.last_url == "https://api.gobiz.co.id/v1/merchants/payouts/payable_detail?merchant_id=G1"
