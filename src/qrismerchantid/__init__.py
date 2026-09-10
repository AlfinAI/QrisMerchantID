"""QrisMerchantID — unofficial Indonesian QRIS merchant API client for Python.

Providers: GoPay/GoBiz merchant (FASE A1+), ShopeePay partner (roadmap).
Only ``core`` ships in FASE A0; provider facades land with their phases.
"""

from __future__ import annotations

from qrismerchantid.core.exceptions import ApiException, QmidException

__version__ = "0.1.0"
__all__ = ["ApiException", "QmidException", "__version__"]
