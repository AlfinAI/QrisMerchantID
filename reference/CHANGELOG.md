---
title: CHANGELOG knowledge base
date: 2026-09-11
sources: []
status: changelog
version: "1.0"
---

# CHANGELOG — KB QRIS Merchant

## [1.1] — 2026-09-11

- Dokumen publik: `docs/APK_RESEARCH_REPRODUCTION_GUIDE.md` (reproduksi + porting),
  `docs/SECURITY_DISCLOSURE.md` (disclosure untuk vendor).
- README utama: section Research menautkan KB + panduan + disclosure.
- TODO-KB-5 baru: update disclosure saat ada respons vendor.

## [1.0] — 2026-09-11

Sumber: S1 (GoPay Merchant 2.3.0), S2 (GoFood Merchant 5.49.0), S3 (endpoints GoFood).

- Kurasi awal: `hosts.csv` (35 host), `endpoints.csv` (6 path IDENTIK +
  ~160 GoPay-only + ~80 GoFood-only), `credentials.md` (masking penuh),
  `deeplinks.md`, `sdk_bersama.md`, `temuan_keamanan.csv` (16 baris),
  `KONFLIK.md` (TODO-KB-1 s.d. -3).
- Naratif: `docs/KB_QRIS_MERCHANT_INDEX.md` + `docs/KB_QRIS_MERCHANT_AGENT_GUIDE.md`.
- Index: `research/README.md`, `docs/README.md`.

Ringkasan: dua APK GoTo terkonfirmasi sister apps (sertifikat + 6 endpoint PIN
identik + SDK bersama), gateway terpisah (midtrans/raccoon vs gobiz BFF).
Runtime 100% BELUM TERVERIFIKASI — integrasi menunggu capture (TODO-NET-1).
