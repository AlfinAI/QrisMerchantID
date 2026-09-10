"""Watch for an incoming payment (gateway loop). Needs: session + MERCHANT_ID + AMOUNT_MINOR."""

import os

from qrismerchantid import GoPayMerchant
from qrismerchantid.core import token_cache
from qrismerchantid.gopay.money import to_rupiah

SESSION_FILE = ".gopay-session.json"


def main() -> None:
    session = token_cache.load(SESSION_FILE)
    merchant_id = os.environ.get("MERCHANT_ID")
    amount = os.environ.get("AMOUNT_MINOR")
    if not session or not merchant_id or not amount:
        raise SystemExit("Need .gopay-session.json, MERCHANT_ID and AMOUNT_MINOR (e.g. 5000000)")
    gopay = GoPayMerchant(access_token=session["access_token"])
    watcher = gopay.watch(merchant_id)
    print(f"Seeded {watcher.seed()} existing transactions.")
    print(f"Waiting for Rp{to_rupiah(int(amount)):,.0f} (5 min timeout)...")
    try:
        paid = watcher.wait_for_payment(int(amount), timeout=300)
    except TimeoutError as exc:
        raise SystemExit(f"TIMEOUT: {exc}") from None
    print(f"PAID: {paid['order_id']} at {paid['transaction_time']}")


if __name__ == "__main__":
    main()
