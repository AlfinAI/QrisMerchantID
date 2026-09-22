"""ShopeePay OTP login + session save. Needs: SHOPEE_PHONE + SHOPEE_PASSWORD env,
optional SHOPEE_DEVICE_REPORT (see docs/shopee/device-risk.md) and SHOPEE_MERCHANT_ID."""

import getpass
import json
import os

from qrismerchantid import ShopeePayPartner

SESSION_FILE = ".shopee-session.json"


def main() -> None:
    phone = os.environ.get("SHOPEE_PHONE")
    password = os.environ.get("SHOPEE_PASSWORD")
    if not phone:
        raise SystemExit("Set SHOPEE_PHONE (and SHOPEE_PASSWORD for protected accounts)")
    if password is None:
        password = getpass.getpass("ShopeePay password (empty if none): ") or None
    sp = ShopeePayPartner(device_report=os.environ.get("SHOPEE_DEVICE_REPORT"))
    challenge = sp.auth.request_otp(
        phone, password=password, channel=int(os.environ.get("SHOPEE_OTP_CHANNEL", "3"))
    )
    print(f"OTP sent via channel {challenge['channel']} — check WhatsApp/SMS.")
    outcome = sp.auth.login_with_otp(
        challenge, getpass.getpass("OTP code: "), merchant_id=os.environ.get("SHOPEE_MERCHANT_ID")
    )
    if outcome["status"] == "merchant-selection-required":
        for m in outcome["merchants"]:
            print(f"  {m['id']}  {m['name']}")
        outcome = {
            "status": "complete",
            "session": sp.auth.complete_login(
                outcome["verification"], merchant_id=input("Merchant ID: ")
            ),
        }
    session = outcome["session"]
    json.dump(session, open(SESSION_FILE, "w"))
    print(f"Logged in as {session['merchant']['name']} — session saved to {SESSION_FILE}")
    print(f"Stores: {', '.join(s['name'] for s in session['stores'])}")


if __name__ == "__main__":
    main()
