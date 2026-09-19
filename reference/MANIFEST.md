---
title: MANIFEST sumber knowledge base
date: 2026-09-11
sources:
  - research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ENDPOINTS.txt
status: verified-index
version: "1.0"
---

# MANIFEST — Sumber KB QRIS Merchant

Semua path relatif ke root repo `QrisMerchantID/`.

| #   | Artefak                                             | SHA256 (tercatat saat kurasi) | Tanggal    | Scope                                     |
| --- | --------------------------------------------------- | ----------------------------- | ---------- | ----------------------------------------- |
| S1  | `research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md`     | `83aa39b0…2574d04f`           | 2026-09-11 | Analisis statis GoPay Merchant (laporan)  |
| S2  | `research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md`   | `0c7000ee…4a71`               | 2026-09-11 | Analisis statis GoFood Merchant (laporan) |
| S3  | `research/APK_GOFOOD_MERCHANT_5.49.0_ENDPOINTS.txt` | `3f03dcd7…c0a5908`            | 2026-09-11 | Daftar endpoint mesin-terbaca (GoFood)    |

SHA256 penuh (verifikasi: `sha256sum research/APK_*`):

- S1: `83aa39b0962a57d778f45dc470c8fc50d773c6315da40b50a2649bed2574d04f`
- S2: `0c7000eedbfe5d171ab76c130e56154ddecc924af57b5e0858bbecd4ae304a71`
- S3: `3f03dcd7f38aa155f2617efa3ed0da8b7d032a5e369a013ff0d2b4892c0a5908`

## File APK asal (sudah dihapus pasca-analisis)

| APK                                                 | SHA256 container (dari §12 laporan) | Status file                           |
| --------------------------------------------------- | ----------------------------------- | ------------------------------------- |
| GoPay Merchant APKM 51,7 MB (APKMirror id 15692643) | `3d83cb9e…fcafba`                   | DIHAPUS — unduh ulang + cocokkan hash |
| GoFood Merchant XAPK 82,2 MB (APKPure)              | `0f25c79c…a9942`                    | DIHAPUS — unduh ulang + cocokkan hash |

> Catatan verifikasi jujur: hash §12 adalah hash **file APK**, bukan hash laporan. APK sudah dihapus
> sehingga kecocokan ulang APK↔hash **BELUM TERVERIFIKASI** sampai unduh ulang dilakukan. Yang
> terverifikasi di sini: ketiga artefak S1–S3 ada, terbaca, dan hash-nya tercatat di atas.

## Link tambahan

Tidak ada link referensi eksternal terverifikasi dalam scope kurasi ini (laporan sumber hanya
merujuk URL unduhan APK di atas). Direktori `reference/links/` sengaja tidak dibuat — TODO-KB-3 jika
referensi docs GoBiz / developer portal dikumpulkan kemudian.

## TODO aktif

- TODO-KB-1: tabrakan kode TODO antar laporan → lihat `KONFLIK.md` (terselesaikan via namespacing).
- TODO-KB-2: last4 API key GoPay tidak terekam → lihat `credentials.md`.
- TODO-KB-3: kumpulkan link referensi eksternal (opsional).
