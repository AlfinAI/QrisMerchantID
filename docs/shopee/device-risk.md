# Device-risk telemetry — capture your own blob

Shopee's fraud SDK posts a telemetry blob to the device-risk issuer before any
OTP request. The issuer grades the body: an empty report returns a **degraded**
risk token whose OTP delivery is **silently suppressed** (every endpoint still
reports success!); a real browser blob returns the full-strength token the OTP
flow needs.

**This package deliberately ships no blob.** Replaying someone else's
fingerprint links your account to strangers, dies for everyone at once when
flagged, and works around an anti-fraud control (account-suspension risk).
Capture your own in 2 minutes:

1. Log out (or open a private window) and open the partner login page.
2. DevTools → Network → filter `report`.
3. Reload the login page; click the `POST .../v2/shpsec/web/report` request.
4. Copy the **request payload** (a long opaque string) → that is your blob.

```python
sp = ShopeePayPartner(device_report="paste-your-blob")  # default for all OTP calls
# ...or per call:
challenge = sp.auth.request_otp("0812xxxxxxx", password="...", device_report="...")
```

The blob is a static fingerprint of one browser — reuse it from the same
machine. If OTPs stop arriving, re-capture (SDK/payload rotation is
TODO-S3 to characterize live).
