---
title: SDK & komponen bersama (bukti sister apps)
date: 2026-09-11
sources:
  - research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md
status: curated
version: "1.0"
---

# SDK & komponen bersama — bukti sister apps

| SDK / komponen                     | Bukti GoPay                                    | Bukti GoFood                                                   | Kesimpulan                                                        |
| ---------------------------------- | ---------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------- |
| PIN SDK (`paymentsdk`)             | 10 path §5.2 (smali)                           | 10 path §5.2 (smali)                                           | **6 path IDENTIK persis** (lihat `endpoints.csv` grup `auth-pin`) |
| Sertifikat signing                 | `CN=Gojek` serial `0x61baec74`                 | `CN=Gojek` serial `0x61baec74`                                 | Penandatangan identik                                             |
| SSO Gojek (`com.scp.login.sso`)    | `TransparentActivity` exported                 | `TransparentActivity` exported + `ILoginSSOProvider`           | Auth terpadu                                                      |
| Narad (notifikasi)                 | `com.gojek.narad.*`, `DeeplinkHandlerActivity` | `com.gojek.narad.*` (alarm + feedbackloops)                    | Stack notifikasi sama                                             |
| OneKyc (`com.iab.digitalidentity`) | `GopayIDKYCActivity` + 20 activity KYC         | Native `libgb367f.so` + paket KYC                              | Vendor KYC sama                                                   |
| GoID / GoTo accounts               | `accounts.goto-products.com`                   | `goid.gojekapi.com` + `accounts-integration.goto-products.com` | Keluarga auth sama                                                |
| AppsFlyer (+OneLink)               | `libaf-android.so`, applink `onelink.me`       | `libaf-android.so`, `SingleInstallBroadcastReceiver`           | Atribusi sama                                                     |
| Firebase (FCM/perf/remoteconfig)   | `GoPayMerchantFirebaseMessagingService`        | `FirebaseNotificationHandler` + perf provider                  | Push stack sama                                                   |
| Play Integrity + deteksi root/hook | frida/xposed/ptrace/emulator                   | xposed/debugger/ptrace/RootBeer                                | Postur anti-tamper sama                                           |

Yang BERBEDA (bukan shared): framework UI (Flutter vs native), gateway API
(raccoon/midtrans/gopayapi vs gobiz BFF), realtime (wss vs FCM), pinning (implisit vs OkHttp
eksplisit), obfuscation (parsial vs minimal).

Kembali ke: [KB index](../docs/KB_QRIS_MERCHANT_INDEX.md) · [MANIFEST](MANIFEST.md)

## TODO aktif

- Tidak ada.
