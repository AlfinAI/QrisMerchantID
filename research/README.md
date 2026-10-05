# Research index

[← Documentation home](../docs/README.md) · [← Main README](../README.md)

This directory contains reverse-engineering notes and traffic-analysis reports that informed the package. Research documents are evidence and hypotheses, not a guarantee that an endpoint is public, stable, or supported.

## How to read the research

1. Start with the [APK research index](../docs/KB_QRIS_MERCHANT_INDEX.md).
2. Check the evidence status and TODO attached to a claim.
3. Compare any candidate endpoint with the supported provider code in `src/`.
4. Never probe a provider or use credentials without authorization.

## Reports

| File | Subject | Status |
| --- | --- | --- |
| [APK GoPay Merchant 2.3.0](APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md) | Static analysis of the GoPay Merchant APK | Research reference |
| [APK GoFood Merchant 5.49.0](APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md) | Static analysis of the GoFood Merchant XAPK | Research reference |
| [GoFood endpoint inventory](APK_GOFOOD_MERCHANT_5.49.0_ENDPOINTS.txt) | Extracted endpoint candidates | Unverified inventory |
| [GoPay and ShopeePay research](RESEARCH_GOPAY_SHOPEEPAY.md) | Earlier provider/API research | Pre-KB notes |
| [ShopeePay phase B](ANALYSIS_SHOPEEPAY_PHASE_B.md) | Authentication and feed research | Pre-KB notes |
| [GoBiz OTP report](REPORT_GOBIZ_OTP_2026-09-19.md) | OTP portal compatibility incident | Compatibility note |

The APK source files are not included. Provenance and hashes are recorded in [`../reference/MANIFEST.md`](../reference/MANIFEST.md). Machine-readable observations are in [`../reference/`](../reference/).

## Evidence vocabulary

- **Verified** means supported by the cited capture or reproducible observation, not guaranteed forever.
- **BELUM TERVERIFIKASI** means *not verified* and must not be treated as a working API.
- **TODO** marks an open research question or a missing capture.

## Responsible handling

Do not publish tokens, cookies, OTPs, passwords, HAR files, device fingerprints, or unmasked security findings. For a suspected vulnerability, follow [`docs/SECURITY_DISCLOSURE.md`](../docs/SECURITY_DISCLOSURE.md) and [`SECURITY.md`](../SECURITY.md).
