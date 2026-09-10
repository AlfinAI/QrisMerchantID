"""AuthService: password + OTP flows (offline; shapes per HAR, research §9)."""

import json

import pytest

from qrismerchantid import GoPayMerchant
from qrismerchantid.core.exceptions import ApiException
from tests.conftest import FakeHttpClient


def test_login_with_password_two_step_sets_token():
    fake = FakeHttpClient()
    fake.add_route("POST", "/goid/login/request", 200, {"success": True})
    fake.add_route("POST", "/goid/token", 201, {"access_token": "AT", "refresh_token": "RT"})
    gopay = GoPayMerchant(transport=fake)
    session = gopay.auth.login_with_password("a@b.id", "pw")
    assert session == {"access_token": "AT", "refresh_token": "RT"}
    assert gopay.client.api_headers()["Authorization"] == "Bearer AT"
    first, second = fake.calls
    assert first["url"].endswith("/goid/login/request")
    assert json.loads(first["body"]) == {
        "email": "a@b.id",
        "login_type": "password",
        "client_id": "go-biz-web-new",
    }
    assert json.loads(second["body"]) == {
        "client_id": "go-biz-web-new",
        "grant_type": "password",
        "data": {"email": "a@b.id", "password": "pw"},
    }
    assert first["headers"]["x-appId"] == "go-biz-web-dashboard"  # auth header set


def test_request_otp_omits_login_type_per_har():
    fake = FakeHttpClient()
    otp_data = {"otp_token": "OT", "otp_expires_in": 720, "otp_length": 4, "next_state": {"state": "sms"}}
    fake.add_route("POST", "/goid/login/request", 201, {"data": otp_data, "success": True})
    gopay = GoPayMerchant(transport=fake)
    assert gopay.auth.request_otp("0812 345-678") == otp_data
    body = json.loads(fake.calls[0]["body"])
    assert body == {"client_id": "go-biz-web-new", "phone_number": "0812345678", "country_code": "62"}
    assert "login_type" not in body  # live portal sends none (research §9.2)


def test_request_otp_without_data_returns_whole_body():
    fake = FakeHttpClient((201, {"success": True}))
    assert GoPayMerchant(transport=fake).auth.request_otp("0811") == {"success": True}


def test_login_with_otp_strips_code_and_sets_token():
    fake = FakeHttpClient((201, {"access_token": "AT2", "refresh_token": "RT2"}))
    gopay = GoPayMerchant(transport=fake)
    session = gopay.auth.login_with_otp(" 1234\n", "OT")
    assert session["access_token"] == "AT2"
    assert gopay.client.api_headers()["Authorization"] == "Bearer AT2"
    assert json.loads(fake.calls[0]["body"]) == {
        "client_id": "go-biz-web-new",
        "grant_type": "otp",
        "data": {"otp": "1234", "otp_token": "OT"},
    }


def test_login_error_propagates_as_api_exception():
    fake = FakeHttpClient((401, {"errors": [{"message": "OTP salah"}]}))
    with pytest.raises(ApiException, match="OTP salah"):
        GoPayMerchant(transport=fake).auth.login_with_otp("0000", "OT")
