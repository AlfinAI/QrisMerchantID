"""Package metadata, top-level exports & facade wiring."""

import qrismerchantid
from qrismerchantid import GoPayMerchant


def test_version_and_exports():
    assert qrismerchantid.__version__ == "0.1.0"
    assert qrismerchantid.GoPayMerchant is GoPayMerchant
    assert set(qrismerchantid.__all__) == {"ApiException", "GoPayMerchant", "QmidException", "__version__"}


def test_api_exception_attributes():
    err = qrismerchantid.ApiException("boom", "200020", {"ok": False}, 401)
    assert isinstance(err, qrismerchantid.QmidException)
    assert str(err) == "boom"
    assert err.code == "200020"
    assert err.payload == {"ok": False}
    assert err.http_status == 401


def test_gopay_facade_shares_one_client():
    gopay = GoPayMerchant()
    for name in ("auth", "users", "merchants", "transactions", "payouts"):
        assert getattr(gopay, name)._client is gopay.client, name
    gopay.client.close()
