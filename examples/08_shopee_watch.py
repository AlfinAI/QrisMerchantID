"""Wait for a ShopeePay payment. Needs: SHOPEE_TOKEN + SHOPEE_STORE_ID + AMOUNT_IDR."""

import os

from qrismerchantid import ShopeePayPartner


def main() -> None:
    token = os.environ.get("SHOPEE_TOKEN")
    store_id = os.environ.get("SHOPEE_STORE_ID")
    amount = os.environ.get("AMOUNT_IDR")
    if not token or not store_id or not amount:
        raise SystemExit("Set SHOPEE_TOKEN, SHOPEE_STORE_ID and AMOUNT_IDR (whole rupiah)")
    sp = ShopeePayPartner(token=token)
    watcher = sp.watch(store_id)
    print(f"seeded={watcher.seed()} — waiting for Rp{int(amount):,} ...")
    paid = watcher.wait_for_payment(int(amount), timeout=300)
    print(f"PAID: {paid['id']} order={paid['order_id']} at {paid['create_time_iso']}")


if __name__ == "__main__":
    main()
