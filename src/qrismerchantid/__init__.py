"""QrisMerchantID — unofficial Indonesian QRIS merchant API client for Python.

Providers: GoPay/GoBiz merchant (FASE A1+), ShopeePay partner (FASE B1:
manual-token feed; programmatic login is B2).
"""

from __future__ import annotations

from qrismerchantid.core.exceptions import ApiException, QmidException
from qrismerchantid.gopay import GoPayMerchant
from qrismerchantid.shopee import ShopeePayPartner

__version__ = "0.2.0"
__all__ = ["ApiException", "GoPayMerchant", "QmidException", "ShopeePayPartner", "__version__"]
