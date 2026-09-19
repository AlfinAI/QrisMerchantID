---
title: Panduan reproduksi riset APK (untuk learner & porter)
date: 2026-09-11
sources:
  - research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md
  - research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md
status: guide
version: "1.0"
---

# Panduan Reproduksi Riset APK Merchant

Dokumen ini menjelaskan **persis bagaimana** riset APK di repo ini dilakukan, sehingga kamu bisa:
(a) memverifikasi ulang temuan kami, (b) menganalisis versi APK yang lebih baru, (c) mem-port
pengetahuan ini ke bahasa/SDK lain. Semua klaim di sini merujuk pada laporan sumber — tidak ada
langkah rahasia.

Contoh hasil yang bisa kamu pelajari strukturnya:

- `research/APK_GOPAY_MERCHANT_2.3.0_ANALYSIS.md` (Flutter + Kotlin, APKM)
- `research/APK_GOFOOD_MERCHANT_5.49.0_ANALYSIS.md` (native, XAPK)
- Data mesin-terbaca: `reference/hosts.csv`, `reference/endpoints.csv`

## 1. Prasyarat jujur

| Kebutuhan      | Minimum                                                         | Catatan                                                  |
| -------------- | --------------------------------------------------------------- | -------------------------------------------------------- |
| OS             | Linux x86_64 (kami: Debian)                                     | Perintah memakai `apt`, `curl`, `unzip`                  |
| RAM            | 4 GB (2 GB **tidak cukup** untuk jadx — terbukti OOM, lihat §7) | apktool + androguard jalan di 2 GB                       |
| Disk sementara | ±1 GB di `/tmp`                                                 | Decode GoFood = 730 MB; **jangan** decode di folder repo |
| Jaringan       | Akses APKMirror/APKPure/GitHub                                  | URL unduhan bisa kedaluwarsa → cari versi terbaru        |

## 2. Instalasi tool

```bash
sudo apt-get update && sudo apt-get install -y apktool aapt unzip binutils
pip install androguard
# jadx: OPSIONAL, butuh RAM besar. Tanpa jadx pun analisis smali+strings cukup.
# (jadx 1.5.6: https://github.com/skylot/jadx/releases — aset bernama jadx-1.5.6.zip TANPA huruf v)
```

Verifikasi versi dan **catat di laporanmu** (contoh kami: apktool 2.7.0-dirty, androguard 4.1.4,
OpenJDK 11, Python 3.13).

## 3. Langkah reproduksi (urutan wajib)

### 3.1 Unduh container (APKM / XAPK)

```bash
# Pola APKMirror (GoPay Merchant) — key dapat berubah, ambil dari halaman unduhan:
curl -sSL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/152" \
  -e "https://www.apkmirror.com/" -o app.apkm "<download.php?id=...&key=...>"

# Pola APKPure (GoFood Merchant):
curl -sSL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/152" \
  -e "https://apkpure.com/" -o app.xapk \
  "https://d.apkpure.com/b/XAPK/<package>?version=latest"
```

### 3.2 Hash + identifikasi isi

```bash
md5sum app.apkm && sha1sum app.apkm && sha256sum app.apkm
file app.apkm                  # harus: Zip archive data
unzip -l app.apkm               # APKM: base.apk + split_config.* ; XAPK: <pkg>.apk + config.*.apk + manifest.json
```

### 3.3 Ekstrak base + split ABI

```bash
mkdir -p work && cd work
unzip -o ../app.apkm base.apk info.json            # sesuaikan nama (XAPK: <pkg>.apk, manifest.json)
sha256sum base.apk
unzip -o ../app.apkm split_config.arm64_v8a.apk
mkdir -p arm64 && cd arm64 && unzip -o ../split_config.arm64_v8a.apk 'lib/*'
find . -name "*.so" -exec du -h {} \; | sort -rh   # inventaris native (§6 laporan)
```

### 3.4 Identitas + permission

```bash
aapt dump badging base.apk   # package, versionCode/Name, SDK, permission
```

### 3.5 Decode (apktool, di /tmp!)

```bash
apktool d -o base base.apk    # 50–730 MB. Catat error non-fatal apa pun.
```

### 3.6 Manifest + sertifikat (androguard)

```python
from androguard.core.apk import APK
a = APK("base.apk")
print(a.get_package(), a.get_androidversion_name(), a.get_androidversion_code())
print(a.get_min_sdk_version(), a.get_target_sdk_version(), a.get_main_activity())
print(sorted(set(a.get_permissions())))
for fn in (a.get_activities, a.get_services, a.get_receivers, a.get_providers):
    print(sorted(fn()))
for c in a.get_certificates():
    print(c.subject.human_friendly, hex(c.serial_number))
xml = a.get_android_manifest_xml()  # baca atribut application: allowBackup, dsb.
```

### 3.7 Exported components + deeplink + netsec

```bash
grep -o '<[a-z-]*[^>]*android:exported="true"[^>]*' base/AndroidManifest.xml
grep -o 'android:scheme="[^"]*"' base/AndroidManifest.xml | sort -u
grep -o 'android:host="[^"]*"' base/AndroidManifest.xml | sort -u
# network-security-config: cari res/xml/*.xml berisi <network-security-config>
# applink @string/<id>: resolve via res/values/public.xml (hex id) -> res/values/strings.xml
```

### 3.8 Sapuan URL/host (smali + native)

```bash
# Smali (semua dex):
grep -rhoh 'https\?://[A-Za-z0-9._~:/?#@!$&()*+,;=%-]*' base/smali* | sort -u
# Flutter (jika ada libapp.so): strings -n 6 arm64/lib/arm64-v8a/libapp.so > libapp.txt
# lalu grep pola yang sama + pola path: grep -oh '/api/[A-Za-z0-9_./{}-]*' libapp.txt | sort -u
```

### 3.9 Sapuan secret (WAJIB masking di output!)

```bash
# JANGAN pernah print nilai mentah. Pola deteksi saja, lalu mask manual:
grep -rhoh 'AIza[0-9A-Za-z_-]\{35\}' base/smali* base/res 2>/dev/null | wc -l   # hitung dulu
grep -o '<string name="[^"]*">[^<]*' base/res/values/strings.xml | grep -iE "google|gcm|firebase|sender|project"
grep -o '<meta-data[^>]*>' base/AndroidManifest.xml   # cek API_KEY — SENSOR sebelum mencatat!
grep -rhoh '-----BEGIN [A-Z ]*-----' base/smali* base/res base/assets 2>/dev/null  # PEM (header saja, aman)
```

Aturan masking kami: `AIza…E0ROM (len=39)` — 4 char awal + 4 char akhir + panjang.

### 3.10 Sinyal anti-tamper / kripto / pinning

```bash
for w in frida xposed isRooted RootBeer SafetyNet PlayIntegrity attest emulator qemu ptrace debugger; do
  printf "%s " "$w"; grep -roi "$w" base/smali* 2>/dev/null | wc -l
done
for w in javax.crypto AES/GCM AES/CBC RSA/ECB CertificatePinner TrustManager; do
  printf "%s " "$w"; grep -roi "$w" base/smali* 2>/dev/null | wc -l
done
```

**Catat cakupan sapuanmu** (contoh: "3 dari 16 dex" jika tidak penuh).

### 3.11 Tulis laporan

Ikuti struktur `research/APK_*_ANALYSIS.md` (§0–§12): ringkasan → metadata → permission → komponen →
statis → jaringan → native → dinamis (jujur jika tidak dilakukan) → verdict → rekomendasi →
relevansi → log reproduksibilitas. Setiap angka harus bisa dilacak ke perintah di §12.

### 3.12 Bersih-bersih

```bash
rm -rf /tmp/work   # decode ratusan MB jangan masuk repo/snapshot
```

Simpan di repo: laporan + hash + (opsional) daftar endpoint terfilter.

## 4. Checklist porter (bahasa/SDK lain)

1. Ambil `reference/endpoints.csv` + `hosts.csv` sebagai titik awal — JANGAN klaim endpoint "aktif"
   (semuanya TODO-NET-1).
2. Petakan grup `auth-pin` dulu (satu-satunya yang identik lintas-APK = pola paling stabil).
3. Untuk setiap endpoint yang kamu implementasi: butuh capture traffic sendiri (host, method,
   header, auth, signing) — string statis tidak cukup.
4. Tiru aturan kami: full docstring/type-hint/test offline, atribusi sumber, tanpa kredensial
   hardcoded.
5. Kirim kembali temuanmu (issue/PR) — KB ini hidup dari kontribusi.

## 5. Etika & batasan (dibaca sebelum mulai)

- Riset ini **statis + edukasional** atas APK yang didistribusikan publik.
- Dilarang: probing backend orang lain, mengekstrak data pengguna, mempublikasikan secret mentah,
  mengklaim kerentanan dari indikator statis saja.
- Bukan afiliasi GoTo/GoPay/GoFood/Shopee. Baca `SECURITY_DISCLOSURE.md`.

Kembali ke: [KB index](KB_QRIS_MERCHANT_INDEX.md)

## TODO aktif

- Tidak ada (dokumen panduan).
