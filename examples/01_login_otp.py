"""Login via SMS OTP and cache the session. Needs: GOPAY_PHONE env."""

import os

from qrismerchantid import GoPayMerchant
from qrismerchantid.core import token_cache

SESSION_FILE = ".gopay-session.json"


def main() -> None:
    phone = os.environ.get("GOPAY_PHONE")
    if not phone:
        raise SystemExit("Set GOPAY_PHONE first, e.g. GOPAY_PHONE=0812xxxxxxx")
    gopay = GoPayMerchant()
    otp = gopay.auth.request_otp(phone)
    print(f"OTP sent ({otp['otp_length']} digits, ~{otp['otp_expires_in'] // 60} min window)")
    code = input("Enter SMS code: ")
    session = gopay.auth.login_with_otp(code, otp["otp_token"])
    token_cache.save(SESSION_FILE, session)
    print(f"Logged in. Session cached to {SESSION_FILE}")
    print("Profile:", gopay.users.me()["user"]["email"])


if __name__ == "__main__":
    main()
