---
title: Kredensial terkurasi (masking)
date: 2026-09-11
sources:
  - research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md
status: curated-masked
version: "1.0"
---

# Kredensial — temuan termasking

> Aturan: tidak ada nilai mentah di file ini. Format masking: `prefix…suffix (len=N)`.

| Item                                         | Nilai masked                                               | Lokasi                                                             | APK      | Status                                     | TODO                                     |
| -------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------ | -------- | ------------------------------------------ | ---------------------------------------- |
| Google API key (geo)                         | `AIza…E0ROM` (len=39)                                      | `AndroidManifest.xml` → meta-data `com.google.android.geo.API_KEY` | GoFood   | TRUE_KEY (cocok `^AIza[0-9A-Za-z_-]{35}$`) | GOFOOD-TODO-ST-3 (dampak restriksi)      |
| Google API key                               | `AIza…????` (len=BELUM TERVERIFIKASI)                      | smali (hitungan=1, nilai tidak terekam)                            | GoPay    | BELUM TERVERIFIKASI                        | TODO-KB-2 (ekstrak ulang termasking)     |
| Firebase DB instance                         | `go-resto-v2.firebaseio.com` (nama instance, bukan secret) | `res/values/strings.xml`                                           | GoFood   | IDENTIFIER                                 | GOFOOD-TODO-NET-4 (rules, tanpa probing) |
| OAuth client ID                              | `2582…bco4.apps.googleusercontent.com`                     | `res/values/strings.xml` → `default_web_client_id`                 | GoFood   | IDENTIFIER (bukan secret)                  | —                                        |
| AES key statis                               | —                                                          | —                                                                  | keduanya | TIDAK DITEMUKAN                            | —                                        |
| HMAC/signing key statis                      | —                                                          | —                                                                  | keduanya | TIDAK DITEMUKAN                            | —                                        |
| RSA/EC PEM tertanam                          | —                                                          | —                                                                  | keduanya | TIDAK DITEMUKAN                            | —                                        |
| `client_secret` / `private_key` const-string | —                                                          | —                                                                  | keduanya | TIDAK DITEMUKAN                            | —                                        |

Kesimpulan: tidak ada static secret kriptografis di client — konsisten dengan arsitektur server-side
signing (token diterbitkan server, GoID SSO). Konfirmasi runtime: TODO-DYN-1 (keduanya).

Kembali ke: [KB index](../docs/KB_QRIS_MERCHANT_INDEX.md) · [MANIFEST](MANIFEST.md)

## TODO aktif

- TODO-KB-2, GOFOOD-TODO-ST-3, GOFOOD-TODO-NET-4
