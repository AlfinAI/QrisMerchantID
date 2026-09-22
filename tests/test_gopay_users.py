"""UsersService.me() (offline)."""

from qrismerchantid import GoPayMerchant
from tests.conftest import FakeHttpClient


def test_me_returns_profile_body():
    body = {"user": {"id": 1, "email": "a@b.id", "roles": ["verified_admin"]}}
    fake = FakeHttpClient((200, body))
    assert GoPayMerchant(transport=fake).users.me() == body
    assert fake.last_method == "GET"
    assert fake.last_url == "https://api.gobiz.co.id/v1/users/me"
