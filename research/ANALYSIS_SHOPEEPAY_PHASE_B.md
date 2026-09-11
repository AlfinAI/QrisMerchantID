# ANALISA FASE B: Provider ShopeePay (`shopee/`)

Tanggal: 2026-09-11 · Status: **analisa kode selesai, BELUM verifikasi runtime**
Sumber: `alhifnywahid/merchantid` v0.1.1 (3.535 baris provider Shopee + 6 dokumen
`docs/shopee/*.mdx`, dibaca penuh — authClient, api, token, crypto, deviceRisk,
cookieJar, httpClient, merchantClient, transactionFeed, types, login/sessions/
merchants-stores/payments/device-risk) + README `ahmadzakiyox/shoppepay-api-gateway`
(442 baris, dibaca penuh — kodenya obfuscated, hanya README yang dipakai).

> Aturan main: temuan di bawah ini 100% berasal dari kode/dok yang dibaca (jalur
> file dicantumkan). Yang belum bisa dibuktikan tanpa akun Partner ditandai TODO-S.

## 0. Ringkasan eksekutif + putusan feasibility

1. **Feed transaksi + stores + profil = straightforward di Python.** Token `B:...`
   + cookies via `httpx` (cookie handling bawaan — tidak perlu cookieJar custom
   seperti merchantid).
2. **Login OTP programmatic = feasible TAPI berlapis** (3 step, 9+ endpoint,
   cookie SSO, JWT). Satu-satunya ganjalan serius: **device-risk blob** — tanpa
   telemetry fraud-SDK, OTP di-suppress diam-diam (§5).
3. **Jalur pragmatis (zaki-style): tempel token `B:...` manual** dari DevTools →
   langsung akses feed tanpa login flow. Direkomendasikan sebagai **B1** (value
   cepat), login programmatic sebagai **B2** (advanced).
4. **QRIS = tidak ada kerja baru.** ShopeePay static QRIS manual (user supply);
   inject Tag 54 + CRC16 sama persis dengan `qris.py` GoPay kita — reuse 100%.
5. **Nominal ShopeePay = RUPIAH UTUH, bukan minor units!** (`"409.662"` = Rp409.662
   — format grup Indonesia pakai titik). Beda dari GoPay (sen). Wajib parser khusus.
6. **Butuh akun ShopeePay Partner + nomor WA** untuk verifikasi runtime (TODO-S1).
   Tanpa itu B1/B2 hanya teruji offline (seperti A1/A2 sebelum HAR).

## 1. Arsitektur merchantid (validasi desain kita)

`merchantid` = registry + adapter per provider; auth/session/discovery/pagination/
normalisasi dimiliki adapter (AGENTS.md, berbahasa Indonesia). Prinsip yang kita adopsi:

- `MerchantID` tidak memaksakan login universal → `QrisMerchantID` kita sudah benar:
  `core/` milik bersama, `gopay/` dan `shopee/` adapter mandiri.
- Payment matching = nominal unik + waktu + status + **PaymentScope**
  (provider/account/merchant-store) agar tx satu store tak melunasi store lain.
  → Watcher ShopeePay kita harus scope-aware (store_id wajib).
- Feed GoPay = offset-based; feed ShopeePay = **cursor-based** (`next_position`).
- Peringatan mereka: "library ini memindahkan uang sungguhan" — ambang ketelitian
  rekonsiliasi tinggi. Kita read-only, tapi prinsip kehati-hatian tetap dipakai.

## 2. Login ShopeePay — 3 step OTP (programmatic, B2)

Akun: nomor HP format e164 (`628…`) + password HANYA bila akun password-protected
(tanpa password di akun tsb, `send_otp` lapor sukses tapi kode ditahan diam-diam!).

### Step 1 — `requestOtp(phone, password?, channel?, deviceReport?)`

1. `GET {ACCOUNT}/login?lang=id` (bootstrap cookies anonim: csrftoken, SPC_*, language).
2. `POST df.infra.sz.shopee.co.id/v2/shpsec/web/report` — tukar device-report blob
   → `riskToken` (full `24,80,16,2,1` vs degraded `24,76,…`, §5).
3. `POST /api/v4/account/business/check_password_migrate` `{phone}`.
4. `POST …/check_account_exist_by_password` → `{has_password, otp_channel[], otp_default_channel}`.
5. `POST …/authenticate_toc_by_password` `{phone, password_hash, …}` → kode
   `48401102` (NeedOTP) = password benar, lanjut OTP. Password wire transform:
   **`sha256Hex(md5Hex(password))`** (crypto.ts:237 — trivial di Python via hashlib).
6. `POST …/get_otp_settings` `{operation: 50001, phone, security_device_fingerprint,
   support_session: false, supported_channels: [1,2,3,5]}` → channel default (3 = WA).
7. `POST …/send_otp` `{…, supported_channels: [1,2,3,5,4], channel, captcha_signature: ""}`
   → `{seed?}`. Channel: 1 SMS, 2 voice, 3 WA (default), 4 email, 5 zalo.
8. Hasil: challenge `{phoneNumber, channel, availableChannels, deviceFingerprint,
   riskToken, hasPassword, cookies(snapshot), requestedAt}`.

### Step 2 — `verifyOtp(challenge, otp 4–10 digit)`

1. Restore cookies challenge → `POST …/verify_otp` `{operation, otp,
   phone: "(+62) 897 7110 640" (format grup BERSPASI — compact e164 DITOLAK!),
   security_device_fingerprint, support_session: false}` → `{otp_token}`.
2. `POST …/authenticate_toc_by_otp` `{otp_token, security_device_fingerprint,
   is_signup: false}` → `{toc_nonce, toc_account: {userid}}`.
3. Ambil cookie `SPC_CLIENTID` → `followGet {PARTNER}/account/login/auth
   ?lang&spc_clientid&state&toc_nonce` (hop SSO, penting!).
4. `POST {PARTNER_API}/nb/mss/mer-detect-api/PartnerMerchantDetectServer/MerchantDetect`
   `{}` + `partnerHeaders({tocNonce})` → `{selectMerchant: {merchantList: [...]}}`.
5. Hasil: verification `{tocNonce, tocUserId, spcClientId, deviceFingerprint,
   cookies, merchants[{id, name, status, staffUserId, staffRole, isActive, isBanned}], verifiedAt}`.
   Verification reusable untuk pilih merchant tanpa OTP kedua.

### Step 3 — `completeLogin(verification, merchantId?, storeId?)`

1. Pilih merchant (auto bila tepat 1 usable; tolak bila inactive/banned).
2. `followGet {ACCOUNT}/authenticate/login/token/?lang&spc_clientid&state
   &tob_userid={staffUserId}&next={PARTNER}/account/login/tob/auth
   &client_id=5&toc_nonce=…`.
3. `POST …/login_toc` → `{nonce}` → lanjut ke `/account/login/tob/auth`.
4. **Baca kredensial dari cookie JWT** `__shopee_partner_website_x_token_live`
   (token.ts): payload `{token (= B:...), userid, businessId?, exp?}`.
5. Ambil profil (GetUserInfo) + seluruh stores → session
   `{cookies, token, accountId, merchantId, storeId, switchCredential, …}`.

### Sesi, refresh, ganti merchant (B2, tanpa OTP ulang)

- `login_status` (`POST …/login_status {}`): `error: 0` = hidup; `48500102` = mati.
  **Satu-satunya sinyal liveness yang jujur** — `exp` JWT (~1000 hari) TIDAK berarti!
- `refreshSession()`: cek `login_status` → ulangi SSO exchange → token baru.
  Token BEROTASI tiap refresh → caller wajib persist ulang (`onSessionUpdated`).
- `selectMerchant(id)`: ulangi token-exchange (`login_toc` → `tob/auth`) untuk
  staff merchant tujuan. **JANGAN pakai endpoint `SwitchMerchant` headless** —
  tokennya ditolak dashboard (`200020`) di luar browser sungguhan!
- `switchCredential` (materi SSO) = se-sensitif cookie; sesi impor-cookie-mentah
  tanpanya tidak bisa refresh/ganti merchant.

## 3. Feed transaksi (B1 — inti FASE B)

`POST https://shopeepay.shopee.co.id/merchant/v1/partner-web/get-transaction-list`

Headers (`paymentHeaders`): `Origin/Referer: partner.shopee.co.id`,
`X-Timestamp-Ms: <now>`, `X-Token: ""` (kosong — token lewat body!).

Body:

```json
{"data": {"metadata": {"token": "B:…", "language": "id", "timezone": "Asia/Jakarta"},
  "pageSize": 10, "filter": {"startTime": 1784050000, "endTime": 1784053600,
  "serviceList": [1, 3]}, "sorter": {"field": "createTime", "order": "descend"},
  "next_position": ""}}
```

- `startTime/endTime` = epoch DETIK (bukan ms, bukan ISO — beda dari GoPay!).
- `pageSize` maks terverifikasi = 10. `serviceList` = `[1, 3]`.
- Paginasi cursor: `next_position` ("") → ulang sampai kosong; guard anti
  cursor-tidak-maju (cursor sama/berulang = error, jangan infinite loop).
- Respons: envelope payment `{code: 0, msg, data: {list: [...], next_position}}`.
- Row: `{transactionId: "264693445089687719" (18 digit),
  externalTransactionId?, displayTransactionId?, createTime (epoch detik),
  storeId, service, amount: "409.662" (STRING grup-ID!), status: 3,
  transactionType, merchantId}`.
- **status `3` = satu-satunya completed yang terobservasi.**
- Map status lengkap dari `server.js` ter-deobfuscate: `{1: pending, 2: failed,
  3: success, 4: refunded, 5: expired}` → kolom `status_name` (TODO-S4 CLOSED).
- Detail issuer: `GET get-transaction-detail?order_sn=<displayTransactionId ||
  transactionId>` → `data.issuer` (TODO-S2 CLOSED; runtime = TODO-S1). zaki
  mengirim `pageSize: 100` — KAMI TETAP 10 (100 belum terverifikasi, §7).
- Respons list juga membawa `totalNetSales` (agregat, bukan per-row).
- **Amount = rupiah utuh berformat Indonesia**: `"409.662"` → 409662;
  `"1008"` → 1008. Parser: terima `^\d+$` atau `^\d{1,3}(\.\d{3})+$`, strip titik.
  Selain itu = undefined (jangan crash-kan polling!).
- Normalisasi: tolak row tanpa id/amount/time valid atau merchant/store di luar
  scope; dedup by `transactionId`; `orderId = external ?? display ?? transactionId`.

## 4. Stores + profil (B1)

- `POST …/merchant/v1/partner-web/get-store-list`, body
  `{data: {metadata, storeName: "", lastStoreId: 0 (cursor!), pageSize: 30,
  serviceList: [1, 10]}}` → `{list: [{storeId, storeName, status}], storeCount}`.
  Cursor = `lastStoreId` (int, dari store terakhir); berhenti saat batch < 30 /
  kosong / total tercapai; guard cursor-tidak-maju.
  **Unfiltered retry**: bila filter `serviceList` menghasilkan NOL, ulangi TANPA
  key `serviceList` (bukan array kosong!) agar store tanpa service tetap ketemu.
- `POST {PARTNER_API}/nb/mss/web-api/PartnerAccountServer/GetUserInfo` `{}` +
  `partnerHeaders({token})` (`X-Merchant-Token`, `X-Merchant-RequestId` uuid fresh
  + `shopee-baggage` WAJIB — mer-detect menolak tanpanya!) →
  `{merchantId, merchantName, store_id, tobUserId, tocUid, userName, language,
  shopeepay_service_status, …}`. Cocokkan `merchantId` dengan sesi (tolak bila beda).

## 5. Device-risk — caveat terbesar port Python

Fraud SDK browser mem-POST blob telemetry ke
`df.infra.sz.shopee.co.id/v2/shpsec/web/report` (header `szdet`, SDK `1.12.26-user.1`)
→ `riskToken`. Tanpa telemetry: token degraded → **OTP di-suppress diam-diam**
(semua endpoint tetap lapor sukses!). Token dipakai sebagai
`security_device_fingerprint` + header `af-ac-enc-sz-token` di semua auth call.

merchantid me-replay SATU blob capture statis + peringatan jujur: fingerprint
bersama = akun saling ter-link, bisa mati massal bila di-flag, dan secara
substansi mengakali anti-fraud (risiko ToS/suspend). Alternatif jujur: user
capture blob sendiri dari browsernya (`deviceReport` param).

**Rekomendasi untuk kita**: B1 = token manual (tanpa device-risk sama sekali).
B2 = `device_report: str | None` (wajib user-supply, TIDAK dibundel default —
lebih aman & jujur daripada merchantid). Dokumentasikan cara capture + risikonya.

## 6. Envelope + error codes

| API | Sukses | Gagal |
|---|---|---|
| Account (SSO/passport) | `error: 0` + `data` | else → auth error; `captcha_required: true`/msg captcha → CaptchaRequired |
| Partner (mss) | `errorCode: 0` + `data` | else; invalid-token → auth error, sisanya API error |
| Payment (merchant feed) | `code: 0` + `data` | sama seperti partner |

Kode penting: `48401102` NeedOTP (password OK), `48500102` not-login,
`200020` NotAuthorized = **terminal** (jangan retry — sesi harus baru!),
`2010000` invalid token. Pesan mengandung token/auth/login/session ≈ auth error.

## 7. Cross-verifikasi: merchantid × zaki (2 sumber independen, cocok)

| Aspek | merchantid (kode) | zaki (README) | Status |
|---|---|---|---|
| Host feed | `shopeepay.shopee.co.id` | sama | ✅ |
| Token | body `data.metadata.token`, prefix `B:` | `SHOPEE_TOKEN=B:…`, cara curi via DevTools | ✅ |
| Endpoint list | `get-transaction-list` | sama | ✅ |
| Endpoint detail (issuer) | — (tidak ada) | `get-transaction-detail` → issuer (Seabank/OVO/DANA/BCA) | ✅ shape terungkap dari `server.js` ter-deobfuscate (TODO-S2 CLOSED) |
| `transactionId` 18 digit | `transactionId: string` | `"264693445089687719"` | ✅ |
| Amount grup-ID | parser `"409.662"` | `total_amount: "409.662"` | ✅ |
| QRIS dinamis | Tag EMV inject (src/qris) | Tag `54` + CRC16 + expiry 15 mnt | ✅ konsep sama |
| Anti double-claim | scope + consumed-ids | kode unik + dedup RAM 24 jam | ✅ pola sama |
| Multi-store | sessions/scope | header `X-Shopee-Token` | ✅ pola sama |

## 8. Gap & TODO-S (butuh akun Partner untuk verifikasi)

- TODO-S1: verifikasi runtime SEMUA endpoint (butuh akun ShopeePay Partner + nomor WA).
- TODO-S2: ✅ CLOSED 2026-09-11 — shape `get-transaction-detail` terungkap dari
  `server.js` (`order_sn` → `data.issuer`); sisa verifikasi runtime = TODO-S1.
- TODO-S3: `verify_otp` grouped-phone + NEED_OTP path — verifikasi live saat B2.
- TODO-S4: ✅ CLOSED 2026-09-11 — map `{1: pending, 2: failed, 3: success,
  4: refunded, 5: expired}` dari `server.js`; kolom `status_name` shipped.

## 9. Rencana build

**B1 — feed manual-token** (tanpa login flow): `shopee/constants.py` (hosts,
endpoints, codes, page sizes, services), `shopee/client.py` (payment envelope +
`paymentHeaders`/`paymentMetadata`, cursor helpers, error mapping → ApiException),
`shopee/stores.py` (`list_stores()` cursor + unfiltered retry), `shopee/transactions.py`
(`list_recent()` cursor + normalisasi + parser amount ID), `shopee/money.py`
(`parse_id_amount()` — rupiah utuh!), `ShopeePayPartner(token=…)` facade +
`watch()` (scope store-aware), tests offline, docs/gopay→docs/shopee/*, examples,
README ShopeePay section. Estimasi ≈ A1+A2 digabung (lebih ramping: tanpa auth).

**B2 — login OTP programmatic**: `shopee/auth.py` (3-step + JWT cookie read +
`hashShopeePassword` via hashlib + `device_report` user-supply), cookies via
httpx jar, `refresh_session()`, `select_merchant()`, session persist
(`token_cache` reuse), tests offline + docs. Estimasi ≈ A1. Terblokir parsial
oleh TODO-S1 (bisa dibangun offline, verifikasi belakangan).

**B3 — rilis**: README final, CHANGELOG, version `0.2.0`, tag + release GitHub,
re-publish PyPI (re-run workflow, tanpa pending-publisher baru — project sama!),
presentasi. Estimasi ringan.

## 10. Catatan keamanan (wajib masuk docs B1/B2)

- Challenge/verification/session objects = kredensial (cookies!) — jangan log/print.
- Token `B:...` = akses merchant penuh — `.env` + `.gitignore`, jangan hardcode.
- `device_report` milik user (capture sendiri); jelaskan risiko ToS shared-blob.
- Polling hanya saat checkout aktif (anti rate-limit), seperti GoPay.
