---
title: Panduan agen — memakai KB QRIS merchant
date: 2026-09-11
sources:
  - docs/KB_QRIS_MERCHANT_INDEX.md
  - reference/MANIFEST.md
status: guide
version: "1.0"
---

# Panduan Agen — KB QRIS Merchant

## 1. Aturan verifikasi (recap, WAJIB)

1. Setiap klaim punya bukti: `file:line`, hash, atau perintah.
2. Tidak terbukti → tulis **BELUM TERVERIFIKASI** + TODO yang tepat.
3. Kredensial selalu masking (`prefix…suffix (len=N)`); jika ragu → masking.
4. Kata "mungkin/kemungkinan" dilarang tanpa penanda BELUM TERVERIFIKASI.
5. Reproducibility > kelengkapan. Jangan mengarang endpoint/host.

## 2. Cara baca `reference/`

- `*.csv`: baris pertama `# sources:` adalah komentar (bukan header); header sebenarnya di baris
  kedua; delimiter koma standar.
- `endpoints.csv`: `apk_sumber` ∈ {keduanya, GoPay-only, GoFood-only}; `terverifikasi` = "ya (string
  statis)" artinya string ada di APK, BUKAN endpoint aktif; `dipakai_runtime` selalu BELUM
  TERVERIFIKASI.
- `hosts.csv`: kolom `catatan` menandai staging (M3) vs produksi.
- Kode TODO memakai alias KB (`GOPAY-*`/`GOFOOD-*`/tanpa prefix) — lihat `reference/KONFLIK.md`
  TODO-KB-1 untuk pemetaan ke kode laporan asal.

## 3. Cara jawab pertanyaan umum

- "Endpoint apa untuk X?" → grep `endpoints.csv` kolom `grup` (auth-pin, histori, keuangan,
  transaksi-qris, edc-kartu, settlement, …).
- "Apakah Y aman?" → cek `temuan_keamanan.csv` (kolom `status`: indikasi-statis ≠ kerentanan) + TODO
  terkait.
- "Bagaimana integrasi Z?" → `deeplinks.md` + `endpoints.csv` grup relevan + §4 KB index
  (prioritas); selalu sertakan TODO-NET-1 sebagai syarat runtime.
- "Apakah data ini benar?" → lacak `apk_sumber` → laporan S1/S2 §tercantum → `MANIFEST.md` (hash).

## 4. Anti-pattern (dilarang)

1. Mengklaim endpoint "aktif/berfungsi" tanpa capture (pelanggaran TODO-NET-1).
2. Mencetak nilai kredensial mentah (lihat `credentials.md`).
3. Menyimpulkan kerentanan dari indikator statis saja (gunakan kata "indikasi").
4. Memilih salah satu sisi data konflik tanpa mencatat di `KONFLIK.md`.
5. Mengutip path absolut (`/home/user/...`) — selalu path relatif repo.

## 5. Contoh Q&A terverifikasi

**Q1: Endpoint apa untuk riwayat transaksi GoPay Merchant?** A: `/api/v1/unified-histories` +
`/filter`, `/api/v2/histories` (`reference/endpoints.csv`, grup `histori`, apk_sumber GoPay-only).
Keyakinan: SEDANG (string statis, runtime BELUM TERVERIFIKASI, TODO-NET-1).

**Q2: Apakah kedua APK memakai auth PIN yang sama?** A: Ya, 6 path PIN IDENTIK persis
(`reference/endpoints.csv` grup `auth-pin`, `sdk_bersama.md`). Keyakinan: TINGGI (2 sumber: S1 §5.2

+ S2 §5.2/S3).

**Q3: Apakah API key GoFood bocor dan berbahaya?** A: Key `AIza…E0ROM (len=39)` terverifikasi ada di
manifest (`reference/credentials.md`), TETAPI dampaknya BELUM TERVERIFIKASI (GOFOOD-TODO-ST-3) —
bergantung restriksi konsol Google. Status: indikasi, bukan kerentanan terkonfirmasi.

**Q4: Bagaimana cara realtime-notifikasi di GoFood Merchant?** A: BELUM TERVERIFIKASI. Tidak ada
string `wss://` (S2 §5.3); kandidat: FCM (`/v1/devices/push_token`). TODO: GOFOOD-TODO-NET-3.

**Q5: Bisakah token GoPay Merchant dipakai di GoFood?** A: BELUM TERVERIFIKASI — pertanyaan riset
terbuka #2 (`KB_QRIS_MERCHANT_INDEX.md` §6). Jangan interpolasi.

Kembali ke: [KB index](KB_QRIS_MERCHANT_INDEX.md) · [MANIFEST](../reference/MANIFEST.md)

## TODO aktif

- Tidak ada (dokumen panduan).
