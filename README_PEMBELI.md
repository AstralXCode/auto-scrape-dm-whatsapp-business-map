# ASTRAL - Scraper + Auto WA DM v2.0

**Global UMKM Scraper + Auto WhatsApp DM + Auto Reply**

## Fitur

- Scrape bisnis dari Google Maps (200+ lokasi, 80+ negara)
- Auto DM WhatsApp bahasa lokal (13 bahasa)
- Auto-reply pesan masuk (7 bahasa)
- Multi-key SerpApi fallback (anti-limit)
- Rate limiting 70 DM/jam (anti-ban)
- Warm-up phase (anti-spam)
- PDF export otomatis
- Sound effects
- License system (trial 3 hari)

## Cara Install

### 1. Install Termux
Download dari F-Droid (bukan Play Store!)

### 2. Jalankan Installer
```bash
# Copy file scrape.py, astral_wa.js, install.sh ke Termux
# Lalu jalankan:
bash install.sh
```

### 3. Jalankan Script
```bash
python3 scrape.py
```

## Cara Pakai

### Pertama Kali
1. Jalankan `python3 scrape.py`
2. Masukkan **SerpApi key** (gratis di serpapi.com)
3. Pilih **Setting WhatsApp** → **Login/Pair**
4. Masukkan kode pairing di WhatsApp
5. Pilih **Scrape & Auto DM**

### API Key (Gratis)
1. Buka https://serpapi.com/manage-api-key
2. Daftar akun baru
3. Copy API key
4. Masukkan saat setup

**Tips**: Daftar banyak akun = banyak key gratis!

## Menu

| Menu | Fungsi |
|------|--------|
| **Scrape & Auto DM** | Scrape + DM otomatis 24/7 |
| **Setting WhatsApp** | Login, logout, ganti nomor |
| **Setting API** | Kelola SerpApi key (multi-key) |
| **Exit** | Keluar |

## Anti-Ban System

- Rate limit: 70 DM/jam
- Warm-up: 5 DM pertama delay 35-50 detik
- Normal: 30 detik per DM
- Batch: 3 target per batch
- Auto-stop jika session logged out
- Auto-restart setelah restriction lewat

## File Structure

```
~/
├── scrape.py          # Main script (Python)
├── astral_wa.js       # WhatsApp bot (Node.js)
├── install.sh         # Installer
├── keygen.py          # License key generator (seller only)
├── package.json       # Node.js dependencies
├── astral_data/       # Data & config
│   ├── wa_status.json
│   ├── wa_sent.json
│   ├── wa_acc.json
│   ├── wa_queue.json
│   ├── api_config.json
│   ├── license.json
│   └── *.wav          # Sound files
└── DejaVuSans.ttf     # Font untuk PDF
```

## Troubleshooting

### WhatsApp Logout
- Tunggu 1-2 jam
- Pilih Setting WhatsApp → Login/Pair

### API Limit
- Tambah key baru di Setting API
- Sistem auto-fallback ke key berikutnya

### Script Error
- Jalankan `bash install.sh` lagi
- Cek koneksi internet

## License

- **Trial**: 3 hari (fitur lengkap)
- **Full**: Permanent (beli dari penjual)

## Support

Hubungi penjual untuk:
- License key
- Error troubleshooting
- Update script

---

**Made with ❤️ by ASTRAL**
