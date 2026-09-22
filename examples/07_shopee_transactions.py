"""Show recent ShopeePay transactions. Needs: SHOPEE_TOKEN + SHOPEE_STORE_ID env."""

import os

from qrismerchantid import ShopeePayPartner


def main() -> None:
    token = os.environ.get("SHOPEE_TOKEN")
    store_id = os.environ.get("SHOPEE_STORE_ID")
    if not token or not store_id:
        raise SystemExit("Set SHOPEE_TOKEN and SHOPEE_STORE_ID")
    sp = ShopeePayPartner(token=token)
    feed = sp.transactions.list_recent(store_id, minutes=60)
    print(f"pages={feed['pages_fetched']} truncated={feed['truncated']}")
    for tx in feed["transactions"]:
        flag = "OK " if tx["completed"] else "-- "
        print(f"{flag} Rp{tx['amount_idr']:>12,}  {tx['create_time_iso']}  {tx['id']}")


if __name__ == "__main__":
    main()
