"""List ShopeePay stores. Needs: SHOPEE_TOKEN env (a manual B:... token)."""

import os

from qrismerchantid import ShopeePayPartner


def main() -> None:
    token = os.environ.get("SHOPEE_TOKEN")
    if not token:
        raise SystemExit("Set SHOPEE_TOKEN (see docs/shopee/token.md)")
    sp = ShopeePayPartner(token=token)
    for store in sp.stores.list_stores():
        print(f"{store['id']:>6}  {store['name']}  (status={store['status']})")


if __name__ == "__main__":
    main()
