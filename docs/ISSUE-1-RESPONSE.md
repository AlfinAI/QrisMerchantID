# Proposed response to Issue #1

The failure was reproduced from the supplied 2026-10-03 browser HAR shape: OTP request succeeds, but the GoID token exchange is rejected when the client metadata/host no longer matches the current browser portal.

The fix in this branch:

- updates `X-AppVersion` from `platform-v3.122.0-72edb090` to `platform-v3.125.0-e1923971`;
- routes browser `/goid/login/request` and `/goid/token` through `https://portal.gofoodmerchant.co.id`;
- keeps merchant/data endpoints on `https://api.gobiz.co.id`;
- aligns browser metadata to Chrome 148 from the new HAR;
- allows a future build override through `QRISMERCHANTID_GOPAY_APP_VERSION`.

The OTP length is read from the response's `otp_length` field and is not assumed to be six digits.

Tests pass locally: 190 passed.

Please retry with a fresh OTP after upgrading. Existing OTP challenges should not be reused after changing the client version/host.
