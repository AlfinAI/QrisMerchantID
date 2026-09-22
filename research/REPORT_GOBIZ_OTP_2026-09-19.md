# Laporan: GoPay `request_otp()` tidak work — analisa HAR + perbaikan

Tanggal: 2026-09-19 · Status: **implemented, UNCOMMITTED — menunggu review user** Sumber traffic:
`GOTO.har` (12,5 MB zip → 51 MB, 589 entries, capture 13:25–13:27 UTC, Firefox desktop →
`portal.gofoodmerchant.co.id` → `api.gobiz.co.id`).

> ⚠️ File HAR asli **MENGANDUNG KREDENSIAL LIVE** (access/refresh token JWE, nomor HP, email,
> `otp_token`) dan **TIDAK BOLEH di-commit** (repo sudah `.gitignore` `*.har`; file HAR hanya di
> `uploads/` lokal, di luar repo). Semua nilai sensitif di laporan ini **disensor penuh**
> (`<disensor>`); yang tercatat hanya FORMAT-nya (11 digit nasional bare, tanpa prefix).

## 1. Ringkasan eksekutif

Alur OTP portal per 19 Sep 2026 **bentuknya tidak berubah** — endpoint, body, dan mapping response
identik dengan implementasi QMID. Ditemukan **2 drift** yang masing-masing bisa menjelaskan "kirim
OTP gk work":

| #   | Drift                                                                                                                                         | Bukti                            | Fix                                                                   |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | --------------------------------------------------------------------- |
| 1   | `X-AppVersion` portal naik `v3.119.0-eab7f749` → **`v3.122.0-72edb090`**; QMID masih kirim yang lama di `/goid/*`                             | Header live §3.1                 | Bump `APP_VERSION`                                                    |
| 2   | Portal **tidak pernah** kirim nomor ber-prefix (11 digit nasional bare, `<disensor>`); QMID meneruskan prefix apa adanya (`0851…`, `+62851…`) | Body live §3.1 vs `auth.py` lama | Normalisasi ke format nasional bare + `ValueError` untuk input sampah |

Kandidat #1 relevan bila GoBiz mem-version-gate; kandidat #2 relevan bila user memasukkan nomor
format natural Indonesia (`08…`). Keduanya diperbaiki sekaligus karena keduanya adalah "tirulah
browser" yang terbukti dari traffic.

## 2. Metodologi

1. `GOTO.zip.json` ternyata **ZIP** → ekstrak → `GOTO.har` (51 MB, 589 entries).
2. Petakan semua host/path non-statis; isolasi 30 call `api.gobiz.co.id`.
3. Bedah penuh 2 call auth: `POST /goid/login/request` (→ 201 + `otp_token`) dan `POST /goid/token`
   (→ 201 + `access_token`/`refresh_token`/`dbl_enabled`).
4. Bandingkan header-per-header & body-per-body vs `gopay/client.py` + `auth.py`.
5. Verifikasi silang endpoint data (`merchants/search`, `journals/search`, `payouts*`, `users/me`,
   analytics) vs service QMID.
6. Terapkan fix minimal + tes offline, jalankan gate penuh.

## 3. Temuan traffic (yang penting saja)

### 3.1 `POST /goid/login/request` → 201 (kirim OTP)

Request (redacted): header device penuh + `Authentication-Type: go-id` + `Authorization: Bearer`
**kosong**; body:

```json
{"client_id": "go-biz-web-new", "phone_number": "<disensor: 11 digit bare>", "country_code": "62"}
```

Respons 201:

```json
{"data": {"otp_token": "17e37b1b-…", "otp_expires_in": 720, "otp_length": 4,
 "next_state": {"state": "sms", "destination": "", "timer_in_seconds": 120}},
 "success": true, "errors": []}
```

Header respons: `x-verification-method: otp`, rate-limit 10/mnt. OTP 4 digit.

### 3.2 `POST /goid/token` → 201 (verifikasi OTP)

```json
// request
{"client_id": "go-biz-web-new", "data": {"otp": "••••", "otp_token": "17e37b1b-…"},
 "grant_type": "otp"}
// response keys
{"access_token": "eyJ…(JWE dir/A128GCM, 2279 char)",
 "refresh_token": "eyJ…(751 char)", "dbl_enabled": true}
```

Call ber-auth berikutnya memakai `Authorization: Bearer <access_token>` + `Authentication-Type:
go-id` (contoh: `GET /v1/users/me` → 200).

### 3.3 Diff header-per-header (OTP request: live vs QMID-lama)

17 header live; **16 identik**, satu-satunya beda fungsional:

| Header                        | Live 19 Sep 2026                 | QMID lama                                                              |
| ----------------------------- | -------------------------------- | ---------------------------------------------------------------------- |
| `X-AppVersion`                | `platform-v3.122.0-72edb090`     | `platform-v3.119.0-eab7f749` ❌                                         |
| `User-Agent` / `X-PhoneModel` | Firefox 156 (browser si perekam) | Chrome 149 (default lama) — kosmetik, pasangan konsisten, tidak diubah |

Split-header design tetap valid: `X-AppVersion` **NOL** kemunculan di luar `/goid/*` (589 entries
di-scan).

### 3.4 Endpoint data — status vs QMID

| Endpoint                                                 | Hasil                                                                                                                                                      |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `merchants/search`                                       | ⚠️ Portal kini selalu sertakan `_source:[...]` (1 call pakai `{from,to}`); bare `{from,size}` (§9.1) tak terlihat lagi — tapi tanpa bukti rusak (lihat §5) |
| `journals/search` (+ `JOURNAL_HEADERS`)                  | ✅ identik                                                                                                                                                  |
| `payouts?page=1&per=10`, `payable_detail?merchant_id=G…` | ✅ identik dengan default SDK                                                                                                                               |
| `users/me`, analytics GET                                | ✅ identik                                                                                                                                                  |
| `POST /v2/users/public/search`                           | 🆕 baru terlihat (user-management) — di luar scope mutasi, SKIP                                                                                             |
| raccoon `/events`, litmus, grafana proxy, OneTrust       | Telemetri/iklan — abaikan                                                                                                                                  |

## 4. Root cause (ranking)

1. **`X-AppVersion` basi (paling mungkin bila input nomor sudah bare).** Satu-satunya byte
   fungsional yang beda di call OTP. GoBiz/GoTo dikenal mem-version-gate client portal ("please
   update"); server bisa menolak atau mengabaikan OTP untuk versi basi tanpa pesan yang jelas.
2. **Prefix nomor HP (paling mungkin bila input `08…`/`+628…`).** Portal selalu kirim bare `851…`;
   QMID-lama meneruskan `0851…` apa adanya. Kombinasi `country_code:62` + `0851…` = nomor invalid
   (`620851…`) di sisi server.
3. Bukan penyebab: endpoint, body shape, response mapping, token exchange, header lain — semuanya
   identik dan bekerja di traffic live ini.

Catatan jujur: pesan error persis dari sisi user tidak tersedia ("gk work" tanpa screenshot error);
kedua fix di atas adalah satu-satunya deviasi dari traffic live, jadi keduanya diperbaiki (prinsip
repo: *tiru browser, byte-per-byte*).

## 5. Perubahan kode (uncommitted)

| File                                    | Perubahan                                                                                                                                     |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/qrismerchantid/gopay/constants.py` | `APP_VERSION` → `platform-v3.122.0-72edb090` (+ atribusi §9.4)                                                                                |
| `src/qrismerchantid/gopay/auth.py`      | `request_otp()` normalisasi: strip spasi/`-`/`.`/`(`/`)`, prefix `+`, prefix `country_code`, satu `0` depan; `ValueError` bila sisa < 7 digit |
| `tests/test_gopay_auth.py`              | Update 2 ekspektasi lama ke format bare + 2 tes baru (matriks 6 format nomor, 7 input sampah → `ValueError`)                                  |
| `docs/gopay/README.md`                  | Contoh `app_version` → versi baru                                                                                                             |
| `research/RESEARCH_GOPAY_SHOPEEPAY.md`  | §9.4: hasil capture kedua + keputusan                                                                                                         |
| `CHANGELOG.md`                          | Entri `Fixed` di Unreleased                                                                                                                   |

**Sengaja TIDAK diubah:** `USER_AGENT`/`PHONE_MODEL` (mengikuti browser perekam, kosmetik, pasangan
default tetap konsisten); body `merchants/search` (bare `{from,size}` terverifikasi §9.1; `_source`
hanya proyeksi field — TODO-R2: verifikasi ulang bila search bertingkah); endpoint
`/v2/users/public/search` (di luar scope).

## 6. Verifikasi

Gate penuh hijau (offline, tanpa API riil):

- `pytest`: **180 passed** (178 lama + 2 baru), coverage total **100%**
- `ruff check` + `ruff format --check`: bersih (44 file)
- `mypy src` (strict): bersih (24 file)

## 7. Checklist review (commit atau tidak?)

- [ ] Setuju bump `X-AppVersion` ke `v3.122.0` (mengikuti traffic 19 Sep 2026)?
- [ ] Setuju normalisasi nomor (perilaku berubah: `0851…` kini dikirim sebagai `851…`; input sampah
      kini `ValueError` lokal, bukan error server)?
- [ ] Sisa risiko: **belum ada live-proof** — butuh kirim OTP sungguhan ke nomor real untuk
      konfirmasi final ( scaffolded: `request_otp("0851…")` lalu cek SMS).
- [ ] File HAR/zip tetap di `uploads/` (tidak ikut repo) — jangan commit.

Perintah setelah ACC: `git add -A && git commit -m "fix(gopay): ..." && git push` (menunggu
token/order seperti biasa).

## 8. Addendum — login email+password (HAR kedua, 19 Sep 2026)

Sumber: `emialku.har.json` (Reqable, 169 entries, 19 detik: buka `/login` → 2 call goid →
dashboard). Semua 2xx — TIDAK ada contoh gagal di capture ini.

| Call                       | Shape live (disensor)                                                                                                | vs QMID                 |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| `POST /goid/login/request` | `{email:'<disensor>', login_type:'password', client_id:'go-biz-web-new'}` → 201 `{data:{}, success:true, errors:[]}` | ✅ persis                |
| `POST /goid/token`         | `{client_id, grant_type:'password', data:{email, password}}` → 201 `{access_token, refresh_token, dbl_enabled:true}` | ✅ persis                |
| Headers                    | `X-AppVersion: platform-v3.122.0-72edb090` (sama seperti HAR OTP)                                                    | ✅ konsisten dgn bump §4 |

**TODO-R1 CLOSED** — login email terverifikasi live (dulu hanya ikut repo referensi). Prasyarat
(permintaan user): akun merchant **HARUS sudah set email+password di portal**; bila belum, server
menolak. Bentuk error persis "email belum di-set" TIDAK ada di capture → **TODO-R3** (petakan saat
temukan traffic gagal). Mitigasi kini: validasi format email + password non-kosong di client
(`ValueError` lokal, tanpa panggil API), error server tetap diteruskan apa adanya via
`ApiException`.

**Pilihan login (opsional, user pilih salah satu):**

- OTP: `request_otp(phone)` → SMS 4 digit → `login_with_otp(otp, otp_token)`
- Email: `login_with_password(email, password)` (syarat: email+password sudah di-set)
