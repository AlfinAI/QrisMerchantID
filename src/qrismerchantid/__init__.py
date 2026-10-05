"""Unofficial Indonesian QRIS merchant API client for Python.

The package provides GoPay/GoBiz and ShopeePay Partner facades. Use the
provider guides in ``docs/`` for authentication, units, and safety notes.
"""

from __future__ import annotations

from qrismerchantid.core.exceptions import ApiException, QmidException
from qrismerchantid.gopay import GoPayMerchant
from qrismerchantid.shopee import ShopeePayPartner

__version__ = "0.3.2"
__all__ = ["ApiException", "GoPayMerchant", "QmidException", "ShopeePayPartner", "__version__"]
