```
    _             _____ _____  _____ _____    _____             __
   / \   _ __ ___|  ___|_   _|/ ____/ ____|  / ____|_____________| |__
  / _ \ | '__/ __| |_    | | | (___| (___  | (___ / ___ ___  | |  __|
 / ___ \| | | (__ |  _|   | |  \___ \\___ \  \___ \ / __/ _ \ | | |_
/_/   \_\_|  \___|_|     |_|  ____) |___) | ____) | (_|  __/ | | |__
                            |_____/_____/  |_____/ \___\___|_|_|\__|
```

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/platform-Termux%20%7C%20Linux-green?style=for-the-badge)
![Node](https://img.shields.io/badge/node-%3E%3D18-brightgreen?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.10+-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-red?style=for-the-badge)

**Global UMKM Scraper + Auto WhatsApp DM + AI Auto-Reply**

Scrape businesses worldwide → Send personalized DMs in their language → Auto-reply to responses → Stop when clients accept.

[Getting Started](#-quick-start) • [Features](#-features) • [How It Works](#-how-it-works) • [Configuration](#-configuration) • [FAQ](#-faq)

</div>

---

## Features

| Feature | Description |
|---|---|
| **200+ Global Locations** | Scrape businesses across 80+ countries in 12+ languages |
| **Auto WhatsApp DM** | Send personalized DMs matching the business's local language |
| **AI Auto-Reply** | Multilingual conversation flow (id/en/es/pt/fr/de/ar/hi/th/tr) |
| **Rate Limiting** | 70 DM/hour cap, auto-pause 10 min to prevent ban |
| **Smart Filtering** | Skip big brands, platforms (Instagram/Shopee), and businesses with websites |
| **Acc Tracking** | Auto-stop DM when 3 clients accept, auto-reply stays active |
| **Sent Tracking** | Never DM the same business twice (permanent tracking) |
| **Pairing Code Login** | No QR scan needed — just enter pairing code on your phone |
| **24/7 Daemon** | Runs continuously in background, scrapes & sends automatically |

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                    ASTRAL Pipeline                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. SCRAPE        →  Google/DuckDuckGo → Business Data  │
│  2. FILTER        →  Skip brands, platforms, big corps  │
│  3. DETECT LANG   →  ID/EN/ES/PT/FR/DE/AR/HI/TH/TR    │
│  4. QUEUE DM      →  Store in wa_queue.json              │
│  5. SEND DM       →  Baileys daemon picks up & sends    │
│  6. AUTO-REPLY    →  Listen for responses, reply in     │
│                      same language with conversation     │
│  7. TRACK ACC     →  Stop DM at 3 accepts               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- **Termux** (Android) or **Linux** terminal
- **Node.js** >= 18
- **Python** >= 3.10
- **WhatsApp** account (secondary number recommended)

### 1. Install Dependencies

```bash
# Clone the repo
git clone https://github.com/AstralXCode/astral.git
cd astral

# Install Node.js packages
npm install @whiskeysockets/baileys pino @hapi/boom csvtojson

# Install Python packages
pip install requests beautifulsoup4
```

### 2. Login WhatsApp (Pairing Code)

```bash
python3 scrape.py
```

Select **Setting WhatsApp** → **Login (Pairing Code)**

Enter your phone number when prompted (e.g. `628123456789`)

Check your WhatsApp app → Enter the 8-digit pairing code shown in terminal.

### 3. Run Auto DM

```bash
python3 scrape.py
```

Select **Scrape & Auto DM** → Type `y` to confirm

The system will:
1. Start Baileys WhatsApp daemon in background
2. Begin scraping global businesses
3. Send DMs automatically (70/hour max)
4. Auto-reply to any responses
5. Stop DM when 3 clients accept

### 4. Stop

Press `Ctrl+C` to stop gracefully.

---

## Configuration

### Rate Limits

| Setting | Value | File |
|---|---|---|
| Max DM/hour | 70 | `astral_wa.js` → `RATE_LIMIT` |
| Pause duration | 10 min | Auto when limit hit |
| Max accepted clients | 3 | `astral_wa.js` → `MAX_ACC` |
| Delay between DMs | 5-8 sec | Randomized |

### Customize DM Templates

Edit `scrape.py` → `DM_TEMPLATES` dictionary:

```python
DM_TEMPLATES = {
    "id": "Halo {name}, ...",
    "en": "Hello {name}, ...",
    "es": "Hola {name}, ...",
    # Add more languages...
}
```

### Customize Business Keywords

Edit `scrape.py` → `BIZ_KEYWORDS` dictionary to add business types per language.

### Customize Locations

Edit `scrape.py` → `GLOBAL_LOCATIONS` list:

```python
GLOBAL_LOCATIONS = [
    ("toko", "Indonesia"),
    ("restaurant", "USA"),
    ("cafe", "France"),
    # Add more...
]
```

---

## File Structure

```
astral/
├── scrape.py              # Main Python script (UI + scraper + DM queue)
├── astral_wa.js           # Node.js Baileys bot (WhatsApp + auto-reply)
├── package.json           # Node.js dependencies
├── astral_data/           # Runtime data (gitignored)
│   ├── wa_status.json     # Connection status
│   ├── wa_sent.json       # Sent tracking (permanent)
│   ├── wa_acc.json        # Accepted clients
│   ├── wa_chats.json      # Chat history
│   └── wa_queue.json      # Message queue
├── .astral_auth/          # Baileys auth session (gitignored)
└── README.md
```

---

## Menu UI

```
+==================================================+
|                                                    |
|          ASTRAL — Global UMKM Scraper             |
|          Auto WhatsApp DM + Auto Reply             |
|                                                    |
+==================================================+
|                                                    |
|  [0] Scrape & Auto DM                              |
|      → Scrape global UMKM + kirim DM otomatis     |
|                                                    |
|  [1] Setting WhatsApp                              |
|      → Login, Logout, Switch Number, Status        |
|                                                    |
+==================================================+
```

---

## Supported Languages

| Code | Language | DM Template | Auto-Reply | Keywords |
|---|---|---|---|---|
| `id` | Indonesian | ✅ | ✅ | ✅ |
| `en` | English | ✅ | ✅ | ✅ |
| `es` | Spanish | ✅ | ✅ | ✅ |
| `pt` | Portuguese | ✅ | ✅ | ✅ |
| `fr` | French | ✅ | ✅ | ✅ |
| `de` | German | ✅ | ✅ | ✅ |
| `ar` | Arabic | ✅ | ✅ | ✅ |
| `hi` | Hindi | ✅ | ✅ | ✅ |
| `th` | Thai | ✅ | ✅ | ✅ |
| `tr` | Turkish | ✅ | ✅ | ✅ |
| `ja` | Japanese | ✅ | ✅ | — |
| `ko` | Korean | ✅ | — | — |
| `zh` | Chinese | ✅ | — | — |

---

## FAQ

**Q: Will my WhatsApp get banned?**
A: ASTRAL uses rate limiting (70 DM/hour) and randomized delays to minimize risk. Use a secondary number if possible.

**Q: Can I scrape only specific countries?**
A: Yes. Edit `GLOBAL_LOCATIONS` in `scrape.py` to add/remove countries and business types.

**Q: How do I reset the sent tracking?**
A: Delete `astral_data/wa_sent.json` to DM previously contacted businesses again.

**Q: How do I reset the accepted clients count?**
A: Press `r` when the system shows "Max acc reached", or delete `astral_data/wa_acc.json`.

**Q: Can I run this on a VPS instead of Termux?**
A: Yes. ASTRAL works on any Linux system with Node.js 18+ and Python 3.10+.

---

## Tech Stack

- **[Baileys](https://github.com/WhiskeySockets/Baileys)** — WhatsApp Web API (no browser needed)
- **Python** — Scraping, filtering, UI
- **DuckDuckGo / Google** — Search engines for business data
- **BeautifulSoup** — HTML parsing

---

## License

MIT License — use freely, just don't spam people too hard.

---

<div align="center">

**Built with 💜 by [AstralXCode](https://github.com/AstralXCode)**

</div>
