# Analisis APK — GoPay Merchant: QRIS 2.3.0 (`com.gojek.gopaymerchant`)

- **Tanggal analisis:** 2026-09-11 (Asia/Jakarta) · **Analis:** agent (statis saja)
- **Sumber APK:** APKMirror, apk_id `15692643`, post_date `2026-08-29`
- **Scope:** ✅ statis + metadata · ❌ dinamis/instrumentasi (tidak tersedia di sandbox — lihat §7)
- **Aturan proyek:** setiap klaim terverifikasi; yang tidak bisa dibuktikan ditandai
  **BELUM TERVERIFIKASI** + TODO. Tidak ada kredensial rahasia yang dicetak di laporan ini.

## 0. Ringkasan eksekutif

APK adalah **build rilis resmi GoPay Merchant** (Aplikasi merchant QRIS GoPay, Flutter +
Kotlin, multidex). Struktur tanda tangan ganda valid: sertifikat pengembang `CN=Gojek`
(2014–2039) + `CN=Android/Google Inc.` (Play App Signing / bundletool), v2-signed.
Tidak ditemukan indikator malware konklusif — yang ada adalah SDK komersial normal
(Firebase, AppsFlyer, OneKyc, GoPay PaymentSDK) + proteksi anti-tamper yang kuat
(deteksi frida/xposed/root, Play Integrity, ptrace).

Temuan (statis saja, bukan kerentanan terkonfirmasi):

| Level | Jumlah | Temuan |
|---|---|---|
| 🔴 Kritis | **0** | — |
| 🟠 Menengah | **3** | M1 Google API key tertanam · M2 `allowBackup` default true · M3 URL staging/dev di build rilis |
| 🟡 Rendah | **5** | R1 CI build-path leak · R2 string `RSA/ECB` perlu review · R3 permission sensitif luas · R4 2 exported SSO Activity · R5 inventory API terekspos (inheren client app) |

**Hasil samping paling berharga untuk proyek:** daftar ±150 endpoint merchant
(`unified-histories`, `finance/balance/*`, `transactions/charge/qris-link`, `qris/shared`,
…), WebSocket realtime `wss://gopay-merchant-raccoon.gojekapi.com/api/v1/events`, dan
bukti statis hubungan GoPay-Merchant-app ↔ GoBiz web (lihat §5.4, §11).

## 1. Identifikasi & metadata

| Atribut | Nilai (terverifikasi) |
|---|---|
| Nama aplikasi | GoPay Merchant: QRIS |
| Package | `com.gojek.gopaymerchant` |
| Versi | `2.3.0` (versionCode `59`) |
| Format unduhan | **APKM** (bundle split-APK, `application/vnd.apkm`), 40 file |
| Ukuran container | 51.766.425 byte |
| MD5 container | `ed243b5d2d16b92bfa688e1e7c42816c` |
| SHA1 container | `8a75c4c1821f1b825d7b3a01ac6bbab6def3b9af` |
| SHA256 container | `3d83cb9ea546df8cdf3324f3e4f62869ba205ce869af28c961ed30756ffcafba` |
| `base.apk` | 19.381.538 byte, SHA256 `4e7851c1…0481ae70c3` (penuh di §12) |
| Split | `base` + arm64-v8a/armeabi-v7a + 7 dpi + 24 bahasa |
| minSdk / targetSdk / compileSdk | 23 (Android 6.0+) / 36 / 36 |
| Arsitektur kode | Flutter (Dart AOT `libapp.so` 22 MB) + Kotlin/Java (multidex: `smali/`–`smali_classes3/`) |
| Penandatangan v1 | `META-INF/BNDLTOOL.RSA` |
| Sertifikat 1 (v1) | Subject/Issuer `CN=Gojek`, serial `0x61baec74`, 2014-12-18 → 2039-12-12 |
| Sertifikat 2 (v2) | `CN=Android, OU=Android, O=Google Inc.` (Play App Signing), 2023-07-17 → 2053-07-17 |
| v2-signed | True |

## 2. Permission (27, via `aapt dump badging`) + kategori risiko

**Berbahaya (9):** `CAMERA` · `POST_NOTIFICATIONS` · `READ_EXTERNAL_STORAGE`
(maxSdk 32) · `WRITE_EXTERNAL_STORAGE` (maxSdk 28) · `ACCESS_FINE_LOCATION` ·
`ACCESS_COARSE_LOCATION` · `RECORD_AUDIO` · `READ_CONTACTS` · `GET_ACCOUNTS`

**Normal/khusus (18):** `INTERNET` · `VIBRATE` · `NFC` · `USE_BIOMETRIC` ·
`USE_FINGERPRINT` · `MODIFY_AUDIO_SETTINGS` · `ACCESS_NETWORK_STATE` ·
`ACCESS_WIFI_STATE` · `WAKE_LOCK` · `RECEIVE_BOOT_COMPLETED` · `FOREGROUND_SERVICE` ·
`SCHEDULE_EXACT_ALARM` · `DETECT_SCREEN_CAPTURE` · `AD_ID` ·
`ACCESS_ADSERVICES_ATTRIBUTION` · `ACCESS_ADSERVICES_AD_ID` ·
`c2dm.permission.RECEIVE` · `BIND_GET_INSTALL_REFERRER_SERVICE`

> R3: kombinasi `READ_CONTACTS` + `RECORD_AUDIO` + lokasi presisi tergolong luas untuk
> aplikasi merchant; sebagian terjustifikasi fitur (KYC, soundbox). **BELUM
> TERVERIFIKASI** apakah semuanya dipakai di runtime (butuh analisis dinamis) — TODO-DYN-1.

## 3. Komponen & attack surface

42 Activity · 14 Service · 17 Receiver · 10 Provider (via androguard).
Hanya **4 komponen `exported=true`** — attack surface kecil:

| Komponen | Catatan |
|---|---|
| `.MainActivity` | Launcher (`singleTask`, portrait) |
| `.notification.narad.DeeplinkHandlerActivity` | Handler deeplink/notifikasi |
| `com.gojek.icp.identity.loginsso.TransparentActivity` | SSO login (R4: auth-related, exported) |
| `com.scp.login.sso.TransparentActivity` | SSO login (R4) |

- Skema deeplink: `gopaymerchant://` (+ `https` applink ke **`gopaymerchant.onelink.me`**,
  di-resolve dari `@string/2131951684`, string `res/values/strings.xml`).
- `queries` manifest: SSO provider Gojek app, Tokopedia, GoPay app (varian
  dev/alpha/beta/staging/nightly — mengindikasikan satu kode sumber multi-flavor),
  WhatsApp, Maps, Facebook/Instagram (AppsFlyer attribution).
- Modul penting: `com.gopay.paymentsdk.*` (checkout, PIN, OTP), `com.gojek.pin`,
  `com.iab.digitalidentity.sdk.*` (OneKyc: KYC, eKYC, SLIK, EDD),
  `com.gojek.narad.*` (notifikasi), `GoPayMerchantFirebaseMessagingService`,
  `WaRetrieverBroadcastReceiver` (WhatsApp zero-tap login).
- Flag `application`: `allowBackup/debuggable/usesCleartextTraffic/
  networkSecurityConfig` **absen** → default platform berlaku:
  `allowBackup=true` (M2), `debuggable=false`, cleartext=false (targetSdk 36).
  `extractNativeLibs=true`.

## 4. Analisis statis

### 4.1 Obfuscation & anti-tamper

- Obfuscation **parsial**: paket `o.*` satu huruf (`o.CustomTabsIntentBuilder`, …)
  berdampingan dengan nama paket asli Gojek/Gopay — konsisten dengan R8/minify
  yang mengecualikan sebagian SDK.
- Anti-tamper kuat (hitung string smali): `xposed` 103 · `attest` 132 ·
  `emulator` 50 · `isRooted` 34 · `ptrace` 25 · `debugger` 12 · `frida` 8 ·
  `qemu` 6 · `PlayIntegrity` 3. SafetyNet/RootBeer: 0 (digantikan Play Integrity).
- `assets/blocked_apis.js` ada (WebView hardening) — isi **BELUM TERVERIFIKASI** (TODO-ST-1).

### 4.2 Kripto

`javax.crypto` 665 · `IvParameterSpec` 39 · `AES/GCM` 8 · `AES/CBC` 8 ·
`RSA/ECB` 6 · `SSL` 2464. Tidak ada `TrustManager`/`CertificatePinner` kustom di
smali (pinning kemungkinan di lapisan Flutter/native — **BELUM TERVERIFIKASI**,
TODO-ST-2). R2: string `RSA/ECB` perlu review padding (OAEP vs PKCS#1 v1.5) —
tidak disimpulkan rentan tanpa melihat konteks kode.

### 4.3 Secret & info disclosure

- **M1:** tepat **1** string pola Google API key (`AIza…`) di smali. Nilainya
  **disensor** di laporan ini. Dampak tergantung restriksi API di konsol Google —
  **BELUM TERVERIFIKASI** (TODO-ST-3). Tidak ada URL Firebase Realtime DB.
- String `apiKey/clientSecret/authToken/"Bearer "` yang lain hanya berupa nama
  field/error message, bukan kredensial.
- **M3:** build rilis menanam banyak host staging/dev: `i-integration.gojekapi.com`,
  `app.integration-gwk.gopayapi.com`, `customer.{staging,sandbox}.gopayapi.com`,
  `gopaymerchant.stg.midtrans.com`, `accounts-q.goto-products.com`,
  `app.staging.findaya.co.id` (umum untuk multi-flavor, tetap dicatat).
- **R1:** CI path leak di `libapp.so`:
  `///builds/go-merchants/merchant-qr/gopay-merchant-mobile/...` (nama proyek
  internal: `merchant-qr`).

### 4.4 Kegagalan tool (dicatat jujur)

- `jadx` 1.5.6 berhenti setelah fase *loading* tanpa output (sandbox 2 GB RAM,
  `threadsCount=1`, exit 0). Analisis kode memakai smali (apktool) + strings —
  tujuh class-level flow **BELUM TERVERIFIKASI** dan butuh jadx di mesin lebih besar (TODO-ST-4).
- `aapt dump xmltree` gagal total pada manifest split-APK ini; atribut dibaca via androguard.

## 5. Inventaris jaringan & API (statis)

> Semua host/path di bawah adalah **string statis** — pemakaian runtime
> (header, auth, base-URL aktif) **BELUM TERVERIFIKASI** tanpa capture traffic (TODO-NET-1).

### 5.1 Host produksi

| Host | Peran (indikasi) |
|---|---|
| `api.gojekapi.com` | API Gojek umum (help/zendesk merchant) |
| `i.gojekapi.com` | CDN `darkroom/gopay-merchants/v2/*` (57 string URL) |
| `gopay-merchant-raccoon.gojekapi.com` | **WebSocket** `wss://…/api/v1/events` (realtime event, protobuf `odpf.raccoon.v1beta1`) |
| `gopaymerchant.midtrans.com` | Gateway merchant (Midtrans) |
| `customer.gopayapi.com` · `customer-web.gopayapi.com` | API + web customer GoPay |
| `app.gwk.gopayapi.com` | Gateway wallet (`/unified-transfers`, `/app/identity/consent`) |
| `onekyc.ky.id.gopayapi.com` | KYC |
| `accounts.goto-products.com` | SSO GoTo |
| `app.gobiz.com` | Syarat & bantuan GoBiz (lihat §5.4) |
| `merchant.gopay.co.id` · `app.gopay.co.id` | Web merchant / install banner |

### 5.2 Endpoint merchant (dari `libapp.so`, dikelompokkan)

- **Histori & rekonsiliasi:** `/api/v1/unified-histories`, `/api/v1/unified-histories/filter`,
  `/api/v2/histories`, `/api/history-filter`, `/api/orders`, `/api/orders/histories`,
  `/api/orders/summary`, `/api/reports/on-demand`, `/api/reports/transactions/job`
- **Keuangan:** `/api/v1/finance/balance/{home,multi-wallet,payout,sof}`,
  `/api/v2/finance/balance/home`, `/api/v1/finance/{earning,gopay-limit,pills}`,
  `/api/v1/finance/interests/gptu`
- **Transaksi & QRIS:** `/api/transactions/`, `/api/transactions/charge`,
  `/api/transactions/charge/qris-link`, `/api/transactions/cpm/payment`,
  `/api/transactions/refund`, `/api/v1/qris/shared`
- **Payout & bank:** `/api/payouts/{manual,options,settings}`,
  `/api/v1/payouts/{schedules,gptu/backfill}`, `/api/v1/payout-confirm`,
  `/api/v1/payout-page`, `/api/bank-accounts/{validate,validate-gopay,validate-gptu,beneficiary-banks}`,
  `/api/v2/bank-accounts/{register,verify}`, `/api/v1/sof/gopay/{register,verify}`
- **Auth & profil:** `/api/auth/token`, `/api/v1/login/complete`, `/api/v1/totp`,
  `/api/v1/profile`, `/api/v1/profile/verify-{fr,otp}`, `/api/v1/user/{kyc-submission-status,safety-meter}`,
  `/api/registration/status`, `/api/kyc/token`, `/api/v1/auth/register`
- **PIN (smali, paymentsdk):** `/api/v1/users/pin/{challenges,tokens}`,
  `/api/v1/users/pins/{allowed,otp/init}`, `/api/v2/users/pins/{reset,setup}/tokens`,
  `/api/v3/users/pins/{reset,setup}/tokens`, `/api/v3/partner/identity/auth`,
  `/api/v2/challenges/{challenge-id}/pin-page`
- **Onboarding/outlet/produk:** `/api/onboarding/processes`, `/api/outlets/`,
  `/api/v1/outlets/`, `/api/products/`, `/api/products/orders/`,
  `/api/products/SOUNDBOX/outlets`, `/api/v1/products/gopay-spiker/price`,
  `/api/v1/subscriptions/soundbox/*`, `/api/shipping-addresses/*`,
  `/api/documents/{mcc,postal-code}`, `/api/location/*`, `/api/search*`
- **Remote config & konten:** `/api/configs/detail/*` (±30 key:
  `gopay-container`, `webview-features`, `cico-*-shortcut`, `soundbox-*`,
  `gma-onboarding-*`, …), `/api/pages/welcome/banners`, `/api/article*`,
  `/api/dynamic-webpage/contents/`, `/api/notifications/*`, `/api/feedback*`,
  `/api/campaigns*`, `/api/v1/homepage*`, `/api/v1/user-tasks*`,
  `/api/partner/gomodal/{auth,consent}`, `/api/umi/eligibility`, `/api/consents/umi`,
  `/api/v1/cico/*` (cashout/withdraw), `/api/v1/affiliate/validate`,
  `/api/v1/analytics/partner-id-mappings`, `/api/v1/roles`→`/api/roles`

### 5.3 Protokol

HTTPS (default, tanpa `networkSecurityConfig` kustom) + **WebSocket aman (wss)**
untuk event realtime. Tidak ada URL `http://` API yang ditemukan di smali/libapp
(selain contoh/dokumentasi).

### 5.4 Relasi GoPay-Merchant-app ↔ GoBiz (menjawab riset kavionn#3)

Bukti statis di APK:

1. `app.gobiz.com` dirujuk untuk dokumen resmi merchant:
   `//app.gobiz.com/files/terms-and-condition/gopay-merchant-tnc-v01.2025`
   (+ help center) — permukaan web GoBiz dipakai bersama.
2. API runtime memakai gateway khusus merchant (`raccoon`, `midtrans`,
   `gopayapi`), BUKAN host `gobiz` — mengindikasikan: **akun/sistem sama,
   gateway API berbeda**.
3. Konsisten dengan jawaban maintainer `kavionn/gobiz-payment#3` (data transaksi
   terlihat di kedua sisi untuk akun yang sama).

Kesetaraan flow/parameter antar keduanya **BELUM TERVERIFIKASI** (butuh capture —
TODO-NET-2).

## 6. Library native (split arm64)

| Library | Ukuran | Identifikasi |
|---|---|---|
| `libapp.so` | 22 MB | **Dart AOT** — seluruh logika Flutter app |
| `libflutter.so` | 11 MB | Flutter engine (string versi tidak ketemu — TODO-ST-5) |
| `liba25.so` | 3,7 MB | Tidak teridentifikasi (hanya simbol C++ generik) — TODO-ST-6 |
| `libaf-android.so` | 2,1 MB | AppsFlyer |
| `libceec.so` | 896 KB | Tidak teridentifikasi — TODO-ST-6 |
| `libbatteryOpt.so` | 640 KB | Battery-optimization helper (generik) |
| `libba87b2.so` | 552 KB | Tidak teridentifikasi — TODO-ST-6 |
| `libd996c4.so` | 8 KB | `androidx.datastore` native counter |

`base.apk` sendiri tidak membawa `.so` (native hanya di split ABI).

## 7. Analisis dinamis — TIDAK DILAKUKAN

Alasan terverifikasi: sandbox tanpa KVM/emulator/device (`adb`, `frida`, `mitmdump`
tidak tersedia; instalasi frida tanpa target Android tidak berguna). Maka:

- Runtime behavior, API hooking (enkripsi/jaringan), dan intersepsi traffic:
  **BELUM TERVERIFIKASI** (TODO-DYN-1).
- Instruksi template "hentikan jika malware": tidak terpicu — tidak ada indikator
  malware konklusif pada tahap statis.
- Prosedur lanjutan (di mesin analis): install split via `bundletool`/`apkmirror
  installer` di emulator terisolasi → `frida` hook `javax.crypto` + WebSocket →
  `mitmproxy` dengan CA sistem (catatan: Play Integrity + SSL default mempersulit —
  antisipasi kegagalan bypass).

## 8. Perbandingan Play Store — TODO

Tidak dilakukan (tidak ada akses API Play Store terverifikasi dari sandbox).
Verifikasi yang sudah ada sebagai pengganti parsial: sertifikat `CN=Gojek` +
struktur Play App Signing konsisten dengan rilis resmi. TODO-REL-1: bandingkan
`versionCode 59` + hash dengan listing Play Store dari perangkat.

## 9. Verdict keamanan

- **Malware:** tidak ada indikator konklusif (skor: bersih-secara-statis).
- **Keaslian:** struktur signature + sertifikat Gojek valid; kemungkinan
  repack terdeteksi akan menggugurkan v2-signature (belum diuji re-sign —
  TODO-REL-2).
- **Risiko utama bersifat postur** (M1–M3, R1–R5 di §0), semuanya butuh
  konfirmasi dinamis sebelum diklaim sebagai kerentanan.

## 10. Rekomendasi

1. (M1) Batasi Google API key per aplikasi/Android + rotasi berkala.
2. (M2) Set eksplisit `allowBackup="false"` (atau `fullBackupContent` selektif)
   untuk data sesi/token.
3. (M3) Pisahkan konstanta staging dari build rilis (build flavor/gating).
4. (R2) Audit pemakaian `RSA/ECB` → pastikan OAEP; pertimbangkan pinning
   terpusat yang teraudit.
5. (R3) Terapkan permission rationale + minimalisasi (khusus `READ_CONTACTS`).
6. Umum: ulangi analisis ini tiap rilis minor (endpoint merchant berubah cepat).

## 11. Relevansi untuk QrisMerchantID (riset lanjutan)

Kandidat endpoint prioritas (butuh capture untuk host+header+auth):

1. `wss://gopay-merchant-raccoon.gojekapi.com/api/v1/events` — alternatif
   realtime pengganti polling watcher.
2. `/api/v1/unified-histories` + `/filter`, `/api/v2/histories` — riwayat terpadu.
3. `/api/v1/finance/balance/multi-wallet` — saldo multi-wallet.
4. `/api/transactions/charge/qris-link`, `/api/v1/qris/shared` — QRIS dinamis/link.
5. `/api/v1/login/complete` + `/api/v1/totp` — flow login merchant-app
   (kemungkinan berbeda dari GoBiz web — TODO-NET-3).

## 12. Log reproduksibilitas

- Tool: `apktool 2.7.0-dirty`, `aapt` (Debian), `androguard 4.1.4`,
  `jadx 1.5.6` (gagal load — §4.4), `unzip`, `strings` (binutils),
  OpenJDK 11, Python 3.13.
- Perintah inti (urutan):
  1. `curl -sSL -A <browser-UA> -e https://www.apkmirror.com/ -o gopay-merchant.apk
     "https://www.apkmirror.com/.../download.php?id=15692643&key=0b0b1c89…"`
     → 51.766.425 byte, `application/vnd.apkm`
  2. `sha256sum` container: `3d83cb9ea546df8cdf3324f3e4f62869ba205ce869af28c961ed30756ffcafba`
  3. `unzip -o gopay-merchant.apkm base.apk info.json`
  4. `sha256sum base.apk`:
     `4e7851c18113263da47edb07272f3ba3add898e2dce5ec542aadad0481ae70c3`
  5. `aapt dump badging base.apk` → identitas + 27 permission
  6. `apktool d -o base base.apk` (308 MB, di `/tmp`, dihapus setelah analisis)
  7. Skrip androguard → komponen + sertifikat (§1, §3)
  8. `grep` smali → host/URL, `const-string` secret, sinyal anti-tamper/kripto
  9. `strings -n 6 lib/arm64-v8a/libapp.so` (37.662 baris) → §5
  10. Resolve applink: `public.xml` `0x7f130044` → `strings.xml` →
      `gopaymerchant.onelink.me`
- Artefak tersimpan: laporan ini saja. File `upstream/apk-gopay/gopay-merchant.apkm`
  (52 MB) **dihapus pasca-analisis** atas perintah user (folder `upstream/` dibersihkan
  karena proyek OVO selesai); dapat diunduh ulang dari APKMirror (apk_id 15692643)
  selama link unduhan masih hidup, lalu verifikasi SHA256 §1.
