"""Load cached session (or login), then list merchants. Needs: session file or GOPAY_* env."""

import os

from qrismerchantid import GoPayMerchant
from qrismerchantid.core import token_cache
from qrismerchantid.core.exceptions import ApiException

SESSION_FILE = ".gopay-session.json"


def main() -> None:
    session = token_cache.load(SESSION_FILE)
    gopay = GoPayMerchant(access_token=session["access_token"]) if session else GoPayMerchant()
    try:
        found = gopay.merchants.search()  # cheap probe: doubles as token check
    except ApiException as exc:
        if exc.http_status != 401 or not os.environ.get("GOPAY_EMAIL"):
            raise
        print("Session expired, logging in with password...")
        session = gopay.auth.login_with_password(os.environ["GOPAY_EMAIL"], os.environ["GOPAY_PASSWORD"])
        token_cache.save(SESSION_FILE, session)
        found = gopay.merchants.search()
    print(f"Merchants: {found['total']}")
    for hit in found["hits"]:
        print(f"- {hit['id']}: {hit.get('merchant_name')}")
        detail = gopay.merchants.detail(hit["id"])
        print(f"  outlet: {detail.get('outlet_name')} | KYC: {detail.get('kyc_status')}")


if __name__ == "__main__":
    main()
