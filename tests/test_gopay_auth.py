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
    assert body == {"client_id": "go-biz-web-new", "phone_number": "812345678", "country_code": "62"}
    assert "login_type" not in body  # live portal sends none (research §9.2)


def test_request_otp_without_data_returns_whole_body():
    fake = FakeHttpClient((201, {"success": True}))
    assert GoPayMerchant(transport=fake).auth.request_otp("08123456789") == {"success": True}


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


def test_request_otp_normalizes_to_bare_national_format():
    otp_data = {"otp_token": "OT"}
    cases = {
        "085876543210": "85876543210",  # leading 0 stripped (live portal sends bare)
        "+6285876543210": "85876543210",  # +62 stripped
        "6285876543210": "85876543210",  # 62 stripped
        " 0858-7654-3210 ": "85876543210",  # separators stripped
        "(0858) 765.432.10": "85876543210",
        "85876543210": "85876543210",  # already bare — untouched
    }
    for raw, want in cases.items():
        fake = FakeHttpClient()
        fake.add_route("POST", "/goid/login/request", 201, {"data": otp_data, "success": True})
        gopay = GoPayMerchant(transport=fake)
        assert gopay.auth.request_otp(raw) == otp_data
        assert json.loads(fake.calls[0]["body"])["phone_number"] == want


def test_request_otp_rejects_garbage_numbers():
    gopay = GoPayMerchant(transport=FakeHttpClient((201, {"success": True})))
    for bad in ("", "   ", "abc", "+62", "0", "12345", "62"):
        with pytest.raises(ValueError, match="[Dd]ialable|phone"):
            gopay.auth.request_otp(bad)


def test_login_with_password_rejects_bad_email_and_blank_password():
    gopay = GoPayMerchant(transport=FakeHttpClient((201, {"success": True})))
    for bad_email in ("", "   ", "no-at-sign", "a@b", "a @b.id", "a@b id"):
        with pytest.raises(ValueError, match="[Ee]mail"):
            gopay.auth.login_with_password(bad_email, "pw")
    for blank_pw in ("", "   "):
        with pytest.raises(ValueError, match="[Pp]assword"):
            gopay.auth.login_with_password("a@b.id", blank_pw)


def test_login_with_password_strips_email_per_live_har():
    fake = FakeHttpClient()
    fake.add_route("POST", "/goid/login/request", 201, {"data": {}, "success": True})
    fake.add_route("POST", "/goid/token", 201, {"access_token": "AT", "refresh_token": "RT"})
    gopay = GoPayMerchant(transport=fake)
    gopay.auth.login_with_password("  Owner@Toko.id ", "s3cret")
    first, second = fake.calls
    assert json.loads(first["body"])["email"] == "Owner@Toko.id"
    assert json.loads(second["body"])["data"] == {"email": "Owner@Toko.id", "password": "s3cret"}
