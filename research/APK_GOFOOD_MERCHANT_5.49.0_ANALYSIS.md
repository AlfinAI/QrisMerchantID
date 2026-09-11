# Analisis APK — GoFood Merchant 5.49.0 (`com.gojek.resto`)

- **Tanggal analisis:** 2026-09-11 (Asia/Jakarta) · **Analis:** agent (statis saja)
- **Sumber APK:** APKPure, `https://d.apkpure.com/b/XAPK/com.gojek.resto?version=latest`
  (redirect ke `data.winudf.com`, filename `GoFood Merchant_5.49.0_APKPure.xapk`)
- **Scope:** ✅ statis + metadata · ❌ dinamis/instrumentasi (tidak tersedia di sandbox — lihat §7)
- **Aturan proyek:** setiap klaim terverifikasi; yang tidak bisa dibuktikan ditandai
  **BELUM TERVERIFIKASI** + TODO. Nilai kredensial tidak dicetak mentah (masking
  `prefix…suffix (len=N)`).

## 0. Ringkasan eksekutif

APK adalah **build rilis resmi GoFood Merchant** (aplikasi merchant GoFood/Resto,
**native Kotlin/Java** — BUKAN Flutter, 16 dex, 71 MB base). Tanda tangan ganda valid:
sertifikat `CN=Baskara Patria, OU=GO-JEK Indonesia` + `CN=Gojek` (**serial
`0x61baec74` SAMA dengan GoPay Merchant**), plus stamp distribusi Play Store.
Tidak ada indikator malware konklusif — SDK komersial normal (Firebase, AppsFlyer,
OneKyc, Incognia-fraud, CleverTap) + OkHttp certificate pinning + deteksi root/hook.

Temuan (statis saja, bukan kerentanan terkonfirmasi):

| Level | Jumlah | Temuan |
|---|---|---|
| 🔴 Kritis | **0** | — |
| 🟠 Menengah | **3** | M1 Google API key di manifest · M2 cleartext untuk 4 domain (termasuk `*.privydev.id`) · M3 URL staging/dev di build rilis |
| 🟡 Rendah | **5** | R1 nama instance Firebase DB terekspos · R2 permission signature-level `READ_PRIVILEGED_PHONE_STATE` · R3 permission berbahaya luas · R4 `PreviewActivity` (compose tooling) ikut exported · R5 skema deeplink `http` + `*` terlalu longgar |

**Hasil proyek:** ±90 endpoint merchant (grup auth/PIN, EDC/kartu offline, settlement,
change-request, onboarding workflow, chat, outlet), gateway **`api.gobiz.co.id` +
`app.gobiz.co.id`** (GoFood = keluarga GoBiz — jauh lebih erat dibanding GoPay
Merchant yang hanya merujuk GoBiz untuk T&C), dan skema deeplink **`gobiz://`**.

## 1. Identifikasi & metadata

| Atribut | Nilai (terverifikasi) |
|---|---|
| Nama aplikasi | GoFood Merchant |
| Package | `com.gojek.resto` |
| Versi | `5.49.0` (versionCode `247`) |
| Format unduhan | **XAPK v2** (split-APK), 5 file, 82.192.045 byte |
| MD5 container | `45deddf2d3fb3294ca73c9209268628a` |
| SHA1 container | `370c6d206e977fc97015a9eee5faaf19f3b0a796` |
| SHA256 container | `0f25c79cbd05d952dc40cdcfdc072d0b249a2f310c633b951be68f45fe6a9942` |
| Base `com.gojek.resto.apk` | 71.765.609 byte, SHA256 `1a6f85f3dfdac8b1a84936c614fae915098ed086f4c4ba37ba3f69593b695366` |
| `config.arm64_v8a.apk` | 9.241.647 byte, SHA256 `5f7baea2254037e318a4f9dd92dfa21715c792df509337bf62bb069687372810` |
| `config.mdpi.apk` | 1.140.030 byte, SHA256 `fdef855b76f86149aa1848095cd8e79c7d2e743365fbe972ae8deee5f6aa0c72` |
| minSdk / targetSdk / compileSdk | 21 (Android 5.0+) / 35 / 36 |
| Arsitektur kode | Native Kotlin/Java, **16 dex** (`smali/`–`smali_classes16/`), 10.835 file, **tanpa Flutter** (tidak ada `libapp.so`/`libflutter.so`) |
| Main activity | `com.gojek.merchant.splash.GmSplashActivity` |
| Application class | `com.gojek.merchant.common.GoMerchantApp` |
| Penandatangan v1 | `META-INF/BNDLTOOL.RSA` |
| Sertifikat 1 | Subject `CN=Baskara Patria, OU=GO-JEK Indonesia, O=GO-JEK Indonesia, Jakarta, ID`, serial `0x38f053b0`, 2016-09-15 → 2041-09-09 |
| Sertifikat 2 | Subject/Issuer `CN=Gojek`, serial `0x61baec74`, 2014-12-18 → 2039-12-12 — **SAMA dengan GoPay Merchant** |
| Stamp distribusi | `com.android.stamp.source=https://play.google.com/store`, `STAMP_TYPE_DISTRIBUTION_APK` |

## 2. Permission (46, via `aapt` + manifest XAPK) + kategori risiko

**Berbahaya (14):** `CALL_PHONE` · `READ_PHONE_STATE` · `CAMERA` ·
`POST_NOTIFICATIONS` · `READ_EXTERNAL_STORAGE` (maxSdk 32) ·
`WRITE_EXTERNAL_STORAGE` · `ACCESS_COARSE_LOCATION` · `ACCESS_FINE_LOCATION` ·
`RECORD_AUDIO` · `READ_CONTACTS` · `WRITE_CONTACTS` · `BLUETOOTH_SCAN` ·
`BLUETOOTH_CONNECT` · `READ_MEDIA_IMAGES` · `READ_MEDIA_VIDEO`

**Signature/privileged (3):** `READ_PRIVILEGED_PHONE_STATE` (R2 — hanya efektif di
system-app/partner build; di install normal tidak diberikan) ·
`titan.extperm.SETTING_SET` · `titan.extperm.UX_SET` (custom, keluarga perangkat
`titan`/Sunmi — indikasi build EDC/POS)

**Khusus (6):** `SYSTEM_ALERT_WINDOW` · `SCHEDULE_EXACT_ALARM` ·
`MANAGE_OWN_CALLS` · `HIGH_SAMPLING_RATE_SENSORS` ·
`ACCESS_NOTIFICATION_POLICY` · `FOREGROUND_SERVICE_SPECIAL_USE`

**Normal (23):** `INTERNET` · `ACCESS_NETWORK_STATE` · `CHANGE_NETWORK_STATE` ·
`ACCESS_WIFI_STATE` · `CHANGE_WIFI_STATE` · `VIBRATE` · `WAKE_LOCK` ·
`RECEIVE_BOOT_COMPLETED` · `FOREGROUND_SERVICE` · `USE_BIOMETRIC` ·
`USE_FINGERPRINT` · `MODIFY_AUDIO_SETTINGS` · `BLUETOOTH` · `BLUETOOTH_ADMIN` ·
`AD_ID` · `ACCESS_ADSERVICES_ATTRIBUTION` · `c2dm.permission.RECEIVE` ·
`BIND_GET_INSTALL_REFERRER_SERVICE` · `READ_GSERVICES` ·
`com.gojek.resto.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` + 3 vendor
(Samsung/Huawei).

> R3: cakupan berbahaya jauh lebih luas dari GoPay Merchant (9) — telepon, kontak
> tulis, bluetooth, media. Sebagian terjustifikasi (VoIP/voice-call, printer BT,
> upload katalog). Pemakaian runtime **BELUM TERVERIFIKASI** — TODO-DYN-1.

## 3. Komponen & attack surface

413 Activity · 30 Service · 33 Receiver · 14 Provider (via androguard).
**9 komponen `exported=true`:**

| Komponen | Catatan |
|---|---|
| `com.gojek.merchant.splash.GmSplashActivity` | Launcher |
| `com.gojek.merchant.platform.deeplink.AppDeepLinkActivity` | Router deeplink |
| `com.gojek.merchant.lib_bff.screen.BffGenericScreenActivity` | Layar BFF generik |
| `com.gojek.merchant.mart.order.detail.presentation.MartOrderDetailActivity` | Detail order (GoMart berbagi kode) |
| `com.gojek.clipship.presentation.onboarding.ClipshipOnboardingActivity` | Onboarding video/clip |
| `com.gojek.merchant.promo.history.feature.campaigndetail.CampaignDetailActivity` | Detail kampanye |
| `com.gojek.merchant.promo.oc.feature.bundle_mfp_ads.dynamic.DynamicBundleActivity` | Iklan bundle dinamis |
| `com.scp.login.sso.TransparentActivity` | SSO login (auth-related, exported) |
| `androidx.compose.ui.tooling.PreviewActivity` | R4 — tooling compose tidak seharusnya exported di rilis |

- Skema deeplink: **`gofoodmerchant://` · `gobiz://` · `gojek://`** + `https` +
  `http` + `*` (R5 — `http` dan wildcard `*` terlalu longgar).
- Atribut `android:host` pada filter applink berisi token rute in-app
  (`bff_generic_screen`, `clipship`), bukan hostname DNS.
- `queries`: paket **`com.gojek.gopaymerchant`** (!), WhatsApp, Maps, Gmail,
  Facebook/Instagram, TikTok; provider SSO Gojek app + GoPay (varian
  dev/alpha/beta/staging/nightly/**sandbox**/sg-qa — multi-flavor + region SG).
- Modul penting: `com.gojek.offline.payment.sdk.*` (kartu/EDC: settlement,
  reversal, prepaid-report — relevan QRIS/EDC), `com.gojek.voip`,
  `com.gojek.conversations` (chat), `com.gojek.merchant.food.*` (order/katalog/
  dine-in), `com.gojek.merchant.payment.*`, `com.iab.digitalidentity` (OneKyc),
  `com.gojek.narad` (notifikasi), `com.incognia` (fraud lokasi),
  `FirebaseNotificationHandler`.
- Flag `application`: `allowBackup` absen (default true) **tetapi**
  `fullBackupContent=@xml/appsflyer_backup_rules` + `dataExtractionRules` hadir
  (backup ter-skoping — lebih baik dari GoPay Merchant); `debuggable=false`;
  `networkSecurityConfig=@xml/2132213767` (lihat M2); `extractNativeLibs=false`.

## 4. Analisis statis

### 4.1 Obfuscation & anti-tamper

- Obfuscation **minimal**: nama paket/kelas utuh
  (`com.gojek.merchant.food.internal.features.order.details…`) — tidak ada R8
  agresif seperti GoPay Merchant (`o.*`). Hanya nama file `.so` yang diacak
  (`libb12.so`, …).
- Anti-tamper (hitung pada `smali/`, `smali_classes2/`, `smali_classes3/` —
  **sampel 3 dari 16 dex**): `xposed` 976 · `debugger` 28 · `emulator` 8 ·
  `ptrace` 7 · `frida` 4 · `PlayIntegrity` 3 · `isRooted` 2 · `RootBeer` 2 ·
  `attest` 1 · `SafetyNet` 0 · `qemu` 0. Hitungan penuh 16 dex TODO-ST-1.

### 4.2 Kripto & pinning

`javax.crypto` 92 · `AES/CBC` 1 · `AES/GCM` 0 · `RSA/ECB` 0 ·
**`CertificatePinner` 287 · `TrustManager` 296** — OkHttp TLS pinning hadir
(lebih eksplisit dibanding GoPay Merchant yang 0 di smali). CA/pin aktual +
efektivitas bypass **BELUM TERVERIFIKASI** — TODO-DYN-1.

### 4.3 Secret & kredensial (semua dimasking)

- **M1:** `[FOUND] Google API key: AIza…E0ROM (len=39,
  AndroidManifest.xml → meta-data com.google.android.geo.API_KEY)`.
  Dampak tergantung restriksi API di konsol Google — **BELUM TERVERIFIKASI**
  (TODO-ST-3). Tidak ada string `AIza` di direktori smali yang dipindai
  (2,3,4,5,9 + res — parsial).
- **R1:** URL `https://go-resto-v2.firebaseio.com` di `res/values/strings.xml`
  (nama instance; rules tidak diuji — probing dilarang; TODO-NET-4).
- `default_web_client_id`: `2582…bco4.apps.googleusercontent.com`
  (OAuth client ID — identifier publik, bukan secret).
- Tidak ada: blok PEM (`-----BEGIN`), file `values.xml` google-services,
  `google_app_id`/`gcm_defaultSenderId`/`project_id` di `res/values`,
  `const-string` bernama `hmac/client_secret/private_key/signing_key/aes_key`
  (3 dex dipindai, nilai tidak pernah dicetak).
- **Pernyataan eksplisit (sesuai spek): tidak ditemukan kredensial statis
  (AES/HMAC/signing key) di client** — konsisten dengan arsitektur server-side
  signing (token diterbitkan server, GoID SSO). Konfirmasi runtime TODO-DYN-1.
- `assets/` hanya berisi `address_facet_details.json` **0 byte** (placeholder).

### 4.4 Kegagalan tool (dicatat jujur)

- `jadx` **tidak dijalankan** (keputusan sadar setelah jadx 1.5.6 OOM/diam di
  analisis GoPay Merchant pada sandbox 2 GB). Seluruh temuan kode dari smali +
  strings — flow antar-class **BELUM TERVERIFIKASI** (TODO-ST-4).
- `apktool` selesai (730 MB, exit 0) dengan jejak stack-trace non-fatal di log
  (1 file gagal salin — `brut.directory.DirUtil`; manifest + smali + res utuh).
- `aapt dump xmltree` gagal total (seperti GoPay); atribut dibaca via androguard
  + manifest hasil apktool (nama atribut ter-mangle `="…"`, nilai valid).
- Hitungan §4.1–4.2 adalah sampel 3/16 dex (TODO-ST-1); sapuan URL/path §5
  mencakup **penuh** `smali*` (16/16).

## 5. Inventaris jaringan & API (statis)

> String statis — host aktif, header, dan auth runtime **BELUM TERVERIFIKASI**
> (TODO-NET-1). Daftar path lengkap mesin-terbaca:
> `APK_GOFOOD_MERCHANT_5.49.0_ENDPOINTS.txt`.

### 5.1 Host

| Host | Peran (indikasi) |
|---|---|
| `api.gojekapi.com` | API Gojek umum |
| `goid.gojekapi.com` | **Auth GoID** (SSO Gojek) |
| `i.gojekapi.com` | CDN darkroom (+ diizinkan cleartext, M2) |
| `api.gobiz.co.id` | **Gateway merchant GoBiz** |
| `app.gobiz.co.id` | Web merchant: `/micro-app/pos`, `/onboarding/pos/activated`, `/verify-onboarding/intro` |
| `app.gobiz.com` | Statis merchant: `/files/static/gobiz-instant/bank_list.json` |
| `customer.gopayapi.com` | API customer GoPay |
| `gopay.co.id` | T&C GoPay |
| `mpp-tnc-cos.golabs.io` | T&C GoBiz (`gobiz_tnc_2025_04_15.html`) |
| `privy.id` | Tanda tangan elektronik (KYC/registrasi) |
| `findaya.com` | Kebijakan privasi Findaya (lending) |
| `assets.goidentitas.id` | Aset identitas |
| Staging/dev: `customer.staging.gopayapi.com`, `i-integration.gojekapi.com`, `accounts-integration.goto-products.com` | M3 |
| `play.google.com/store/apps/details?id=com.gojek.gopaymerchant` | Cross-promo ke GoPay Merchant |

### 5.2 Endpoint (dikelompokkan)

- **Auth & PIN** (paymentsdk — SAMA dengan GoPay Merchant):
  `/api/v1/users/pin/{challenges,tokens}`, `/api/v1/users/pins/{allowed,reset/tokens,setup/tokens}`,
  `/api/v2/challenges/{challenge-id}/pin-page`, `/api/v2/users/pins/{reset,setup}/tokens`,
  `/v2/users/pin/update`, `/v3/users/pin/update`
- **GoFood merchant:** `gofood/merchant/v1/config`,
  `/gofood/merchant/v2/ocr/catalog/predict` (OCR katalog!)
- **EDC/kartu/offline:** `/v1/edc/createtoken`, `/v2/charge`,
  `/v2/point_inquiry`, `/v3/balance_inquiry`, `/v2/order/{id}/channel`,
  `/v2/{identifier}/{status,cancel,reversal}`,
  `/v2/{transaction_id}/event/edc/metadata/{event_name}`
- **Settlement & payout:** `/v3/settlement`, `/v3/auto-payout-settings/search`
- **Change-request:** `/v1/change_requests`,
  `/v3/change_requests{,/search,/validate,/{container_id}}`,
  `/v3/status_mapping`, `/v3/addresses/update_requests{,/{id}}`,
  `/v3/outlet_profiles/update_requests{,/{facet_id}}`, `/v3/{facet_path}/config`
- **Onboarding workflow:** `/use_cases/v1/processes{,/{process_id},…/init,…/steps/*}`
  (steps: ProductEligibility, SelectProduct, AddOutletDetails,
  AddBankAccountDetails, ValidateBankAccountDetails, SubmitKYC,
  SubmitOnboardingData), `/public/workflow/v1/change-bank-account/*`,
  `/v1/onboardings/upload_url`, `/v3/documents/upload_url`,
  `/v1/individual-entity-gfma/{execution_id}{,/product-eligibility,/select-product,/submit-kyc}`,
  `/v3/register`, `/v1/users/validate_eligibility`
- **Chat & device:** `/v1/chat/profiles/me`, `/v3/chat/channels/{id}`,
  `/v1/devices/push_token`, `/v1/instantfeedback{,/{channel_name}}`
- **Konten & search:** `/v1/api/{article/{id},feedback/reasons,feedback/submit,nanoarticle,search,search/common}`,
  `/v2/api/articlegroup{,/{id}}`, `/v3/api/articlegroup`,
  `/ui/v1/app/{merchantId}/conversion_funnel_page`
- **Payments:** `/v1/payments/search`

### 5.3 Protokol

HTTPS default + `network-security-config` aktif (**M2**):
`cleartextTrafficPermitted=true` untuk `i.gojekapi.com`,
`i-integration.gojekapi.com`, `s3.amazonaws.com`, `lite.privydev.id`
(CDN/gambar + domain dev Privy — intersepsi pada host ini dimungkinkan).
Tidak ada string `wss://` di smali (berbeda dari GoPay Merchant) dan tidak ada
string gRPC — realtime kemungkinan via FCM/push (`/v1/devices/push_token`,
`FirebaseNotificationHandler`) — **BELUM TERVERIFIKASI** (TODO-NET-3).

### 5.4 Relasi GoFood ↔ GoBiz ↔ GoPay-Merchant (bukti statis)

1. **GoFood ∈ keluarga GoBiz (erat):** gateway `api.gobiz.co.id`, web
   `app.gobiz.co.id` (POS micro-app + onboarding), skema **`gobiz://`**,
   `bank_list.json` GoBiz, T&C GoBiz 2025.
2. **GoPay Merchant ↔ GoFood:** `queries` paket `com.gojek.gopaymerchant` +
   string Play Store-nya (cross-launch/promo); sertifikat `CN=Gojek` identik;
   SDK bersama (paymentsdk PIN — path **identik persis**, SSO, narad, OneKyc).
3. **Gateway berbeda:** GoFood→GoBiz BFF; GoPay Merchant→raccoon/midtrans/gopayapi.
   **Overlap endpoint QRIS: tidak ditemukan secara statis** (GoPay punya
   `transactions/charge/qris-link` + `qris/shared`; GoFood punya `v2/charge`
   berorientasi EDC) — TODO-NET-2.
4. Kesimpulan sementara: **sister apps GoTo dengan SSO+SDK bersama, BFF terpisah.**

## 6. Library native (split arm64)

| Library | Ukuran | Identifikasi |
|---|---|---|
| `libb12.so` | 3,7 MB | Tidak dikenal (simbol OpenMP `__kmp_copyright` — komputasi native/ML?) — TODO-ST-6 |
| `libaf-android.so` | 2,1 MB | AppsFlyer |
| `libucrop.so` | 1,2 MB | Image cropping (Yalantis uCrop) |
| `libf2b8.so` | 932 KB | Tidak dikenal — TODO-ST-6 |
| `libgb367f.so` | 552 KB | OneKyc digitalidentity native (`com/iab/digitalidentity/…`) |
| `libI01vdxl32Da.so` | 420 KB | Tidak dikenal — TODO-ST-6 |
| `libc1ee9e.so` | 32 KB | JNI graphics helper (`libjnigraphics`) |
| `libe2102.so` | 12 KB | Stub (string versi SDK) — TODO-ST-6 |
| `libabd756.so` | 12 KB | Stub tak dikenal — TODO-ST-6 |
| `libdf5755.so` | 8 KB | Stub tak dikenal — TODO-ST-6 |

## 7. Analisis dinamis — TIDAK DILAKUKAN

Alasan terverifikasi: sandbox tanpa KVM/emulator/device (`adb`/perangkat tidak
ada; `frida`/`mitmproxy` tanpa target Android tidak berguna). Runtime behavior,
hooking kripto/jaringan, dan intersepsi traffic: **BELUM TERVERIFIKASI**
(TODO-DYN-1). Template "hentikan jika malware" tidak terpicu (tidak ada indikator
malware). Prosedur lanjutan: install split via APKPure installer/bundletool di
emulator terisolasi → hook OkHttp pinning + `javax.crypto` → mitmproxy dengan CA
sistem (antisipasi kegagalan bypass pinning + Play Integrity).

## 8. Perbandingan Play Store — TODO

TODO-REL-1: bandingkan `versionCode 247` + hash dengan listing Play dari perangkat.
Bukti pengganti parsial: stamp `play.google.com/store` + sertifikat Gojek valid.
TODO-REL-2: uji re-sign/repack (diprediksi menggugurkan v2-signature).

## 9. Verdict keamanan

- **Malware:** tidak ada indikator konklusif (bersih-secara-statis).
- **Keaslian:** sertifikat Gojek (+Baskara Patria/GO-JEK) + stamp Play valid.
- **Risiko utama bersifat postur** (M1–M3, R1–R5) — butuh konfirmasi dinamis
  sebelum diklaim kerentanan.

## 10. Rekomendasi

1. (M1) Restriksi geo API key per aplikasi Android + rotasi.
2. (M2) Hapus `lite.privydev.id` dari cleartext; pertimbangkan HTTPS penuh CDN.
3. (M3) Pisahkan konstanta staging dari build rilis.
4. (R2–R3) Minimalisasi permission (khusus kontak-tulis, telepon, BT) + rationale.
5. (R4–R5) Cabut exported `PreviewActivity`; persempit skema deeplink (`http`/`*`).
6. Umum: ulangi tiap rilis minor; lengkapi hitungan 16 dex (TODO-ST-1).

## 11. Relevansi untuk QrisMerchantID

Kandidat endpoint prioritas (butuh capture untuk host+header+auth):

1. `api.gobiz.co.id` + `/v1/payments/search`, `/v3/settlement` — kandidat BFF
   merchant terpadu (GoBiz) yang kemungkinan juga melayani data GoPay Merchant.
2. `/v2/charge`, `/v3/balance_inquiry`, `/v1/edc/createtoken` — flow charge/EDC;
   bandingkan dengan `transactions/charge/*` GoPay Merchant (TODO-NET-2).
3. PIN SDK (`/api/v*/users/pins/*`, `/v*/users/pin/update`) — **identik dengan
   GoPay Merchant**: pola auth PIN dapat dipakai ulang antar riset.
4. `gofood/merchant/v1/config` — config BFF; `/use_cases/v1/processes/*` —
   mesin workflow onboarding (bukan target integrasi, tapi peta akun/outlet).
5. GoID (`goid.gojekapi.com`) + SSO provider — kandidat auth terpadu; token
   kemungkinan server-issued (tidak ada static secret di client).

## 12. Log reproduksibilitas

- Tool: `apktool 2.7.0-dirty`, `aapt` (Debian), `androguard 4.1.4`, `unzip`,
  `strings`, OpenJDK 11, Python 3.13. `jadx` tidak dijalankan (alasan §4.4).
- Perintah inti (urutan):
  1. `curl -sSL -A <browserUA> -e https://apkpure.com/ -o gofood.xapk
     "https://d.apkpure.com/b/XAPK/com.gojek.resto?version=latest"`
     → 82.192.045 byte, `application/octet-stream` (via `data.winudf.com`)
  2. Hash container: MD5 `45deddf2…8628a`, SHA1 `370c6d20…0a796`,
     SHA256 `0f25c79cbd05d952dc40cdcfdc072d0b249a2f310c633b951be68f45fe6a9942`
  3. `unzip -l gofood.xapk` → `com.gojek.resto.apk` + 2 split + icon + manifest.json
  4. `unzip -o gofood.xapk -d work <semua apk+manifest+icon>`
  5. `sha256sum work/*.apk` (§1); `aapt dump badging` → identitas + 46 permission
  6. `apktool d -o work/base work/com.gojek.resto.apk` (730 MB di `/tmp`, dihapus)
  7. Skrip androguard → komponen + sertifikat + flag aplikasi (§1–§3)
  8. `grep -rho 'https\?://…'` seluruh `smali*` → 180 string URL (§5.1)
  9. Sapuan path + `const-string` + `res/values` + `assets` (§5.2, §4.3)
  10. Netsec: `res/xml/2132213767.xml` + referensi `@xml/2132213767` di manifest
- Artefak tersimpan: laporan ini + `APK_GOFOOD_MERCHANT_5.49.0_ENDPOINTS.txt`.
  XAPK 82 MB + decode 730 MB **dihapus** (unduh ulang via URL §12.1 + verifikasi
  SHA256 §1).
