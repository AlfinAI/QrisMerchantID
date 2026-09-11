---
title: Deeplink & applink terkurasi
date: 2026-09-11
sources:
  - research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md
status: curated
version: "1.0"
---

# Deeplink & applink

| Skema | APK | Host / path | Catatan risiko |
|---|---|---|---|
| `gopaymerchant://` | GoPay | (router in-app) | — |
| `https` (applink) | GoPay | host `gopaymerchant.onelink.me` (AppsFlyer OneLink, resolve dari `@string/2131951684`) | — |
| `mailto`, `tel` | GoPay | — | Bukan attack surface |
| `gofoodmerchant://` | GoFood | (router in-app) | — |
| `gobiz://` | GoFood | (router in-app) | Bukti GoFood ∈ keluarga GoBiz |
| `gojek://` | GoFood | (router in-app) | — |
| `https` / `http` | GoFood | host attrs = token rute in-app (`bff_generic_screen`, `clipship`), bukan DNS | R5: skema `http` + wildcard `*` terlalu longgar |
| `*` | GoFood | — | R5 |

Kembali ke: [KB index](../docs/KB_QRIS_MERCHANT_INDEX.md) · [MANIFEST](MANIFEST.md)

## TODO aktif

- Tidak ada (temuan R5 tercatat di `temuan_keamanan.csv`).
