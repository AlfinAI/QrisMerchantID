---
title: Responsible disclosure — riset APK merchant
date: 2026-09-11
sources:
  - research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md
status: disclosure
version: "1.0"
---

# Responsible Disclosure — Riset APK Merchant

> **Untuk tim keamanan GoTo/GoPay/GoFood (atau siapa pun yang berwenang):** dokumen ini merangkum
> apa yang kami temukan, bagaimana menemukannya, dan bagaimana menghubungi kami. Kami peneliti
> independen, **tidak terafiliasi**.

## 1. Ruang lingkup & metode (jujur)

- Objek: APK publik GoPay Merchant 2.3.0 (APKMirror) dan GoFood Merchant 5.49.0 (APKPure). Hash
  SHA256 tercatat di `reference/MANIFEST.md`.
- Metode: **analisis statis saja** (apktool, androguard, strings) di sandbox terisolasi. **Tidak
  ada** eksekusi APK, intersepsi traffic produksi, probing backend, pengujian kredensial, atau akses
  data pengguna.
- Klasifikasi kami: **0 kritis**. Semua temuan M/R adalah *indikator statis*, bukan kerentanan
  terkonfirmasi — detail + bukti per temuan ada di laporan §0 dan `reference/temuan_keamanan.csv`.

## 2. Ringkasan temuan (indikator, bukan vonis)

| ID           | Subjek                                                 | Indikator                            | Bukti        |
| ------------ | ------------------------------------------------------ | ------------------------------------ | ------------ |
| GOPAY-M1     | API key tertanam (1 string)                            | Nilai tidak terekam (hanya hitungan) | S1 §4.3      |
| GOPAY-M2/M3  | `allowBackup` default; URL staging di rilis            | Manifest + strings                   | S1 §3, §4.3  |
| GOFOOD-M1    | API key geo di manifest (`AIza…E0ROM`, len=39)         | `AndroidManifest.xml` meta-data      | S2 §4.3      |
| GOFOOD-M2    | Cleartext untuk 4 domain (termasuk `lite.privydev.id`) | `network-security-config`            | S2 §5.3      |
| GOFOOD-M3/R1 | URL staging; nama instance Firebase DB                 | strings + `strings.xml`              | S2 §4.3/§5.1 |

Rekomendasi teknis per temuan: S1 §10 dan S2 §10 (restriksi key, hapus dev domain dari cleartext,
pisahkan flavor staging, minimalisasi permission).

## 3. Yang TIDAK kami lakukan (komitmen)

1. Tidak mempublikasikan nilai kredensial mentah (semua masking).
2. Tidak menguji rules Firebase / validitas API key terhadap layanan live.
3. Tidak mengklaim kata "vulnerability/exploit" — hanya "indikator".
4. Tidak mendistribusikan ulang file APK (artefak dihapus pasca-analisis).

## 4. Kontak & tindak lanjut

- Kontak peneliti: Telegram **[@JoestarMojo](https://t.me/JoestarMojo)** · Issue repo:
  [QrisMerchantID/issues](https://github.com/AlfinAI/QrisMerchantID/issues)
- Yang bisa kami bagikan atas permintaan resmi: hash lengkap, versi tool, kutipan output tool
  termasking, dan koreksi jika temuan keliru.
- Kebijakan: temuan dipublikasikan sebagai riset edukasional; jika ada masukan atau koreksi dari
  vendor, kami perbarui dokumen ini + `reference/CHANGELOG.md` maksimal 7 hari setelah kontak yang
  terverifikasi.

## 5. Riwayat

| Tanggal    | Kejadian                                                       |
| ---------- | -------------------------------------------------------------- |
| 2026-09-11 | Publikasi awal dokumen ini + KB v1.1 (belum ada kontak vendor) |

Kembali ke: [KB index](KB_QRIS_MERCHANT_INDEX.md)

## TODO aktif

- TODO-KB-5: perbarui §5 saat ada respons vendor (P2, owner: user).
