"""Package metadata & top-level exports."""

import qrismerchantid


def test_version_and_exports():
    assert qrismerchantid.__version__ == "0.1.0"
    assert qrismerchantid.QmidException.__name__ == "QmidException"
    assert qrismerchantid.ApiException.__name__ == "ApiException"
    assert set(qrismerchantid.__all__) == {"ApiException", "QmidException", "__version__"}


def test_api_exception_attributes():
    err = qrismerchantid.ApiException("boom", "200020", {"ok": False}, 401)
    assert isinstance(err, qrismerchantid.QmidException)
    assert str(err) == "boom"
    assert err.code == "200020"
    assert err.payload == {"ok": False}
    assert err.http_status == 401
