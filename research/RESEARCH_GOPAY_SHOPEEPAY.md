# RISET: GoPay Merchant & ShopeePay Unofficial API

Tanggal: 2026-09-11 · Status: **riset kode selesai, BELUM verifikasi runtime** Tujuan: memetakan
repo/referensi kode untuk project next (SDK Python GoPay/ShopeePay). Metode: clone 8 repo + bedah
kode + GitHub API search + web search. Semua klaim endpoint berasal dari kode yang dibaca (jalur
file dicantumkan); klaim "masih work" hanya untuk repo yang di-test user (warungerik) — sisanya
BELUM TERVERIFIKASI runtime.

> Aturan main (konsisten dengan project ovoid): tidak ada kredensial di repo, riset untuk edukasi,
> atribusi ke repo sumber hukumnya WAJIB kalau kita port/contek polanya.

## Ringkasan eksekutif

1. **GoPay Merchant (GoBiz) = ekosistem matang.** Auth + endpoint mutasi terdokumentasi penuh di
   kode terbuka (`kavionn/gobiz-payment` paling lengkap; repo user `warungerik/API-GOPAY-MERCHANT` =
   versi rampingnya + full gateway, **sudah user-test ✓**).
2. **ShopeePay Partner = bisa diakses dua jalur.** Jalur cepat: token internal curian DevTools
   (`B:...`). Jalur dalam: login programmatic penuh (password→OTP→cookies) yang direverse
   `alhifnywahid/merchantid` (open-source, tested).
3. **Dua repo terbesar bintangnya semi-obfuscated** (`ahmadzakiyox/*`) — tetap berguna untuk
   README/arsitektur, tapi bukan referensi kode utama.
4. **GAP BESAR: tidak ada SATU PUN Python SDK** untuk GoPay merchant maupun ShopeePay partner. Semua
   referensi Node.js/PHP/TypeScript/Go. → Rekomendasi project next §6.

## 1. Peta ekosistem

### 1.1 GoPay Merchant / GoBiz (merchant-side: mutasi, QRIS, settlement)

| Repo                                                           | ★   | Bahasa | Push       | Kode                                                                          | Nilai                                                                                                                        |
| -------------------------------------------------------------- | --- | ------ | ---------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `ahmadzakiyox/gopay-api-gateaway`                              | 182 | JS     | 2026-07-25 | ⚠️ sebagian obfuscated (`login.js`, `sessionManager.js`; `server.js` terbuka) | Arsitektur gateway + klaim auto-refresh token 6 jam (BELUM TERVERIFIKASI)                                                    |
| `kavionn/gobiz-payment`                                        | 60  | JS     | 2026-09-07 | ✅ terbuka penuh + JSDoc                                                       | **REFERENSI UTAMA**: login password+OTP, merchants, analytics, journals, watcher                                             |
| `warungerik/API-GOPAY-MERCHANT`                                | 10  | Vue/JS | 2026-09-02 | ✅ terbuka                                                                     | Versi ramping pola kavionn (TANPA login OTP) + gateway lengkap (Nuxt 3, Supabase, Telegram, webhook HMAC). **User-tested ✓** |
| `namtxs/gopay-api`                                             | 93  | PHP    | 2024-06-02 | ✅ terbuka                                                                     | Customer-side (login OTP, balance, transfer, withdrawal) — pembanding, mungkin stale                                         |
| `IbraDecode/gopaymerchant`                                     | 6   | TS     | 2026-07-08 | ✅ terbuka                                                                     | Toolkit QRIS + payment (belum dibedah dalam — TODO)                                                                          |
| `ardianryan/qbiz-qrisdinamis`                                  | 7   | —      | —          | ✅ terbuka                                                                     | QRIS dinamis + HMAC webhook + integrasi POS                                                                                  |
| `xirf/gobiz-merchant-sdk`                                      | 1   | TS     | 2026-08-31 | ✅ terbuka                                                                     | GoFood + GoPay merchant SDK                                                                                                  |
| `azmi2409/gopay-merchant-qris-gateway`                         | 0   | TS     | 2026-09-10 | ✅ terbuka                                                                     | Baru (Sep 2026), REST v1 — kandidat segar                                                                                    |
| `nur900963-maker/gobiz-payment`, `Cylne/Web-GopayMerchant-Api` | ≤1  | JS     | Agu 2026   | —                                                                             | Kecil, prioritas rendah                                                                                                      |

### 1.2 ShopeePay Partner (merchant-side)

| Repo                                                                            | ★   | Bahasa  | Push       | Kode                                                              | Nilai                                                                                                         |
| ------------------------------------------------------------------------------- | --- | ------- | ---------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `ahmadzakiyox/shoppepay-api-gateway`                                            | 155 | JS      | 2026-09-07 | ⚠️ `server.js` OBFUSCATED penuh (`server-raw.js` tidak di-upload) | **README emas**: cara curi token, flow stateless, anti-collision. Kode tidak bisa dibaca                      |
| `alhifnywahid/merchantid`                                                       | 27  | TS      | 2026       | ✅ terbuka + vitest                                                | **REFERENSI UTAMA**: login ShopeePay programmatic penuh + provider GoPay & Shopee + QRIS dinamis + reconciler |
| `pkbarellano/shopeepay-api`                                                     | 1   | PHP/CI3 | 2026-07-30 | ✅ terbuka                                                         | ⚠️ ZONK: skeleton middleware, tidak ada upstream ShopeePay asli di kodenya                                    |
| `adhiva/go-shopeepay-wrapper`                                                   | 2   | Go      | 2020-10-31 | ✅ terbuka                                                         | Stale (2020), arsip saja                                                                                      |
| `Pengendali-API/ShopeePay`                                                      | 0   | —       | 2024-03-20 | —                                                                 | ZONK: cuma README link Play Store                                                                             |
| Official: `mu-hanz/shoapi`, `minchao/shopee-php`, `raviMukti/shopee-api-client` | —   | PHP     | —          | ✅ terbuka                                                         | ⚠️ Scope BEDA: Shopee Open Platform (seller/order/produk, butuh partner_id resmi) — BUKAN wallet ShopeePay    |

## 2. GoPay Merchant API (GoBiz) — temuan teknis

Sumber utama: `kavionn_gobiz-payment/gobiz.js` (dibaca penuh) + `gopay-merchant/gobiz.js` (600
baris, dibaca penuh) + `merchantid/.../gopayProvider.ts` (sebagian).

### 2.1 Auth — GoID (`https://api.gobiz.co.id`, `client_id: go-biz-web-new`)

**Login password** (warungerik + kavionn):

1. `POST /goid/login/request` body `{email, login_type: 'password', client_id}`
2. `POST /goid/token` body `{client_id, grant_type: 'password', data: {email, password}}` →
   `{access_token, refresh_token, expires_in}`

**Login OTP HP** (hanya kavionn, baris ~151-255):

1. `POST /goid/login/request` body `{login_type: 'otp', phone_number/country_code...}` →
   `{otp_token}` (kode dikirim via SMS)
2. `POST /goid/token` body `{client_id, grant_type: 'otp', data: {otp: kode, otp_token}}`

**Header wajib** (meniru portal web merchant): `Authentication-Type: go-id`, `X-User-Type:
merchant`, `x-appId: go-biz-web-dashboard`, `X-Platform: Web`, `x-uniqueid: <uuid>`, `X-AppVersion:
platform-v3.107.0-...`, `Origin/Referer: https://portal.gofoodmerchant.co.id`, UA Chrome,
`Gojek-Country-Code: ID`, `Gojek-Timezone: Asia/Jakarta`.

**Quirk penting:**

- Login dieksekusi via **binary `curl -4`** (IPv4 eksplisit) pakai `execFileSync`, bukan `fetch` —
  indikasi masalah TLS/IPv6 හෝ fingerprinting (BELUM TERVERIFIKASI alasannya).
- Token di-cache di file (`.gopay_cache.json` / `.GOPAY_SESI_JANGAN_DIHAPUS.json`); tiap request 401
  → login ulang otomatis.
- Zaki mengklaim auto-refresh token tiap 6 jam (kode obfuscated → BELUM TERVERIFIKASI).

### 2.2 Endpoint

| Method | Host + Path                                                     | Body / Param                                                              | Fungsi                                            |
| ------ | --------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------- |
| POST   | `api.gobiz.co.id/v1/merchants/search`                           | `{from, to, _source: ['id','merchant_name']}`                             | Daftar merchant + **validasi token** (401 = mati) |
| GET    | `api.gobiz.co.id/v1/users/me`                                   | —                                                                         | Profil merchant (dari merchantid)                 |
| GET    | `api.gojekapi.com/merchant-analytics/v2/merchants/transactions` | `from, size, statuses, payment_types, start_time, end_time, merchant_ids` | **Mutasi utama**                                  |
| POST   | `api.gobiz.co.id/journals/search`                               | Query DSL (`included_categories`, `clauses`, rentang waktu, merchant_id)  | Mutasi detail (fallback)                          |

`statuses`: `SETTLEMENT,CAPTURE,REFUND,PARTIAL_REFUND`. `payment_types`:
`QRIS,GOPAY,OFFLINE_CREDIT_CARD,OFFLINE_DEBIT_CARD,CREDIT_CARD`. **Nominal = minor units**
(`gross_amount / 100`).

### 2.3 Watcher pattern (semua gateway GoPay pakai ini)

Polling `getHistory({days:1, size:30})` tiap ±6 detik → seed awal (tandai semua SEEN, jangan emit) →
emit event `payment` hanya untuk tx baru → `waitForPayment(amount, {timeout: 5 mnt, tolerance})`
resolve saat nominal cocok → dedup by `transaction_id ?? id ?? order_id`, cache 500 terakhir.
Timeout = invoice gagal.

### 2.4 QRIS dinamis (pola umum, ada di semua gateway)

Parse QRIS statis sebagai EMVCo TLV → suntik nominal ke tag `54` → hitung ulang **CRC16-CCITT** →
render QR baru. Rekomendasi anti double-claim: tambah kode unik Rp1–99 ke nominal + dedup
`transactionId` 24 jam.

## 3. GoPay Customer API — pembanding (namtxs, Jun 2024, BELUM TERVERIFIKASI masih work)

Hosts: `goid.gojekapi.com` (OTP: `/goid/login/request`, `/goid/token`), `api.gojekapi.com`
(`/v1/users/transaction-history`, `/v1/users/kyc/status`, `/v1/users/p2p-profile`),
`customer.gopayapi.com` (`/v1/payment-options/balances`, `/v1/funds/transfer`, `/v1/banks`,
`/v1/withdrawals`, `/v1/withdrawals/detail`, `/v1/bank-accounts/validate`). Fitur: login OTP, saldo,
history, profil, transfer GoPay/bank, QRID, GoClub, paylater. File:
`namtxs_gopay-api/src/GojekPay.php` (~250 baris, 1 class).

## 4. ShopeePay Partner API — temuan teknis

Sumber utama: `alhifnywahid_merchantid/src/providers/shopee/*` (dibaca: constants, struktur
`authClient/loginService/deviceRisk/cookieJar/crypto`) + README `ahmadzakiyox_shoppepay-api-gateway`
(dibaca penuh).

### 4.1 Hosts

| Host                                     | Peran                                                      |
| ---------------------------------------- | ---------------------------------------------------------- |
| `partner.shopee.co.id`                   | Portal merchant (web)                                      |
| `shopeepay.shopee.co.id`                 | **Merchant API** (`/merchant/v1/partner-web/*`)            |
| `api.partner.shopee.co.id`               | MSS API (`/nb/mss/...`: merchant-detect, user-info, probe) |
| `partner.business.accounts.shopee.co.id` | SSO/passport (login programmatic)                          |
| `df.infra.sz.shopee.co.id`               | Fraud/device-risk SDK (wajib sebelum OTP)                  |

### 4.2 Auth — dua jalur

**Jalur cepat (zaki, tanpa kode login):** login manual di portal → F12 Network → cari
`get-transaction-list` → payload `data.metadata.token` (prefix `B:`) → pakai sebagai `SHOPEE_TOKEN`.
Multi-store via header `X-Shopee-Token` per request.

**Jalur programmatic (merchantid, full reverse):** `/api/v4/account/business/check_password_migrate`
→ `authenticate_toc_by_password` → `48401102` (NeedOTP = password benar, lanjut OTP) →
`get_otp_settings` → `send_otp` (channel: 1 SMS, 2 voice, 3 **WA (default)**, 4 email, 5 zalo;
operation `50001`) → `verify_otp` → `authenticate_toc_by_otp` → `login_toc`. Sesi = cookies `SPC_*`

+ `__shopee_partner_website_x_token_live`; probe `login_status` (`48500102` = harus OTP ulang); lalu
  `MerchantDetect` / `SwitchMerchant` / `GetUserInfo`. Token mati permanen: kode `200020` (terminal
  — jangan retry, wajib sesi baru!) dan `2010000`. Client IDs: business `1`, account `5`; Referer
  SSO harus persis (kalau tidak, OTP di-suppress diam-diam!).

### 4.3 Endpoint transaksi

| Method | Path (di `shopeepay.shopee.co.id`)                | Catatan                                                     |
| ------ | ------------------------------------------------- | ----------------------------------------------------------- |
| POST   | `/merchant/v1/partner-web/get-store-list`         | Page size 30, services `[1, 10]`                            |
| POST   | `/merchant/v1/partner-web/get-transaction-list`   | Page size **10**, services `[1, 3]`, status completed = `3` |
| POST   | `/merchant/v1/partner-web/get-transaction-detail` | Issuer resolution (Seabank/OVO/DANA/BCA/...)                |

### 4.4 Flow gateway (zaki, stateless/client-polled)

`POST /create-qris {amount}` (inject Tag 54 + CRC16, seperti §2.4) → tampilkan QR → toko polling
`POST /check-payment {amount, startTime}` tiap 10–15 dtk selama checkout aktif (saat sepi = 0
request → anti rate-limit) → kalau ketemu, ambil detail pengirim → `{paid: true, transaction}` +
dedup `transactionId` di RAM 24 jam.

## 5. Pola arsitektur gateway (umum, semua repo)

`QRIS statis → inject nominal → halaman checkout → polling cek bayar → lunas → webhook HMAC-SHA256
ke toko + notif Telegram`. Database opsional (Supabase/Postgres di warungerik; 100% stateless di
zaki-ShopeePay). Anti double-claim selalu ganda: kode unik nominal + dedup transactionId.

## 6. Gap analysis → rekomendasi project next

**Fakta:** tidak ada satu pun Python SDK untuk GoPay merchant / ShopeePay partner / GoPay customer.
PyPI kosong di niche ini (perlu cek ulang saat eksekusi).

| Opsi | Nama                                                                                       | Basis referensi                           | Tingkat kesulitan                   |
| ---- | ------------------------------------------------------------------------------------------ | ----------------------------------------- | ----------------------------------- |
| A    | `gobiz-python` — SDK merchant GoPay (login, merchants, mutasi, watcher, QRIS dinamis)      | kavionn (open) + warungerik (user-tested) | ⭐ rendah — pola 1:1 dari JS         |
| B    | `shopeepay-python` — SDK partner ShopeePay (login OTP/cookies, stores, transactions, QRIS) | merchantid (open, tested)                 | ⭐⭐ sedang — flow SSO lebih berlapis |
| C    | `payid-python` — payung multi-provider (gopay + shopeepay + ovoid)                         | pola provider merchantid + GetPay         | ⭐⭐⭐ setelah A & B jadi              |

**Rekomendasi: A → B → C.** A bisa jalan tercepat (user sudah punya akun merchant GoBiz yang
tested). B butuh akun ShopeePay Partner. Keduanya butuh **verifikasi runtime dengan akun asli**
(TODO-R1..Rn, seperti FASE ovoid).

## 7. Clone lokal (`/home/user/research-payid/`)

`gopay-merchant/` (warungerik), `kavionn_gobiz-payment/`, `namtxs_gopay-api/`,
`ahmadzakiyox_gopay-api-gateaway/`, `ahmadzakiyox_shoppepay-api-gateway/`,
`alhifnywahid_merchantid/`, `pkbarellano_shopeepay-api/`. Total ±9 MB, depth-1.

## 8. TODO lanjutan (saat eksekusi project)

- TODO-R1: ~~verifikasi login GoBiz~~ ✅ TERVERIFIKASI via HAR: OTP flow persis (§9.1), password flow
  persis (§9.5) — FULLY CLOSED. Sisa: uji live login password + refresh-token flow dari SDK.
- TODO-R2: ~~verifikasi respons mentah~~ ✅ TERVERIFIKASI via HAR (§9): analytics, journals (varian
  agregasi), payouts, merchant detail, users/me. Sisa: uji live dari SDK + crosscheck tampilan
  portal untuk skala nominal (keyakinan tinggi: sen).
- TODO-R3: verifikasi login ShopeePay programmatic (butuh akun partner + nomor WA).
- TODO-R4: bedah `IbraDecode/gopaymerchant` + `azmi2409/gopay-merchant-qris-gateway` (TS segar).
- TODO-R5: (opsional, prioritas rendah) deobfuscate `server.js` ShopeePay zaki untuk konfirmasi
  parameter `get-transaction-list`.

## 9. Verifikasi HAR — capture browser asli portal GoBiz (Sep 2026) ✅

Sumber: `har/gobizverbrowser.har` (80 MB, 1063 entries, 77 API calls; iPhone WebView `mark.via.gp` →
`portal.gofoodmerchant.co.id`). SEMUA nilai di bawah ini DIANONIMKAN — file HAR asli + zip-nya
**MENGANDUNG KREDENSIAL LIVE (token, email, HP, no. rekening) dan TIDAK BOLEH di-commit** (wajib
`.gitignore` di project turunan).

### 9.1 Hasil verifikasi (riset §2 vs traffic asli)

| Temuan riset                                                     | Hasil HAR                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /goid/login/request` → `POST /goid/token`                  | ✅ persis; keduanya HTTP **201**                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Login OTP: request → `otp_token` → verify                        | ✅ `{client_id, phone_number, country_code:'62'}` → `{data:{otp_token, otp_expires_in:720, otp_length:4, next_state:{state:'sms', timer_in_seconds:120}}}` → `/goid/token {grant_type:'otp', data:{otp, otp_token}}` → `{access_token, refresh_token, dbl_enabled:true}`                                                                                                                                                                                                                              |
| `POST /v1/merchants/search`                                      | ✅ body asli `{from:0, size:20}` → `{total, success, hits:[...]}`                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `GET /v1/users/me`                                               | ✅ `{user:{id,email,full_name,phone,language,merchant_id,roles[],scopes{60+},...}}`                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Analytics `GET .../merchant-analytics/v2/merchants/transactions` | ✅ query persis (`from,size,statuses,payment_types,start_time,end_time,merchant_ids`); objek tx 23 keys: `id, wallstreet_transaction_id, order_id (QRIS-...), transaction_status, payment_type, *_time, gross_amount:int, real_gross_amount:int, currency:IDR, service_type, channel_type (STATIC_QR), transaction_source (GOPAY_INSTORE), qris_provider_rrn, qris_on_us, qris_provider_aspi_issuer/acquirer, merchant_cross_reference_id, shares[], promo_details{}, transaction_history[], version` |
| `POST /journals/search` (query DSL)                              | ✅ + varian AGREGASI terverifikasi: `{size:0, time_range:{gte,lt}, aggs:{by_qris_issuer:{terms:{field:'metadata.provider_metadata.aspi.issuer'}}}}` → `{success,total,total_relation,hits:[],aggregations}`                                                                                                                                                                                                                                                                                           |
| Nominal minor units (÷100)                                       | ✅ konsisten: analytics `gross_amount` int 7–8 digit; payouts string desimal skala sama                                                                                                                                                                                                                                                                                                                                                                                                               |

### 9.2 Koreksi terhadap kode referensi

1. **Browser TIDAK mengirim `login_type`** di `/goid/login/request` (kavionn mengirim
   `login_type:'otp'`) — field itu opsional/diabaikan. SDK harus meniru browser.
2. **`X-AppVersion` live = `platform-v3.119.0-...`** (referensi: `v3.107.0`) — SDK pakai default
   baru + bisa override. (Catatan 19 Sep 2026: disupersede oleh §9.4 → `v3.122.0`.)
3. **Split header**: header device lengkap (`X-User-Type`, `X-PhoneModel`, `x-appId`, `x-uniqueid`,
   ...) HANYA di call `goid/*`; data call lebih ramping. Semua call browser membawa
   `X-Requested-With: mark.via.gp` (penanda WebView — opsional).
4. **Header khusus journals**: `Accept: ...application/vnd.journal.v1+json` + `X-Client-Id:
   gobiz-web`.

### 9.3 Endpoint BARU (tidak ada di repo referensi mana pun)

| Endpoint                                                   | Respons                                                                                                                                                           |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET /v1/merchants/payouts?page&per`                       | `{payouts:[{payout_id, merchant_id, net/gross/refund_amount, fee/mdr breakdown, status:'paid', created/paid_at, account_no, ...}], current_page, per, next_page}` |
| `GET /v1/merchants/payouts/payable_detail?merchant_id=`    | `{payable_detail:{payable, net_amount, total_settlement, fees, adjustments[], ...}}`                                                                              |
| `GET /v1/merchants/{id}` (detail, format ID `G` + 9 digit) | Objek merchant penuh: KYC, outlet, bank, `payment_settings{...VA bank/retail...}`, `active_payment_channels[]`                                                    |
| `POST /v2/onboardings/search`                              | Onboarding outlet (`add_outlet`) — kosong di akun ini; SKIP untuk SDK v1                                                                                          |
| `GET /goresto/v5/public/users/config?merchant_id=`         | Roles + permissions granular — SKIP untuk SDK v1 (`users/me` cukup)                                                                                               |

Abaikan untuk SDK: `gobiz-web-raccoon.gojekapi.com/api/v1/events` (beacon analitik),
`api.gojekapi.com/litmus/run/experiments` (feature flags).

### 9.4 Capture kedua — `GOTO.har` (19 Sep 2026, Firefox desktop)

Sumber: login → dashboard portal (589 entries, 13:25–13:27 UTC). Pemicu: user lapor `request_otp()`
tidak work. File HAR **MENGANDUNG KREDENSIAL LIVE dan TIDAK BOLEH di-commit** (sama seperti §9).

| Area                                             | Hasil vs §9.1–§9.3                                                                                                                                                                                                                               |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `POST /goid/login/request` body                  | ✅ identik: `{client_id:'go-biz-web-new', phone_number:'<disensor: 11 digit nasional bare>', country_code:'62'}` — TANPA `login_type`, nomor TANPA prefix 0                                                                                       |
| `POST /goid/login/request` headers               | ⚠️ `X-AppVersion` naik `platform-v3.119.0-eab7f749` → **`platform-v3.122.0-72edb090`**; sisanya identik (termasuk `Authorization: Bearer` kosong)                                                                                                |
| `POST /goid/token`                               | ✅ identik: `{client_id, grant_type:'otp', data:{otp(4 digit), otp_token}}` → 201 `{access_token, refresh_token, dbl_enabled:true}`                                                                                                               |
| Split header goid vs data                        | ✅ masih berlaku (`X-AppVersion` NOL kemunculan di luar `/goid/*`)                                                                                                                                                                                |
| `POST /v1/merchants/search`                      | ⚠️ portal kini selalu menambah `_source:[...]` (1 call pakai `{from,to}` tanpa `size`); body bare `{from,size}` §9.1 TIDAK terlihat lagi — TETAP dipakai SDK (terverifikasi §9.1, tanpa bukti rusak; TODO-R2: verifikasi ulang bila search aneh) |
| Analytics / journals / payouts / `users/me`      | ✅ identik (query params, DSL, `JOURNAL_HEADERS`, `?page=1&per=10`)                                                                                                                                                                               |
| `POST /v2/users/public/search` (user-management) | 🆕 terlihat pertama kali — SKIP untuk SDK (di luar scope mutasi)                                                                                                                                                                                  |

Keputusan (shipped, belum live-proof — butuh OTP sungguhan): bump `APP_VERSION`, normalisasi nomor
HP ke format nasional bare (portal tidak pernah kirim prefix). Detail lengkap:
`research/REPORT_GOBIZ_OTP_2026-09-19.md`.

### 9.5 Capture ketiga — login email (`emialku.har.json`, 19 Sep 2026)

Reqable, 169 entries / 19 detik (buka `/login` → 2 call goid → dashboard). Semua 2xx. Nilai disensor
penuh (format saja yang dicatat).

| Call                       | Shape live                                                                                                           |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `POST /goid/login/request` | `{email, login_type:'password', client_id:'go-biz-web-new'}` → 201 `{data:{}, success:true, errors:[]}`              |
| `POST /goid/token`         | `{client_id, grant_type:'password', data:{email, password}}` → 201 `{access_token, refresh_token, dbl_enabled:true}` |
| Headers                    | `X-AppVersion: platform-v3.122.0-72edb090` — konsisten dgn §9.4                                                      |

**TODO-R1 FULLY CLOSED** (OTP §9.1 + password di sini): `login_with_password()` persis sama dengan
traffic live (sebelumnya hanya ikut kavionn/gobiz-payment). **TODO-R3 BARU**: bentuk error server
saat akun BELUM set email+password belum tercapture (semua call di HAR ini sukses) — petakan saat
ada traffic gagal. Prasyarat tetap didokumentasikan: email+password harus sudah di-set di portal.
