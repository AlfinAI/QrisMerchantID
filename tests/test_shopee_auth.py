"""ShopeePay AuthService: OTP login, sessions, renewal (all offline via MockTransport)."""

import base64
import json

import httpx
import pytest

from qrismerchantid import ShopeePayPartner
from qrismerchantid.core.exceptions import ApiException, QmidException
from qrismerchantid.shopee import AuthService
from qrismerchantid.shopee import auth as A
from qrismerchantid.shopee import constants as C
from tests.conftest import FakeHttpClient

RISK = "24,80,16,2,1-risk-token"


def _jwt(payload):
    def b64(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    return f"{b64({'alg': 'none'})}.{b64(payload)}.sig"


JWT = _jwt({"token": "B:login-token", "userid": 501, "businessId": 1, "exp": 9999999999})
JWT2 = _jwt({"token": "B:renewed-token", "userid": "501", "businessId": "1", "exp": 9999999999})

MERCHANT = {
    "merchantId": 42,
    "merchantName": "Toko",
    "merchantStatus": 1,
    "staffTobUid": 501,
    "staffRole": 2,
    "staffStatus": 1,
    "isActive": True,
    "isBanned": False,
    "isCurrentLoginUser": True,
}
MERCHANT_BANNED = {
    **MERCHANT,
    "merchantId": 43,
    "staffTobUid": 502,
    "isActive": False,
    "isBanned": True,
    "isCurrentLoginUser": False,
}


class MockShopee:
    """Routed httpx.MockTransport handler with call recording."""

    def __init__(self):
        self.routes = []
        self.calls = []

    def add(self, method, url_contains, body, status=200, headers=None):
        self.routes.append((method, url_contains, status, body, headers or {}))
        return self

    def json(self, method, url_contains, obj, status=200, headers=None):
        return self.add(method, url_contains, json.dumps(obj), status, headers)

    def __call__(self, request):
        self.calls.append(
            {
                "method": request.method,
                "url": str(request.url),
                "body": request.content.decode("utf-8", "replace"),
                "headers": dict(request.headers),
            }
        )
        for method, contains, status, body, headers in self.routes:
            if method == request.method and contains in str(request.url):
                return httpx.Response(status, content=body, headers=headers, request=request)
        raise AssertionError(f"no route for {request.method} {request.url}")

    @property
    def transport(self):
        return httpx.MockTransport(self)

    def bodies(self, url_contains):
        return [json.loads(c["body"]) for c in self.calls if url_contains in c["url"]]


def _otp_routes(mock, *, password=True, channels=(1, 2, 3, 5), default_channel=3):
    mock.add("GET", "/login", "<html>login</html>", headers={"set-cookie": "csrftoken=CSRF123; Path=/"})
    mock.json("POST", "/v2/shpsec/web/report", {"code": 0, "msg": "ok", "data": {"riskToken": RISK}})
    mock.json("POST", "check_password_migrate", {"error": 0, "error_msg": "", "data": {}})
    mock.json("POST", "check_account_exist_by_password", {"error": 48401004, "error_msg": "x"})
    if password:
        mock.json("POST", "authenticate_toc_by_password", {"error": C.NEED_OTP_CODE, "error_msg": "need otp"})
    else:
        mock.json("POST", "authenticate_toc_by_password", {"error": 0, "error_msg": "", "data": {}})
    mock.json(
        "POST",
        "get_otp_settings",
        {
            "error": 0,
            "error_msg": "",
            "data": {"available_channel_list": list(channels), "default_channel": default_channel},
        },
    )
    mock.json("POST", "send_otp", {"error": 0, "error_msg": "", "data": {"seed": "s"}})
    return mock


def _auth_service(mock, **kwargs):
    kwargs.setdefault("transport", mock.transport)
    kwargs.setdefault("backoff_base", 0)
    return AuthService(**kwargs)


# ---------------------------------------------------------------- pure helpers
def test_hash_vector():
    assert A.hash_shopee_password("test123") == (
        "2e6a0fc5e51d119fc5cd8c0a89bbbc7ae5a700f944d54fc167deb8fe0a9adb24"
    )
    assert len(A.hash_shopee_password("x")) == 64


@pytest.mark.parametrize(
    ("raw", "e164", "national"),
    [
        ("081297110640", "6281297110640", "081297110640"),
        ("6281297110640", "6281297110640", "081297110640"),
        ("+62 812-9711-0640", "6281297110640", "081297110640"),
        ("81297110640", "6281297110640", "081297110640"),
        ("00 62 081297110640", "6281297110640", "081297110640"),
        ("(0812) 9711 0640", "6281297110640", "081297110640"),
    ],
)
def test_parse_id_mobile_valid(raw, e164, national):
    parsed = A.parse_id_mobile(raw)
    assert (parsed["e164"], parsed["national"], parsed["subscriber"]) == (e164, national, e164[2:])


@pytest.mark.parametrize(
    "raw", ["", "   ", "abc", "021234567", "12345", "0812", "+1 555 123 4567", "628129711064012345"]
)
def test_parse_id_mobile_invalid(raw):
    with pytest.raises(ValueError, match="valid Indonesian mobile"):
        A.parse_id_mobile(raw)


def test_grouped_phone_format():
    assert A.format_phone_for_verification("628977110640") == "(+62) 897 7110 640"
    assert A.format_phone_for_verification("62812") == "(+62) 812"


def test_merchant_helpers():
    good = {"id": "1", "is_active": True, "is_banned": False, "is_current_login_user": False}
    current = {**good, "id": "2", "is_current_login_user": True}
    banned = {**good, "id": "3", "is_banned": True}
    assert A.usable_merchants([good, current, banned]) == [good, current]
    assert A.resolve_single_merchant([good, current, banned]) == current
    assert A.resolve_single_merchant([good, banned]) == good
    assert A.resolve_single_merchant([good, {**good, "id": "9"}]) is None


def test_partner_state_and_referer_shapes():
    state = A.partner_state()
    assert "business_next=" in state and "business_client_id=1" in state
    referer = A.login_referer()
    assert referer.startswith(C.ACCOUNT_BASE_URL + C.ENDPOINT_AUTHENTICATE_LOGIN)
    assert "client_id=5" in referer and "should_hide_back=true" in referer


def test_read_merchant_credential():
    cookies = [{"name": C.LIVE_TOKEN_COOKIE, "value": JWT, "domain": "x", "path": "/"}]
    cred = A.read_merchant_credential(cookies)
    assert cred == {
        "token": "B:login-token",
        "account_id": "501",
        "business_id": "1",
        "expires_at": 9999999999000,
    }
    assert (
        A.read_merchant_credential(
            [{"name": C.LIVE_TOKEN_COOKIE, "value": JWT2, "domain": "x", "path": "/"}]
        )["account_id"]
        == "501"
    )


@pytest.mark.parametrize("value", ["", "a.b", "a..c", "h.badjson.sig", "h.e30.sig"])
def test_read_merchant_credential_unreadable(value):
    cookies = [{"name": C.LIVE_TOKEN_COOKIE, "value": value, "domain": "x", "path": "/"}]
    with pytest.raises(QmidException, match="unreadable|did not return"):
        A.read_merchant_credential(cookies)


def test_read_merchant_credential_missing_cookie():
    with pytest.raises(QmidException, match="did not return"):
        A.read_merchant_credential([{"name": "other", "value": "x"}])


# ---------------------------------------------------------------- request_otp
def test_request_otp_full_chain_and_wire_shapes():
    mock = _otp_routes(MockShopee())
    auth = _auth_service(mock)
    challenge = auth.request_otp("0812 9711-0640", password="test123")
    assert challenge["version"] == 1
    assert challenge["phone_number"] == "6281297110640"
    assert challenge["channel"] == 3
    assert challenge["available_channels"] == [1, 2, 3, 5]
    assert challenge["device_fingerprint"] == RISK
    assert challenge["risk_token"] == RISK
    assert challenge["has_password"] is True
    assert any(c["name"] == "csrftoken" for c in challenge["cookies"])

    report = mock.calls[1]
    assert report["body"] == "{}"  # no blob -> empty JSON object
    assert report["headers"]["content-type"] == "application/json"
    assert "szdet" not in report["headers"]

    by_pw = mock.bodies("authenticate_toc_by_password")[0]
    assert by_pw["phone"] == "6281297110640"
    assert by_pw["password"] == A.hash_shopee_password("test123")
    assert by_pw["security_device_fingerprint"] == RISK

    send = mock.bodies("send_otp")[0]
    assert send["supported_channels"] == [1, 2, 3, 5, 4]
    assert send["channel"] == 3
    assert send["captcha_signature"] == ""
    settings = mock.bodies("get_otp_settings")[0]
    assert settings["supported_channels"] == [1, 2, 3, 5]

    for call in mock.calls[2:]:
        assert call["headers"].get("af-ac-enc-sz-token") == RISK
        assert call["headers"].get("x-csrftoken") == "CSRF123"
        assert call["headers"]["x-app-type"] == "2"


def test_request_otp_with_device_report_blob():
    mock = _otp_routes(MockShopee())
    challenge = _auth_service(mock).request_otp("081297110640", password="p", device_report="BLOB!")
    assert challenge["device_fingerprint"] == RISK
    report = mock.calls[1]
    assert report["body"] == "BLOB!"
    assert report["headers"]["content-type"] == "text/plain;charset=UTF-8"
    assert report["headers"]["szdet"].isdigit()


def test_request_otp_facade_default_blob():
    mock = _otp_routes(MockShopee())
    sp = ShopeePayPartner(auth_transport=mock.transport, device_report="Dflt")
    sp.auth.request_otp("081297110640", password="p")
    assert mock.calls[1]["body"] == "Dflt"
    sp.close()


def test_request_otp_passwordless_and_channel_rules():
    mock = _otp_routes(MockShopee(), password=False)
    challenge = _auth_service(mock).request_otp("081297110640")
    assert challenge["has_password"] is False
    assert mock.bodies("authenticate_toc_by_password")[0]["password"] == ""

    mock = _otp_routes(MockShopee())
    challenge = _auth_service(mock).request_otp("081297110640", password="p", channel=1)
    assert challenge["channel"] == 1

    mock = _otp_routes(MockShopee())
    with pytest.raises(ValueError, match="channel is unavailable"):
        _auth_service(mock).request_otp("081297110640", password="p", channel=9)


def test_request_otp_password_required_paths():
    mock = _otp_routes(MockShopee())
    with pytest.raises(ValueError, match="password-protected"):
        _auth_service(mock).request_otp("081297110640")  # NEED_OTP but no password

    mock = MockShopee()
    _otp_routes(mock)
    mock.routes = [r for r in mock.routes if "authenticate_toc_by_password" not in r[1]]
    mock.json(
        "POST",
        "authenticate_toc_by_password",
        {"error": 1, "error_msg": "x", "data": {"toc_account": {"has_password": True}}},
    )
    with pytest.raises(ValueError, match="password-protected"):
        _auth_service(mock).request_otp("081297110640", password="p")


def test_request_otp_wrong_password_and_report_failure():
    mock = MockShopee()
    _otp_routes(mock)
    mock.routes = [r for r in mock.routes if "authenticate_toc_by_password" not in r[1]]
    mock.json("POST", "authenticate_toc_by_password", {"error": 48401003, "error_msg": "bad pw"})
    with pytest.raises(ApiException, match="rejected the password"):
        _auth_service(mock).request_otp("081297110640", password="nope")

    mock = MockShopee()
    _otp_routes(mock)
    mock.routes = [r for r in mock.routes if "shpsec" not in r[1]]
    mock.json("POST", "/v2/shpsec/web/report", {"code": 500, "msg": "err"})
    with pytest.raises(ApiException, match="device-risk"):
        _auth_service(mock).request_otp("081297110640", password="p")


def test_request_otp_captcha_paths():
    mock = MockShopee()
    _otp_routes(mock)
    mock.routes = [r for r in mock.routes if "get_otp_settings" not in r[1]]
    mock.json("POST", "get_otp_settings", {"error": 0, "error_msg": "", "data": {"captcha_required": True}})
    with pytest.raises(ApiException, match="captcha"):
        _auth_service(mock).request_otp("081297110640", password="p")

    mock = MockShopee()
    _otp_routes(mock)
    mock.routes = [r for r in mock.routes if "send_otp" not in r[1]]
    mock.json("POST", "send_otp", {"error": 100, "error_msg": "need captcha"})
    with pytest.raises(ApiException, match="captcha"):
        _auth_service(mock).request_otp("081297110640", password="p")


# ---------------------------------------------------------------- verify_otp
def _verify_routes(mock):
    mock.json("POST", "verify_otp", {"error": 0, "error_msg": "", "data": {"otp_token": "OTP"}})
    mock.json(
        "POST",
        "authenticate_toc_by_otp",
        {"error": 0, "error_msg": "", "data": {"toc_nonce": "NONCE", "toc_account": {"userid": 99}}},
        headers={"set-cookie": "SPC_CLIENTID=SPC1; Path=/"},
    )
    mock.add("GET", "account/login/auth", "", status=302, headers={"location": "/redir1"})
    mock.add("GET", "/redir1", "ok")
    mock.json(
        "POST",
        "MerchantDetect",
        {
            "errorCode": 0,
            "errorMsg": "",
            "data": {"TocUid": 99, "selectMerchant": {"merchantList": [MERCHANT, MERCHANT_BANNED]}},
        },
    )
    return mock


def _challenge(**overrides):
    base = {
        "version": 1,
        "phone_number": "628977110640",
        "device_fingerprint": RISK,
        "risk_token": RISK,
        "cookies": [],
    }
    return {**base, **overrides}


def test_verify_otp_input_validation():
    auth = _auth_service(MockShopee())
    with pytest.raises(ValueError, match="challenge version"):
        auth.verify_otp({"version": 2}, "1234")
    for bad in ("", "12", "12345678901", "12ab", "  "):
        with pytest.raises(ValueError, match="4 to 10 digits"):
            auth.verify_otp(_challenge(), bad)


def test_verify_otp_full_flow_and_headers():
    mock = _verify_routes(MockShopee())
    auth = _auth_service(mock)
    verification = auth.verify_otp(_challenge(), "123456")
    assert verification["version"] == 1
    assert verification["toc_nonce"] == "NONCE"
    assert verification["toc_userid"] == 99
    assert verification["spc_clientid"] == "SPC1"
    assert verification["device_fingerprint"] == RISK
    assert [m["id"] for m in verification["merchants"]] == ["42", "43"]
    assert verification["merchants"][0]["staff_user_id"] == 501

    bodies = mock.bodies("verify_otp")[0]
    assert bodies["phone"] == "(+62) 897 7110 640"
    assert bodies["otp"] == "123456"
    assert bodies["support_session"] is False
    auth_by_otp = mock.bodies("authenticate_toc_by_otp")[0]
    assert auth_by_otp == {"otp_token": "OTP", "security_device_fingerprint": RISK, "is_signup": False}

    login_hop = next(c for c in mock.calls if "account/login/auth" in c["url"])
    assert "spc_clientid=SPC1" in login_hop["url"] and "toc_nonce=NONCE" in login_hop["url"]
    assert any("/redir1" in c["url"] for c in mock.calls)  # redirect followed

    detect = next(c for c in mock.calls if "MerchantDetect" in c["url"])
    assert detect["headers"]["x-merchant-token"] == ""
    assert detect["headers"]["x-merchant-toc-nonce"] == "NONCE"
    assert detect["headers"]["shopee-baggage"] == "PFB=undefined"
    assert "cookie" not in detect["headers"]  # header-only host: no cookies, ever


def test_verify_otp_contract_failures():
    mock = _verify_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "verify_otp" not in r[1]]
    mock.json("POST", "verify_otp", {"error": 0, "error_msg": "", "data": {}})
    with pytest.raises(QmidException, match="no token"):
        _auth_service(mock).verify_otp(_challenge(), "1234")

    mock = _verify_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "authenticate_toc_by_otp" not in r[1]]
    mock.json("POST", "authenticate_toc_by_otp", {"error": 0, "error_msg": "", "data": {}})
    with pytest.raises(QmidException, match="incomplete"):
        _auth_service(mock).verify_otp(_challenge(), "1234")

    mock = _verify_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "MerchantDetect" not in r[1]]
    mock.json(
        "POST",
        "MerchantDetect",
        {"errorCode": 0, "errorMsg": "", "data": {"selectMerchant": {"merchantList": []}}},
    )
    with pytest.raises(QmidException, match="no accessible merchant"):
        _auth_service(mock).verify_otp(_challenge(), "1234")


def test_verify_otp_partner_envelope_errors():
    mock = _verify_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "MerchantDetect" not in r[1]]
    mock.json("POST", "MerchantDetect", {"errorCode": 200020, "errorMsg": "not auth"})
    with pytest.raises(ApiException, match="login again"):
        _auth_service(mock).verify_otp(_challenge(), "1234")

    mock = _verify_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "MerchantDetect" not in r[1]]
    mock.json("POST", "MerchantDetect", {"errorCode": 90004, "errorMsg": "sgw"})
    with pytest.raises(ApiException, match="partner API request failed"):
        _auth_service(mock).verify_otp(_challenge(), "1234")


# ---------------------------------------------------------------- complete_login
def _verification(**overrides):
    merchant = {
        "id": "42",
        "name": "Toko",
        "status": 1,
        "staff_user_id": 501,
        "staff_role": 2,
        "staff_status": 1,
        "is_active": True,
        "is_banned": False,
        "is_current_login_user": True,
    }
    base = {
        "version": 1,
        "toc_nonce": "NONCE",
        "toc_userid": 99,
        "spc_clientid": "SPC1",
        "device_fingerprint": RISK,
        "cookies": [],
        "merchants": [merchant],
        "verified_at": 1,
    }
    return {**base, **overrides}


def _complete_routes(mock, jwt=JWT):
    mock.add("GET", "/authenticate/login/token/", "page")
    mock.json("POST", "login_toc", {"error": 0, "error_msg": "", "data": {"nonce": "CODE"}})
    mock.add(
        "GET",
        "account/login/tob/auth",
        "ok",
        headers={"set-cookie": f"{C.LIVE_TOKEN_COOKIE}={jwt}; Domain=partner.shopee.co.id; Path=/"},
    )
    mock.json(
        "POST",
        "GetUserInfo",
        {
            "errorCode": 0,
            "errorMsg": "",
            "data": {
                "merchantId": 42,
                "merchantName": "Toko",
                "store_id": 7,
                "tobUserId": 501,
                "tocUid": 99,
                "userName": "crew",
                "language": "id",
                "shopeepay_service_status": 1,
            },
        },
    )
    return mock


def _store_feed(*store_ids):
    rows = [{"storeId": i, "storeName": f"s{i}", "status": 1} for i in store_ids]
    return (200, {"code": 0, "msg": "ok", "data": {"list": rows}})


def test_complete_login_full_session():
    mock = _complete_routes(MockShopee())
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7)), auth_transport=mock.transport, backoff_base=0
    )
    session = sp.auth.complete_login(_verification())
    assert session["version"] == 1
    assert session["token"] == "B:login-token"
    assert session["account_id"] == "501"
    assert session["merchant"]["id"] == "42"
    assert session["switch_credential"] == {
        "toc_nonce": "NONCE",
        "spc_clientid": "SPC1",
        "device_fingerprint": RISK,
    }
    assert [s["id"] for s in session["stores"]] == ["7"]
    assert session["store_id"] == "7"  # profile store wins
    assert session["profile"]["user_name"] == "crew"
    assert session["expires_at"] == 9999999999000
    assert any(c["name"] == C.LIVE_TOKEN_COOKIE for c in session["cookies"])
    # data client now carries the minted token
    assert sp.client.payment_metadata()["token"] == "B:login-token"

    token_page = next(c for c in mock.calls if "/authenticate/login/token/" in c["url"])
    assert "tob_userid=501" in token_page["url"] and "client_id=5" in token_page["url"]
    toc = mock.bodies("login_toc")[0]
    assert toc == {"toc_nonce": "NONCE", "tob_userid": 501, "security_device_fingerprint": RISK}
    userinfo = next(c for c in mock.calls if "GetUserInfo" in c["url"])
    assert userinfo["headers"]["x-merchant-token"] == "B:login-token"
    assert "cookie" not in userinfo["headers"]
    sp.close()


def test_complete_login_merchant_selection_and_guards():
    mock = _complete_routes(MockShopee())
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7, 8)), auth_transport=mock.transport, backoff_base=0
    )
    second = {
        "id": "43",
        "name": "C2",
        "status": 1,
        "staff_user_id": 502,
        "staff_role": 2,
        "staff_status": 1,
        "is_active": True,
        "is_banned": False,
        "is_current_login_user": False,
    }
    first = {**_verification()["merchants"][0], "is_current_login_user": False}
    two = _verification(merchants=[first, second])
    with pytest.raises(ValueError, match="merchantId is required"):
        sp.auth.complete_login(two)
    session = sp.auth.complete_login(two, merchant_id="42")
    assert session["merchant"]["id"] == "42"
    assert session["store_id"] == "7"  # profile store, not first
    with pytest.raises(ValueError, match="not accessible"):
        sp.auth.complete_login(two, merchant_id="99")
    banned = _verification(merchants=[{**two["merchants"][0], "is_active": False}])
    with pytest.raises(QmidException, match="inactive or banned"):
        sp.auth.complete_login(banned, merchant_id="42")
    with pytest.raises(ValueError, match="verification version"):
        sp.auth.complete_login({"version": 2})
    sp.close()

    with pytest.raises(QmidException, match="data client"):
        AuthService(transport=mock.transport).complete_login(_verification())


def test_complete_login_token_and_profile_mismatch():
    mock = _complete_routes(MockShopee(), jwt=_jwt({"token": "B:x", "userid": 999}))
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7)), auth_transport=mock.transport, backoff_base=0
    )
    with pytest.raises(QmidException, match="different merchant"):
        sp.auth.complete_login(_verification())
    sp.close()

    mock = _complete_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "GetUserInfo" not in r[1]]
    mock.json(
        "POST",
        "GetUserInfo",
        {"errorCode": 0, "errorMsg": "", "data": {"merchantId": 777, "merchantName": "?"}},
    )
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7)), auth_transport=mock.transport, backoff_base=0
    )
    with pytest.raises(QmidException, match="different merchant"):
        sp.auth.complete_login(_verification())
    sp.close()

    mock = _complete_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "login_toc" not in r[1]]
    mock.json("POST", "login_toc", {"error": 0, "error_msg": "", "data": {}})
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7)), auth_transport=mock.transport, backoff_base=0
    )
    with pytest.raises(QmidException, match="no authorization code"):
        sp.auth.complete_login(_verification())
    sp.close()


# ---------------------------------------------------------------- login_with_otp
def test_login_with_otp_complete_and_selection_required():
    mock = _verify_routes(_complete_routes(MockShopee()))
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7)), auth_transport=mock.transport, backoff_base=0
    )
    # two merchants, one usable+current -> resolves straight to complete
    outcome = sp.auth.login_with_otp(_challenge(), "123456")
    assert outcome["status"] == "complete"
    assert outcome["session"]["merchant"]["id"] == "42"
    sp.close()

    mock = _verify_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "MerchantDetect" not in r[1]]
    mock.json(
        "POST",
        "MerchantDetect",
        {
            "errorCode": 0,
            "errorMsg": "",
            "data": {
                "selectMerchant": {
                    "merchantList": [MERCHANT, {**MERCHANT, "merchantId": 44, "staffTobUid": 504}]
                }
            },
        },
    )
    auth = _auth_service(mock)
    outcome = auth.login_with_otp(_challenge(), "123456")
    assert outcome["status"] == "merchant-selection-required"
    assert [m["id"] for m in outcome["merchants"]] == ["42", "44"]
    assert outcome["verification"]["toc_nonce"] == "NONCE"
    auth.close()


# ---------------------------------------------------------------- refresh / select / probe
def _session(**overrides):
    merchant = {
        "id": "42",
        "name": "Toko",
        "status": 1,
        "staff_user_id": 501,
        "staff_role": 2,
        "staff_status": 1,
        "is_active": True,
        "is_banned": False,
        "is_current_login_user": True,
    }
    base = {
        "version": 1,
        "cookies": [],
        "token": "B:login-token",
        "account_id": "501",
        "merchant": merchant,
        "merchants": [merchant],
        "switch_credential": {"toc_nonce": "NONCE", "spc_clientid": "SPC1", "device_fingerprint": RISK},
        "stores": [{"id": "7", "name": "s7", "status": 1}],
        "store_id": "7",
        "profile": {"merchant_id": "42", "merchant_name": "Toko"},
        "created_at": 1,
        "expires_at": None,
    }
    return {**base, **overrides}


def _refresh_routes(mock, *, alive=True, jwt=JWT2):
    mock.json(
        "POST",
        "login_status",
        {"error": 0 if alive else C.NOT_LOGIN_CODE, "error_msg": "" if alive else "not login"},
    )
    if alive:
        _complete_routes(mock, jwt=jwt)
    return mock


def test_refresh_session_renews_token():
    mock = _refresh_routes(MockShopee())
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7)), auth_transport=mock.transport, backoff_base=0
    )
    session = sp.auth.refresh_session(_session())
    assert session["token"] == "B:renewed-token"
    assert session["expires_at"] == 9999999999000
    assert sp.client.payment_metadata()["token"] == "B:renewed-token"
    status_call = mock.bodies("login_status")[0]
    assert status_call == {}
    sp.close()


def test_refresh_session_dead_or_no_credential():
    mock = _refresh_routes(MockShopee(), alive=False)
    with pytest.raises(ApiException, match="expired; log in again") as exc:
        _auth_service(mock).refresh_session(_session())
    assert exc.value.code == str(C.NOT_LOGIN_CODE)

    mock = MockShopee()
    session = _session(switch_credential=None)
    with pytest.raises(QmidException, match="predates silent renewal"):
        _auth_service(mock).refresh_session(session)
    with pytest.raises(ValueError, match="session version"):
        _auth_service(mock).refresh_session({"version": 9})


def test_select_merchant_switch_and_guards():
    mock = _complete_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "GetUserInfo" not in r[1]]
    mock.json(
        "POST",
        "GetUserInfo",
        {"errorCode": 0, "errorMsg": "", "data": {"merchantId": 44, "merchantName": "C2", "tobUserId": 504}},
    )
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(9)), auth_transport=mock.transport, backoff_base=0
    )
    second = {
        "id": "44",
        "name": "",
        "status": 1,
        "staff_user_id": 504,
        "staff_role": 2,
        "staff_status": 1,
        "is_active": True,
        "is_banned": False,
        "is_current_login_user": False,
    }
    session = _session(merchants=[_session()["merchant"], second])
    assert sp.auth.select_merchant(session, "42") == session  # no-op when active

    mock2 = _complete_routes(MockShopee(), jwt=_jwt({"token": "B:m44", "userid": 504}))
    mock2.routes = [r for r in mock2.routes if "GetUserInfo" not in r[1]]
    mock2.json(
        "POST",
        "GetUserInfo",
        {"errorCode": 0, "errorMsg": "", "data": {"merchantId": 44, "merchantName": "C2", "tobUserId": 504}},
    )
    sp2 = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(9)), auth_transport=mock2.transport, backoff_base=0
    )
    switched = sp2.auth.select_merchant(session, "44")
    assert switched["merchant"]["id"] == "44"
    assert switched["merchant"]["name"] == "C2"  # filled from profile
    assert switched["token"] == "B:m44"
    assert switched["account_id"] == "504"
    assert [s["id"] for s in switched["stores"]] == ["9"]
    assert switched["store_id"] == "9"  # single store auto-picked
    toc = mock2.bodies("login_toc")[0]
    assert toc["tob_userid"] == 504
    sp.close()
    sp2.close()

    auth = _auth_service(MockShopee())
    with pytest.raises(ValueError, match="not accessible"):
        auth.select_merchant(session, "99")
    banned = {**second, "is_active": False}
    with pytest.raises(ValueError, match="inactive or banned"):
        auth.select_merchant(_session(merchants=[_session()["merchant"], banned]), "44")
    with pytest.raises(QmidException, match="cannot switch"):
        auth.select_merchant(
            _session(switch_credential=None, merchants=[_session()["merchant"], second]), "44"
        )
    with pytest.raises(QmidException, match="data client"):
        AuthService(transport=MockShopee().transport).select_merchant(session, "44")


def test_select_store_pure():
    auth = _auth_service(MockShopee())
    session = _session(stores=[{"id": "7"}, {"id": "8"}], store_id="7")
    assert auth.select_store(session, "8")["store_id"] == "8"
    with pytest.raises(ValueError, match="not in the merchant's store list"):
        auth.select_store(session, "9")
    auth.close()


def test_account_session_alive_and_session_token():
    mock = _refresh_routes(MockShopee(), alive=True)
    auth = _auth_service(mock)
    assert auth.account_session_alive(_session()) is True
    auth.close()
    mock = _refresh_routes(MockShopee(), alive=False)
    auth = _auth_service(mock)
    assert auth.account_session_alive(_session()) is False
    auth.close()

    auth = _auth_service(MockShopee())
    session = _session(cookies=[{"name": C.LIVE_TOKEN_COOKIE, "value": JWT, "domain": "d", "path": "/"}])
    assert auth.session_token(session) == "B:login-token"
    with pytest.raises(QmidException, match="did not return"):
        auth.session_token(_session())
    auth.close()


# ---------------------------------------------------------------- transport edges
def test_transport_retries_then_succeeds_and_exhausts():
    calls = {"n": 0}

    def flaky(request):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("down")
        return httpx.Response(200, json={"code": 0, "msg": "ok", "data": {"riskToken": RISK}})

    auth = AuthService(transport=httpx.MockTransport(flaky), backoff_base=0)
    assert auth._device_fingerprint(None) == RISK
    assert calls["n"] == 2

    def dead(request):
        raise httpx.ConnectError("down")

    auth = AuthService(transport=httpx.MockTransport(dead), backoff_base=0, max_retries=1)
    with pytest.raises(httpx.ConnectError):
        auth._device_fingerprint(None)


def test_redirect_edges():
    mock = MockShopee()
    mock.add("GET", "/a", "", status=302)  # no location
    with pytest.raises(ApiException, match="no.*location"):
        _auth_service(mock)._follow_get("https://x.test/a")

    mock = MockShopee()
    mock.add("GET", "/loop", "", status=302, headers={"location": "/loop"})
    with pytest.raises(ApiException, match="redirect limit"):
        _auth_service(mock)._follow_get("https://x.test/loop")


def test_http_and_json_edges():
    mock = MockShopee()
    mock.add("GET", "/login", "ok")
    mock.json("POST", "/v2/shpsec/web/report", {"code": 0, "msg": "ok", "data": {"riskToken": RISK}})
    mock.add("POST", "check_password_migrate", "not-json{{")
    with pytest.raises(ApiException, match="invalid JSON"):
        _auth_service(mock).request_otp("081297110640", password="p")

    mock = MockShopee()
    mock.add("GET", "/login", "ok")
    mock.json("POST", "/v2/shpsec/web/report", {"code": 0, "msg": "ok", "data": {"riskToken": RISK}})
    mock.json("POST", "check_password_migrate", {"error": 0, "error_msg": "", "data": [1, 2]})
    with pytest.raises(ApiException, match="non-object data"):
        _auth_service(mock).request_otp("081297110640", password="p")

    mock = MockShopee()
    mock.add("GET", "/login", "ok")
    mock.json("POST", "/v2/shpsec/web/report", {"code": 0, "msg": "ok", "data": {"riskToken": RISK}})
    mock.json("POST", "check_password_migrate", {"error": 7, "error_msg": "boom"}, status=500)
    with pytest.raises(ApiException, match="boom") as exc:
        _auth_service(mock).request_otp("081297110640", password="p")
    assert exc.value.http_status == 500
    assert exc.value.code == "7"


def test_jar_domain_preference_and_snapshot_shape():
    auth = _auth_service(MockShopee())
    auth._web.cookies.set("k", "v1", domain="a.test", path="/")
    auth._web.cookies.set("k", "v2", domain="b.test", path="/")
    assert auth._jar_get("k", "https://b.test/x") == "v2"
    assert auth._jar_get("k", "https://z.test/") in ("v1", "v2")  # fallback: some value
    assert auth._jar_get("missing", "https://b.test/") is None
    snap = auth._snapshot()
    assert {"name", "value", "domain", "path", "secure"} <= set(snap[0])
    auth._restore([])
    assert auth._snapshot() == []
    auth.close()


def test_facade_auth_wiring_and_close():
    sp = ShopeePayPartner(token="B:t")
    assert sp.auth._data is sp.client
    sp.close()


# ---------------------------------------------------------------- coverage edges
def test_credential_without_userid_is_unreadable():
    cookies = [{"name": C.LIVE_TOKEN_COOKIE, "value": _jwt({"token": "B:x"}), "domain": "d", "path": "/"}]
    with pytest.raises(QmidException, match="unreadable"):
        A.read_merchant_credential(cookies)


def test_verify_otp_without_spc_cookie():
    mock = MockShopee()
    mock.json("POST", "verify_otp", {"error": 0, "error_msg": "", "data": {"otp_token": "OTP"}})
    mock.json(
        "POST",
        "authenticate_toc_by_otp",
        {"error": 0, "error_msg": "", "data": {"toc_nonce": "N", "toc_account": {"userid": 1}}},
    )
    with pytest.raises(QmidException, match="no client session id"):
        _auth_service(mock).verify_otp(_challenge(), "1234")


def test_verify_otp_skips_junk_merchant_rows():
    mock = MockShopee()
    mock.json("POST", "verify_otp", {"error": 0, "error_msg": "", "data": {"otp_token": "OTP"}})
    mock.json(
        "POST",
        "authenticate_toc_by_otp",
        {"error": 0, "error_msg": "", "data": {"toc_nonce": "N", "toc_account": {"userid": 1}}},
        headers={"set-cookie": "SPC_CLIENTID=S; Path=/"},
    )
    mock.add("GET", "account/login/auth", "ok")
    mock.json(
        "POST",
        "MerchantDetect",
        {
            "errorCode": 0,
            "errorMsg": "",
            "data": {
                "selectMerchant": {
                    "merchantList": ["junk", None, {"merchantId": "x"}, {"merchantId": 1}, MERCHANT]
                }
            },
        },
    )
    verification = _auth_service(mock).verify_otp(_challenge(), "1234")
    assert [m["id"] for m in verification["merchants"]] == ["42"]


def test_complete_login_requested_store_and_no_stores():
    mock = _complete_routes(MockShopee())
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed(7, 8)), auth_transport=mock.transport, backoff_base=0
    )
    session = sp.auth.complete_login(_verification(), store_id="8")
    assert session["store_id"] == "8"  # explicit request wins over profile
    sp.close()

    mock = _complete_routes(MockShopee())
    sp = ShopeePayPartner(
        transport=FakeHttpClient(_store_feed()), auth_transport=mock.transport, backoff_base=0
    )
    session = sp.auth.complete_login(_verification())
    assert session["stores"] == []
    assert session["store_id"] is None
    sp.close()


def test_non_object_json_and_partner_data_edges():
    mock = MockShopee()
    mock.add("GET", "/login", "ok")
    mock.json("POST", "/v2/shpsec/web/report", {"code": 0, "msg": "ok", "data": {"riskToken": RISK}})
    mock.json("POST", "check_password_migrate", [1, 2])
    with pytest.raises(ApiException, match="non-object JSON"):
        _auth_service(mock).request_otp("081297110640")

    mock = _verify_routes(MockShopee())
    mock.routes = [r for r in mock.routes if "MerchantDetect" not in r[1]]
    mock.json("POST", "MerchantDetect", {"errorCode": 0, "errorMsg": "", "data": ["x"]})
    with pytest.raises(ApiException, match="non-object data"):
        _auth_service(mock).verify_otp(_challenge(), "1234")
