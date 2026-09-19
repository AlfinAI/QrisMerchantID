---
title: Register konflik kurasi
date: 2026-09-11
sources:
  - research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md
status: curated
version: "1.0"
---

# KONFLIK — register + resolusi

Aturan: konflik tidak diputuskan sepihak; dicatat + ditandai review manual. Kode TODO laporan asal
**tidak diubah**; KB memakai alias ber-prefix.

## TODO-KB-1: tabrakan kode TODO antar laporan (TERATASI — review manual OK)

Kode yang sama, makna berbeda:

| Kode asal  | Makna GoPay                        | Makna GoFood                       | Alias KB                             |
| ---------- | ---------------------------------- | ---------------------------------- | ------------------------------------ |
| TODO-ST-1  | Isi `assets/blocked_apis.js`       | Hitungan penuh 16 dex              | GOPAY-TODO-ST-1 / GOFOOD-TODO-ST-1   |
| TODO-NET-2 | Kesetaraan flow GoBiz↔merchant-app | Overlap endpoint QRIS GoPay↔GoFood | GOPAY-TODO-NET-2 / GOFOOD-TODO-NET-2 |
| TODO-NET-3 | Flow login merchant-app            | Mekanisme realtime (FCM?)          | GOPAY-TODO-NET-3 / GOFOOD-TODO-NET-3 |

Kode yang maknanya sama (tanpa prefix, berlaku keduanya): TODO-DYN-1, TODO-NET-1, TODO-REL-1,
TODO-REL-2, TODO-ST-3, TODO-ST-4, TODO-ST-6. Kode eksklusif: GOPAY-TODO-ST-2 (pinning),
GOPAY-TODO-ST-5 (versi Flutter), GOFOOD-TODO-NET-4 (rules Firebase).

## TODO-KB-2: last4 API key GoPay tidak terekam (TERBUKA)

Laporan GoPay hanya mencatat hitungan=1 tanpa nilai. KB menulis `AIza…???? (len=BELUM
TERVERIFIKASI)`. Resolusi: unduh ulang APKM (hash §12 S1) → grep termasking → update
`credentials.md`. Owner: agent, P2.

## Konflik data endpoint/host

Nol. Tidak ada path/host yang maknanya bertentangan antar laporan (perbedaan PIN v1/v3
didokumentasikan sebagai varian, bukan konflik — lihat `endpoints.csv` grup `auth-pin`).

Kembali ke: [KB index](../docs/KB_QRIS_MERCHANT_INDEX.md) · [MANIFEST](MANIFEST.md)

## TODO aktif

- TODO-KB-1 (tertutup, menunggu review manual user), TODO-KB-2 (terbuka), TODO-KB-3 (opsional, di
  MANIFEST).
