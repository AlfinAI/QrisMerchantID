"""Programmatic OTP login for ShopeePay (B2): request → verify → complete.

Ports ``ShopeeAuthClient`` + the login half of ``ShopeeProvider`` (merchantid
``src/providers/shopee/authClient.ts`` + ``shopeeProvider.ts``). Unlike the
stateful TS provider, this service is stateless: every step takes a plain
JSON-serializable dict (challenge / verification / session) and returns the
next one, so gateways persist them with ``json.dump`` between runs. Cookies
travel inside those dicts as ``{name, value, domain, path}``; the secure flag
is recorded but cannot be restored (httpx limitation) — sessions are
revalidated server-side via ``login_status`` anyway, so this is cosmetic.

Two HTTP clients are used deliberately: the web client keeps cookies for the
passport/partner-web hosts, while the API client stays cookie-free because the
partner API host authenticates header-only — attaching cookies there makes the
server reject calls with ``200020`` (merchantid ``httpClient.ts``).

Error mapping: account/partner envelope failures → :class:`ApiException` (with
the provider code); bad caller input (phone, OTP shape, unknown ids, version
mismatch) → :class:`ValueError`; dead-end state (no renewal credential,
missing/unreadable token cookie, contract violations) → :class:`QmidException`.
Transport errors retry with backoff; HTTP errors never retry.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
import time
import urllib.parse
import uuid
from typing import Any

import httpx

from qrismerchantid.core.exceptions import ApiException, QmidException
from qrismerchantid.shopee import constants as C
from qrismerchantid.shopee.client import ShopeePayClient
from qrismerchantid.shopee.stores import StoresService

_OTP_RE = re.compile(r"^\d{4,10}$")
_AUTH_WORDS = re.compile(r"token|auth|login|session", re.IGNORECASE)
_CAPTCHA_WORDS = re.compile(r"captcha", re.IGNORECASE)
_PASSWORD_REQUIRED = "This Shopee account is password-protected; supply the password to receive an OTP"
_MAX_REDIRECTS = 5


def parse_id_mobile(number: str) -> dict[str, str]:
    """Parse free-form input into Indonesian mobile forms (port of ``parseIndonesianMobile``).

    Accepts ``62…``, ``+62…``, ``08…``, bare ``8…`` (even ``00 62 0 8…``) with
    spaces/dashes/dots/parens. Returns ``{country_code, subscriber, national,
    e164}``. Raises :class:`ValueError` when the value cannot be an Indonesian
    mobile (subscriber must start with ``8`` and run 9–13 digits).
    """
    digits = re.sub(r"\D+", "", number or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("62"):
        digits = digits[2:]
    digits = digits.lstrip("0")
    if not digits.startswith("8") or not 9 <= len(digits) <= 13:
        raise ValueError("Enter a valid Indonesian mobile number")
    return {"country_code": "62", "subscriber": digits, "national": f"0{digits}", "e164": f"62{digits}"}


def format_phone_for_verification(e164: str) -> str:
    """Render e164 the way ``verify_otp`` wants it: ``(+62) 897 7110 640``.

    The endpoint rejects the compact e164 form.
    """
    subscriber = e164[2:] if e164.startswith("62") else e164
    groups = [subscriber[0:3], subscriber[3:7], subscriber[7:]]
    return f"(+62) {' '.join(g for g in groups if g)}"


def hash_shopee_password(password: str) -> str:
    """Wire transform for account passwords: ``sha256Hex(md5Hex(password))`` (UTF-8)."""
    return hashlib.sha256(hashlib.md5(password.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()


def usable_merchants(merchants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merchants a login can actually select: active and not banned."""
    return [m for m in merchants if m.get("is_active") is True and m.get("is_banned") is not True]


def resolve_single_merchant(merchants: list[dict[str, Any]]) -> dict[str, Any] | None:
    """The one merchant a login can pick without a human (``None`` if ambiguous).

    Prefers the current-login merchant, else the sole usable one.
    """
    usable = usable_merchants(merchants)
    current = [m for m in usable if m.get("is_current_login_user") is True]
    if len(current) == 1:
        return current[0]
    if len(usable) == 1:
        return usable[0]
    return None


def read_merchant_credential(cookies: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract the inner merchant token from the signed dashboard JWT cookie.

    Returns ``{token, account_id, business_id?, expires_at?}`` (``expires_at``
    is epoch millis, like every other timestamp here). NOTE: ``business_id`` is
    the SSO constant (``"1"``), never the merchant id — do not validate with it.
    """
    jwt = next((c.get("value", "") for c in cookies if c.get("name") == C.LIVE_TOKEN_COOKIE), "")
    if not jwt:
        raise QmidException("Shopee login did not return a merchant session token")
    try:
        segments = jwt.split(".")
        if len(segments) != 3 or not segments[1]:
            raise ValueError("Invalid JWT")
        padded = segments[1] + "=" * (-len(segments[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("token"), str):
            raise ValueError("Missing merchant token")
        account_id = payload.get("userid")
        account_id = str(account_id) if isinstance(account_id, (str, int)) else ""
        if not account_id or not payload["token"]:
            raise ValueError("Missing account id")
        business_id = payload.get("businessId")
        business_id = str(business_id) if isinstance(business_id, (str, int)) else None
        exp = payload.get("exp")
        expires_at = exp * 1000 if isinstance(exp, (int, float)) and exp == exp else None
        credential: dict[str, Any] = {"token": payload["token"], "account_id": account_id}
        if business_id is not None:
            credential["business_id"] = business_id
        if expires_at is not None:
            credential["expires_at"] = int(expires_at)
        return credential
    except (ValueError, UnicodeError, json.JSONDecodeError) as cause:
        raise QmidException("Shopee returned an unreadable merchant session token") from cause


def partner_state() -> str:
    """SSO ``state`` param: partner root carrying business_next/state/client_id."""
    login_auth = urllib.parse.quote(C.PARTNER_BASE_URL + C.ENDPOINT_PARTNER_LOGIN_AUTH, safe="")
    base = urllib.parse.quote(C.PARTNER_BASE_URL, safe="")
    return (
        f"{C.PARTNER_BASE_URL}/?business_next={login_auth}&business_state={base}"
        f"&business_client_id={C.BUSINESS_CLIENT_ID}"
    )


def login_referer() -> str:
    """Referer the passport SPA presents on authentication calls (anti-fraud context)."""
    state = urllib.parse.quote(partner_state(), safe="")
    auth = urllib.parse.quote(C.PARTNER_BASE_URL + C.ENDPOINT_ACCOUNT_LOGIN, safe="")
    return (
        f"{C.ACCOUNT_BASE_URL}{C.ENDPOINT_AUTHENTICATE_LOGIN}?lang={C.DEFAULT_LANGUAGE}"
        f"&should_hide_back=true&state={state}&client_id={C.ACCOUNT_CLIENT_ID}&next={auth}"
    )


def _now_ms() -> int:
    return int(time.time() * 1000)


def _num_or(value: Any, fallback: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else fallback


class AuthService:
    """Password + OTP login. Successful logins set the token on the data client.

    Args:
        transport: optional ``httpx.BaseTransport`` both internal clients run
            on (pass ``httpx.MockTransport`` in tests to stay offline).
        data_client: the :class:`ShopeePayClient` logins mint tokens for.
            Required by :meth:`complete_login`/:meth:`select_merchant` (store
            discovery runs through it); a login-only service may omit it.
        timeout: seconds for the internally created httpx clients.
        max_retries: transport-error retries (connect/DNS/timeout) — HTTP
            error statuses are never retried.
        backoff_base: exponential backoff base in seconds.
        language/timezone: locale sent on account + partner calls.
        user_agent: ``User-Agent`` header.
        device_report: default fraud-SDK telemetry blob (captured from YOUR
            own browser — see ``docs/shopee/device-risk.md``). Per-call
            overrides win. Without any blob the issuer returns a degraded
            risk token and the OTP is silently suppressed.
    """

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        data_client: ShopeePayClient | None = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        backoff_base: float = 0.5,
        language: str = C.DEFAULT_LANGUAGE,
        timezone: str = C.DEFAULT_TIMEZONE,
        user_agent: str = C.USER_AGENT,
        device_report: str | None = None,
    ) -> None:
        self._web = httpx.Client(transport=transport, timeout=timeout)
        self._api = httpx.Client(transport=transport, timeout=timeout)
        self._data = data_client
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._language = language
        self._timezone = timezone
        self._user_agent = user_agent
        self._device_report = device_report

    def close(self) -> None:
        """Close both internally created httpx clients."""
        self._web.close()
        self._api.close()

    # ------------------------------------------------------------------ public
    def request_otp(
        self,
        phone_number: str,
        password: str | None = None,
        channel: int | None = None,
        device_report: str | None = None,
    ) -> dict[str, Any]:
        """Run the 7-call OTP request chain; return the serializable challenge.

        Args:
            phone_number: free-form Indonesian mobile (``08…``/``628…``/…).
            password: required when the account is password-protected.
            channel: 1 SMS, 2 voice, 3 WhatsApp, 4 email, 5 Zalo (defaults to
                the server's suggestion).
            device_report: per-call telemetry blob (overrides the default).

        Returns ``{version, phone_number, channel, available_channels,
        device_fingerprint, risk_token, has_password, cookies, requested_at}``.
        """
        phone = parse_id_mobile(phone_number)["e164"]
        self._web.cookies.clear()
        self._bootstrap()
        fingerprint = self._device_fingerprint(device_report or self._device_report)
        self._account(C.ENDPOINT_CHECK_PASSWORD_MIGRATE, {"phone": phone}, fingerprint)
        self._check_account_exists(phone, password, fingerprint)
        has_password = self._authenticate_by_password(phone, password, fingerprint)
        settings = self._account(
            C.ENDPOINT_OTP_SETTINGS,
            {
                "operation": C.OTP_OPERATION,
                "phone": phone,
                "security_device_fingerprint": fingerprint,
                "support_session": False,
                "supported_channels": list(C.OTP_CHANNELS),
            },
            fingerprint,
        )
        available = [c for c in settings.get("available_channel_list", []) if isinstance(c, int)]
        default_channel = settings.get("default_channel")
        resolved = channel if channel is not None else _num_or(default_channel, C.DEFAULT_OTP_CHANNEL)
        if available and resolved not in available:
            raise ValueError("Requested Shopee OTP channel is unavailable")
        self._account(
            C.ENDPOINT_SEND_OTP,
            {
                "operation": C.OTP_OPERATION,
                "phone": phone,
                "security_device_fingerprint": fingerprint,
                "support_session": False,
                "supported_channels": list(C.SEND_OTP_CHANNELS),
                "channel": resolved,
                "captcha_signature": "",
            },
            fingerprint,
        )
        return {
            "version": 1,
            "phone_number": phone,
            "channel": resolved,
            "available_channels": available,
            "device_fingerprint": fingerprint,
            "risk_token": fingerprint,
            "has_password": has_password,
            "cookies": self._snapshot(),
            "requested_at": _now_ms(),
        }

    def verify_otp(self, challenge: dict[str, Any], otp: str) -> dict[str, Any]:
        """Verify the code; return the serializable verification (multi-merchant aware).

        Returns ``{version, toc_nonce, toc_userid, spc_clientid,
        device_fingerprint, cookies, merchants, verified_at}``. Reusable for
        :meth:`complete_login` without a second OTP.
        """
        if challenge.get("version") != 1:
            raise ValueError("Unsupported Shopee OTP challenge version")
        code = otp.strip()
        if not _OTP_RE.match(code):
            raise ValueError("Shopee OTP must contain 4 to 10 digits")
        fingerprint = str(challenge["device_fingerprint"])
        self._restore(challenge.get("cookies", []))
        verified = self._account(
            C.ENDPOINT_VERIFY_OTP,
            {
                "operation": C.OTP_OPERATION,
                "otp": code,
                "phone": format_phone_for_verification(str(challenge["phone_number"])),
                "security_device_fingerprint": fingerprint,
                "support_session": False,
            },
            fingerprint,
        )
        otp_token = verified.get("otp_token")
        if not otp_token:
            raise QmidException("Shopee OTP verification returned no token")
        authenticated = self._account(
            C.ENDPOINT_AUTHENTICATE_BY_OTP,
            {
                "otp_token": otp_token,
                "security_device_fingerprint": fingerprint,
                "is_signup": False,
            },
            fingerprint,
        )
        toc_nonce = authenticated.get("toc_nonce")
        toc_account = authenticated.get("toc_account", {})
        toc_userid = toc_account.get("userid") if isinstance(toc_account, dict) else None
        if not toc_nonce or not isinstance(toc_userid, int) or isinstance(toc_userid, bool):
            raise QmidException("Shopee OTP authentication returned an incomplete account session")
        spc_clientid = self._jar_get(C.CLIENT_ID_COOKIE, C.ACCOUNT_BASE_URL)
        if not spc_clientid:
            raise QmidException("Shopee authentication returned no client session id")
        login_url = (
            f"{C.PARTNER_BASE_URL}{C.ENDPOINT_ACCOUNT_LOGIN}?lang={self._language}"
            f"&spc_clientid={urllib.parse.quote(spc_clientid, safe='')}"
            f"&state={urllib.parse.quote(partner_state(), safe='')}"
            f"&toc_nonce={urllib.parse.quote(str(toc_nonce), safe='')}"
        )
        self._follow_get(login_url)
        detected = self._partner(C.ENDPOINT_MERCHANT_DETECT, {}, toc_nonce=str(toc_nonce))
        select = detected.get("selectMerchant", {})
        raw_list = select.get("merchantList", []) if isinstance(select, dict) else []
        merchants = [m for m in (_normalize_merchant(r) for r in raw_list) if m is not None]
        if not merchants:
            raise QmidException("The Shopee account has no accessible merchant")
        return {
            "version": 1,
            "toc_nonce": toc_nonce,
            "toc_userid": toc_userid,
            "spc_clientid": spc_clientid,
            "device_fingerprint": fingerprint,
            "cookies": self._snapshot(),
            "merchants": merchants,
            "verified_at": _now_ms(),
        }

    def complete_login(
        self,
        verification: dict[str, Any],
        merchant_id: str | None = None,
        store_id: str | None = None,
    ) -> dict[str, Any]:
        """Finish the login: SSO exchange → token → profile → stores → session.

        Also sets the minted token on the data client. Returns the persistable
        session ``{version, cookies, token, account_id, merchant, merchants,
        switch_credential, stores, store_id?, profile, created_at,
        expires_at?}``. Raises :class:`QmidException` without a data client.
        """
        data = self._require_data_client()
        if verification.get("version") != 1:
            raise ValueError("Unsupported Shopee OTP verification version")
        self._restore(verification.get("cookies", []))
        merchant, credential = self._complete_base(verification, merchant_id)
        profile = self._get_profile(credential["token"], merchant["id"])
        data.set_token(credential["token"])
        stores = StoresService(data).list_stores()
        chosen_store = _choose_store_id(stores, store_id, profile.get("store_id"))
        return {
            "version": 1,
            "cookies": self._snapshot(),
            "token": credential["token"],
            "account_id": credential["account_id"],
            "merchant": {**merchant, "name": merchant["name"] or profile["merchant_name"]},
            "merchants": [dict(m) for m in verification["merchants"]],
            "switch_credential": {
                "toc_nonce": verification["toc_nonce"],
                "spc_clientid": verification["spc_clientid"],
                "device_fingerprint": verification["device_fingerprint"],
            },
            "stores": stores,
            "store_id": chosen_store,
            "profile": profile,
            "created_at": _now_ms(),
            "expires_at": credential.get("expires_at"),
        }

    def login_with_otp(
        self,
        challenge: dict[str, Any],
        otp: str,
        merchant_id: str | None = None,
        store_id: str | None = None,
    ) -> dict[str, Any]:
        """Verify + complete in one call (when the merchant is unambiguous).

        Returns ``{"status": "complete", "session"}``, or — when several usable
        merchants exist and none was picked — ``{"status":
        "merchant-selection-required", "verification", "merchants"}`` so a human
        can choose and finish via :meth:`complete_login` (no second OTP).
        """
        verification = self.verify_otp(challenge, otp)
        if merchant_id is None and resolve_single_merchant(verification["merchants"]) is None:
            return {
                "status": "merchant-selection-required",
                "verification": verification,
                "merchants": [dict(m) for m in verification["merchants"]],
            }
        session = self.complete_login(verification, merchant_id, store_id)
        return {"status": "complete", "session": session}

    def refresh_session(self, session: dict[str, Any]) -> dict[str, Any]:
        """Re-mint the merchant token without a new OTP (while the account lives).

        Probes ``login_status`` first: a dead account session raises
        :class:`ApiException` (code ``48500102`` — only a fresh OTP recovers).
        Returns the updated session (new cookies/token) — persist it again.
        """
        self._check_session_version(session)
        credential = session.get("switch_credential")
        if not isinstance(credential, dict):
            raise QmidException("This Shopee session predates silent renewal; log in again with an OTP")
        self._restore(session.get("cookies", []))
        alive, payload, status = self._login_status()
        if not alive:
            raise ApiException(
                "The Shopee account session has expired; log in again with an OTP",
                str(C.NOT_LOGIN_CODE),
                payload,
                status,
            )
        verification = {
            "version": 1,
            "toc_nonce": credential["toc_nonce"],
            "toc_userid": 0,
            "spc_clientid": credential["spc_clientid"],
            "device_fingerprint": credential["device_fingerprint"],
            "cookies": session.get("cookies", []),
            "merchants": session.get("merchants", []),
        }
        _, minted = self._complete_base(verification, session["merchant"]["id"])
        if self._data is not None:
            self._data.set_token(minted["token"])
        return {
            **session,
            "cookies": self._snapshot(),
            "token": minted["token"],
            "expires_at": minted.get("expires_at", session.get("expires_at")),
        }

    def select_merchant(self, session: dict[str, Any], merchant_id: str) -> dict[str, Any]:
        """Switch the active merchant by re-running the SSO exchange (no OTP).

        Never uses the headless-rejected ``SwitchMerchant`` endpoint. Returns
        the updated session — persist it again. Raises :class:`QmidException`
        without a data client.
        """
        self._check_session_version(session)
        merchants = session.get("merchants", [])
        target = next((m for m in merchants if m.get("id") == merchant_id), None)
        if target is None:
            raise ValueError("Shopee merchant is not accessible")
        if session.get("merchant", {}).get("id") == merchant_id:
            return dict(session)
        if target.get("is_active") is not True or target.get("is_banned") is True:
            raise ValueError("The selected Shopee merchant is inactive or banned")
        credential = session.get("switch_credential")
        if not isinstance(credential, dict):
            raise QmidException(
                "This Shopee session cannot switch merchants; log in again to enable switching"
            )
        data = self._require_data_client()
        self._restore(session.get("cookies", []))
        verification = {
            "version": 1,
            "toc_nonce": credential["toc_nonce"],
            "toc_userid": 0,
            "spc_clientid": credential["spc_clientid"],
            "device_fingerprint": credential["device_fingerprint"],
            "cookies": session.get("cookies", []),
            "merchants": merchants,
        }
        merchant, minted = self._complete_base(verification, merchant_id)
        profile = self._get_profile(minted["token"], merchant["id"])
        data.set_token(minted["token"])
        stores = StoresService(data).list_stores()
        return {
            **session,
            "cookies": self._snapshot(),
            "token": minted["token"],
            "account_id": minted["account_id"],
            "merchant": {**merchant, "name": merchant["name"] or profile["merchant_name"]},
            "stores": stores,
            "store_id": _choose_store_id(stores, None, profile.get("store_id")),
            "profile": profile,
            "expires_at": minted.get("expires_at", session.get("expires_at")),
        }

    def select_store(self, session: dict[str, Any], store_id: str) -> dict[str, Any]:
        """Point the session at another known store (pure — no network)."""
        self._check_session_version(session)
        _assert_known_store(session.get("stores", []), store_id)
        return {**session, "store_id": store_id}

    def account_session_alive(self, session: dict[str, Any]) -> bool:
        """Probe ``login_status`` — the only honest liveness signal (``exp`` lies)."""
        self._check_session_version(session)
        self._restore(session.get("cookies", []))
        alive, _, _ = self._login_status()
        return alive

    def session_token(self, session: dict[str, Any]) -> str:
        """Read the ``B:`` token out of the session's dashboard JWT cookie."""
        self._check_session_version(session)
        return str(read_merchant_credential(session.get("cookies", []))["token"])

    # --------------------------------------------------------------- internals
    def _require_data_client(self) -> ShopeePayClient:
        if self._data is None:
            raise QmidException(
                "This login step needs store discovery — construct AuthService with a data client"
            )
        return self._data

    @staticmethod
    def _check_session_version(session: dict[str, Any]) -> None:
        if session.get("version") != 1:
            raise ValueError("Unsupported Shopee session version")

    def _base_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": self._user_agent,
            "Accept-Language": C.ACCEPT_LANGUAGE,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

    def _account_headers(self, risk_token: str | None = None) -> dict[str, str]:
        headers = {
            **self._base_headers(),
            "Origin": C.ACCOUNT_BASE_URL,
            "Referer": login_referer(),
            "X-App-Type": "2",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=0",
        }
        if risk_token:
            headers["af-ac-enc-sz-token"] = risk_token
            headers["x-sz-sdk-version"] = C.SZ_SDK_VERSION
        csrf = self._jar_get(C.CSRF_COOKIE, C.ACCOUNT_BASE_URL)
        if csrf:
            headers["X-CSRFToken"] = csrf
        return headers

    def _snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "name": c.name,
                "value": c.value,
                "domain": c.domain,
                "path": c.path,
                "secure": bool(c.secure),
            }
            for c in self._web.cookies.jar
        ]

    def _restore(self, cookies: list[dict[str, Any]]) -> None:
        self._web.cookies.clear()
        for cookie in cookies:
            self._web.cookies.set(
                str(cookie.get("name", "")),
                str(cookie.get("value", "")),
                domain=str(cookie.get("domain", "")),
                path=str(cookie.get("path", "/") or "/"),
            )

    def _jar_get(self, name: str, domain: str) -> str | None:
        same = [c for c in self._web.cookies.jar if c.name == name]
        if not same:
            return None
        want = domain.split("://", 1)[-1].split("/", 1)[0].lstrip(".")
        for cookie in same:
            have = (cookie.domain or "").lstrip(".")
            if have == want or (have and want.endswith(f".{have}")):
                return cookie.value
        return same[0].value

    def _send(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        headers: dict[str, str],
        content: bytes | None,
    ) -> httpx.Response:
        attempt = 0
        while True:
            try:
                return client.request(method, url, content=content, headers=headers, follow_redirects=False)
            except httpx.TransportError:
                if attempt >= self._max_retries:
                    raise
                time.sleep(self._backoff_base * (2**attempt))
                attempt += 1

    @staticmethod
    def _parse_json(response: httpx.Response, endpoint: str) -> dict[str, Any]:
        try:
            body = json.loads(response.text)
        except ValueError:
            raise ApiException(
                f"Shopee {endpoint} answered HTTP {response.status_code} with invalid JSON",
                None,
                {},
                response.status_code,
            ) from None
        if not isinstance(body, dict):
            raise ApiException(
                f"Shopee {endpoint} answered HTTP {response.status_code} with non-object JSON",
                None,
                {},
                response.status_code,
            )
        return body

    def _post_json(
        self, client: httpx.Client, url: str, body: dict[str, Any], headers: dict[str, str]
    ) -> tuple[int, dict[str, Any]]:
        headers = {**headers, "Content-Type": "application/json"}
        response = self._send(client, "POST", url, headers, json.dumps(body).encode("utf-8"))
        return response.status_code, self._parse_json(response, url)

    def _account(self, path: str, body: dict[str, Any], risk_token: str | None = None) -> dict[str, Any]:
        status, data = self._post_json(
            self._web, C.ACCOUNT_BASE_URL + path, body, self._account_headers(risk_token)
        )
        maybe_captcha = data.get("data")
        if (isinstance(maybe_captcha, dict) and maybe_captcha.get("captcha_required") is True) or (
            _CAPTCHA_WORDS.search(str(data.get("error_msg", "")))
        ):
            code = data.get("error")
            raise ApiException(
                f"Shopee {path} requires a captcha — solve it in a browser and retry",
                str(code) if code is not None else "captcha_required",
                data,
                status,
            )
        if data.get("error") != 0 or data.get("data") is None:
            code = data.get("error")
            reason = str(data.get("error_msg", ""))
            raise ApiException(
                f"Shopee authentication request failed at {path} (error {code}) - {reason}",
                str(code) if code is not None else None,
                data,
                status,
            )
        result = data["data"]
        if not isinstance(result, dict):
            raise ApiException(
                f"Shopee {path} answered with non-object data",
                str(data.get("error")),
                data,
                status,
            )
        return result

    def _partner(
        self, path: str, body: dict[str, Any], token: str = "", toc_nonce: str | None = None
    ) -> dict[str, Any]:
        # Header-only auth: the jar stays out of it (see module docstring).
        self._api.cookies.clear()
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": self._user_agent,
            "Accept-Language": C.ACCEPT_LANGUAGE,
            "Origin": C.PARTNER_ORIGIN,
            "Referer": C.PARTNER_REFERER,
            "X-Merchant-ToB-Clientid": "undefined",
            "X-Merchant-Login-From": C.PARTNER_LOGIN_FROM,
            "X-Merchant-From": C.PARTNER_LOGIN_FROM,
            "X-Merchant-Language": self._language,
            "X-Merchant-Timezone": self._timezone,
            "X-Merchant-RequestId": str(uuid.uuid4()),
            "shopee-baggage": "PFB=undefined",
            "X-Merchant-Token": token,
        }
        if toc_nonce is not None:
            headers["X-Merchant-ToC-Nonce"] = toc_nonce
        status, data = self._post_json(self._api, C.PARTNER_API_BASE_URL + path, body, headers)
        code = data.get("errorCode")
        code_str = str(code) if code is not None else None
        if data.get("errorCode") != 0 or data.get("data") is None:
            reason = str(data.get("errorMsg", ""))
            if (code_str is not None and code_str in C.INVALID_TOKEN_CODES) or _AUTH_WORDS.search(reason):
                raise ApiException(
                    f"Shopee rejected the saved session; login again at {path} (error {code_str}) - {reason}",
                    code_str,
                    data,
                    status,
                )
            raise ApiException(
                f"Shopee partner API request failed at {path} (error {code_str}) - {reason}",
                code_str,
                data,
                status,
            )
        result = data["data"]
        if not isinstance(result, dict):
            raise ApiException(f"Shopee {path} answered with non-object data", code_str, data, status)
        return result

    def _follow_get(self, url: str) -> None:
        current = url
        for _ in range(_MAX_REDIRECTS + 1):
            response = self._send(self._web, "GET", current, self._base_headers(), None)
            if response.status_code < 300 or response.status_code >= 400:
                return
            location = response.headers.get("location")
            if not location:
                raise ApiException(
                    "Shopee redirect did not include a location", None, {}, response.status_code
                )
            current = urllib.parse.urljoin(current, location)
        raise ApiException("Shopee redirect limit was exceeded", None, {}, 508)

    def _bootstrap(self) -> None:
        headers = {**self._base_headers(), "Accept": "text/html"}
        self._send(self._web, "GET", f"{C.ACCOUNT_BASE_URL}/login?lang={self._language}", headers, None)

    def _device_fingerprint(self, device_report: str | None) -> str:
        headers = {
            **self._base_headers(),
            "Origin": C.ACCOUNT_BASE_URL,
            "Referer": f"{C.ACCOUNT_BASE_URL}/",
        }
        if device_report:
            headers["Content-Type"] = "text/plain;charset=UTF-8"
            headers["szdet"] = str(_now_ms())
            content = device_report.encode("utf-8")
        else:
            headers["Content-Type"] = "application/json"
            content = b"{}"
        response = self._send(self._web, "POST", C.DEVICE_FINGERPRINT_REPORT_URL, headers, content)
        data = self._parse_json(response, "/v2/shpsec/web/report")
        inner = data.get("data", {})
        risk_token = inner.get("riskToken") if isinstance(inner, dict) else None
        if data.get("code") != 0 or not risk_token:
            raise ApiException(
                "Shopee device-risk service returned no risk token",
                str(data.get("code")) if data.get("code") is not None else None,
                data,
                response.status_code,
            )
        return str(risk_token)

    def _check_account_exists(self, phone: str, password: str | None, risk_token: str) -> None:
        # Pure lookup: the reference capture answers non-zero here yet proceeds,
        # so the envelope is deliberately NOT validated — only transport fails.
        body = {"phone": phone, "password": hash_shopee_password(password) if password else ""}
        headers = {**self._account_headers(risk_token), "Content-Type": "application/json"}
        self._send(
            self._web,
            "POST",
            C.ACCOUNT_BASE_URL + C.ENDPOINT_CHECK_ACCOUNT_EXISTS,
            headers,
            json.dumps(body).encode("utf-8"),
        )

    def _authenticate_by_password(self, phone: str, password: str | None, risk_token: str) -> bool:
        status, data = self._post_json(
            self._web,
            C.ACCOUNT_BASE_URL + C.ENDPOINT_AUTHENTICATE_BY_PASSWORD,
            {
                "phone": phone,
                "password": hash_shopee_password(password) if password else "",
                "security_device_fingerprint": risk_token,
            },
            self._account_headers(risk_token),
        )
        if data.get("error") == C.NEED_OTP_CODE:
            if not password:
                raise ValueError(_PASSWORD_REQUIRED)
            return True
        if data.get("error") == 0:
            return False
        inner = data.get("data", {})
        if isinstance(inner, dict) and inner.get("toc_account", {}).get("has_password") is True:
            raise ValueError(_PASSWORD_REQUIRED)
        raise ApiException(
            f"Shopee rejected the password before sending the OTP (error {data.get('error')})",
            str(data.get("error")) if data.get("error") is not None else None,
            data,
            status,
        )

    def _login_status(self) -> tuple[bool, dict[str, Any], int]:
        status, data = self._post_json(
            self._web, C.ACCOUNT_BASE_URL + C.ENDPOINT_LOGIN_STATUS, {}, self._account_headers()
        )
        return data.get("error") == 0, data, status

    def _sso_exchange(self, toc_nonce: str, spc_clientid: str, fingerprint: str, staff_user_id: int) -> None:
        token_page = (
            f"{C.ACCOUNT_BASE_URL}{C.ENDPOINT_ACCOUNT_LOGIN_TOKEN}?lang={self._language}"
            f"&spc_clientid={urllib.parse.quote(spc_clientid, safe='')}"
            f"&state={urllib.parse.quote(partner_state(), safe='')}"
            f"&tob_userid={staff_user_id}"
            f"&next={urllib.parse.quote(C.PARTNER_BASE_URL + C.ENDPOINT_ACCOUNT_TOB_AUTH, safe='')}"
            f"&client_id={C.ACCOUNT_CLIENT_ID}&toc_nonce={urllib.parse.quote(toc_nonce, safe='')}"
        )
        self._follow_get(token_page)
        login = self._account(
            C.ENDPOINT_LOGIN_TOC,
            {
                "toc_nonce": toc_nonce,
                "tob_userid": staff_user_id,
                "security_device_fingerprint": fingerprint,
            },
            fingerprint,
        )
        if not login.get("nonce"):
            raise QmidException("Shopee merchant login returned no authorization code")
        exchange_url = (
            f"{C.PARTNER_BASE_URL}{C.ENDPOINT_ACCOUNT_TOB_AUTH}"
            f"?code={urllib.parse.quote(str(login['nonce']), safe='')}&lang={self._language}"
            f"&spc_clientid={urllib.parse.quote(spc_clientid, safe='')}"
            f"&state={urllib.parse.quote(partner_state(), safe='')}"
        )
        self._follow_get(exchange_url)

    def _complete_base(
        self, verification: dict[str, Any], merchant_id: str | None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        merchants = verification.get("merchants", [])
        if merchant_id is not None:
            merchant = next((m for m in merchants if m.get("id") == merchant_id), None)
            if merchant is None:
                raise ValueError("Configured Shopee merchantId is not accessible")
        else:
            merchant = resolve_single_merchant(merchants)
            if merchant is None:
                raise ValueError("merchantId is required when multiple Shopee merchants are accessible")
        if merchant.get("is_active") is not True or merchant.get("is_banned") is True:
            raise QmidException("The selected Shopee merchant is inactive or banned")
        self._sso_exchange(
            str(verification["toc_nonce"]),
            str(verification["spc_clientid"]),
            str(verification["device_fingerprint"]),
            int(merchant["staff_user_id"]),
        )
        credential = read_merchant_credential(self._snapshot())
        if credential["account_id"] != str(merchant["staff_user_id"]):
            raise QmidException("Shopee returned a token for a different merchant")
        return merchant, credential

    def _get_profile(self, token: str, merchant_id: str) -> dict[str, Any]:
        raw = self._partner(C.ENDPOINT_USER_INFO, {}, token=token)
        found = raw.get("merchantId")
        found_id = str(found) if isinstance(found, (int, str)) and not isinstance(found, bool) else ""
        if not found_id or found_id != merchant_id:
            raise QmidException("Shopee returned a profile for a different merchant")
        store = raw.get("store_id")
        user_name = raw.get("userName") or raw.get("tocUserName") or ""
        status = raw.get("shopeepay_service_status")
        return {
            "merchant_id": found_id,
            "merchant_name": str(raw.get("merchantName", "")),
            "store_id": str(store) if isinstance(store, (int, str)) else None,
            "account_id": str(raw.get("tocUid", "")),
            "user_id": str(raw.get("tobUserId", "")),
            "user_name": str(user_name),
            "language": str(raw.get("language", "")),
            "shopeepay_service_status": status if isinstance(status, int) else 0,
            "raw": raw,
        }


def _normalize_merchant(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    merchant_id = raw.get("merchantId")
    staff_uid = raw.get("staffTobUid")
    if (
        not isinstance(merchant_id, int)
        or isinstance(merchant_id, bool)
        or not isinstance(staff_uid, int)
        or isinstance(staff_uid, bool)
    ):
        return None
    return {
        "id": str(merchant_id),
        "name": str(raw.get("merchantName", "")),
        "status": _num_or(raw.get("merchantStatus"), 0),
        "staff_user_id": staff_uid,
        "staff_role": _num_or(raw.get("staffRole"), 0),
        "staff_status": _num_or(raw.get("staffStatus"), 0),
        "is_active": raw.get("isActive") is True,
        "is_banned": raw.get("isBanned") is True,
        "is_current_login_user": raw.get("isCurrentLoginUser") is True,
    }


def _assert_known_store(stores: list[dict[str, Any]], store_id: str) -> None:
    if not any(s.get("id") == store_id for s in stores):
        raise ValueError(f"Shopee store {store_id} is not in the merchant's store list")


def _choose_store_id(
    stores: list[dict[str, Any]], requested: str | None, profile_store: str | None
) -> str | None:
    if requested is not None:
        _assert_known_store(stores, requested)
        return requested
    if profile_store is not None and any(s.get("id") == profile_store for s in stores):
        return profile_store
    if len(stores) == 1:
        return str(stores[0].get("id"))
    return None
