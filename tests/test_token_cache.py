"""token_cache: session + pending-OTP round trips (offline, tmp files)."""

import json
import time

from qrismerchantid.core import token_cache

SESSION = {"access_token": "tok", "refresh_token": "ref", "dbl_enabled": True}


def test_save_load_round_trip_without_expiry(tmp_path):
    p = tmp_path / "session.json"
    token_cache.save(p, SESSION)
    assert token_cache.load(p) == SESSION  # GoBiz sessions carry no server expiry


def test_load_missing_invalid_or_tokenless_returns_none(tmp_path):
    assert token_cache.load(tmp_path / "nope.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert token_cache.load(bad) is None
    bad.write_text(json.dumps(["not", "a", "dict"]))
    assert token_cache.load(bad) is None
    for session in ({}, {"access_token": ""}, {"refresh_token": "r"}):
        bad.write_text(json.dumps(session))
        assert token_cache.load(bad) is None


def test_expires_at_uses_absolute_epoch_not_duration(tmp_path):
    p = tmp_path / "s.json"
    token_cache.save(p, {**SESSION, "expires_at": int(time.time()) + 3600})
    assert token_cache.load(p) is not None
    token_cache.save(p, {**SESSION, "expires_at": int(time.time()) - 1})
    assert token_cache.load(p) is None
    # a *duration-looking* small value is long past as an epoch -> expired
    token_cache.save(p, {**SESSION, "expires_at": 3600})
    assert token_cache.load(p) is None
    token_cache.save(p, {**SESSION, "expires_at": "not-a-number"})
    assert token_cache.load(p) is None


def test_pending_otp_round_trip_and_expiry(tmp_path):
    p = tmp_path / "otp.json"
    otp = {"otp_token": "ot-1", "expires_at": int(time.time()) + 720}
    token_cache.save_pending_otp(p, otp)
    assert token_cache.load_pending_otp(p) == otp

    assert token_cache.load_pending_otp(tmp_path / "missing.json") is None
    p.write_text(json.dumps({"nope": True}))
    assert token_cache.load_pending_otp(p) is None

    token_cache.save_pending_otp(p, {**otp, "expires_at": int(time.time()) - 5})
    assert token_cache.load_pending_otp(p) is None
    token_cache.save_pending_otp(p, {**otp, "expires_at": "garbage"})
    assert token_cache.load_pending_otp(p) is None
    # ignore_expiry=True lets the server judge validity instead of a local guess
    assert token_cache.load_pending_otp(p, ignore_expiry=True)["otp_token"] == "ot-1"
