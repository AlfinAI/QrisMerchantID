"""Last-7-days analytics + payouts + issuer breakdown. Needs: cached session + MERCHANT_ID."""

import os

from qrismerchantid import GoPayMerchant
from qrismerchantid.core import token_cache
from qrismerchantid.gopay.money import to_rupiah

SESSION_FILE = ".gopay-session.json"


def main() -> None:
    session = token_cache.load(SESSION_FILE)
    merchant_id = os.environ.get("MERCHANT_ID")
    if not session or not merchant_id:
        raise SystemExit("Need .gopay-session.json (see 01_login_otp.py) and MERCHANT_ID env")
    gopay = GoPayMerchant(access_token=session["access_token"])

    txns = gopay.transactions.analytics(merchant_id, days=7)
    print(f"Transactions (7d): {txns['total']}")
    for tx in txns["transactions"][:10]:
        print(f"- {tx['order_id']}: Rp{to_rupiah(tx['gross_amount']):,.0f} [{tx['transaction_status']}]")

    payable = gopay.payouts.payable_detail(merchant_id)["payable_detail"]
    print(f"Payable: Rp{to_rupiah(payable['payable']):,.0f}")

    page = gopay.payouts.list()
    print(f"Payouts on file: {len(page['payouts'])} (page {page['current_page']})")


if __name__ == "__main__":
    main()
