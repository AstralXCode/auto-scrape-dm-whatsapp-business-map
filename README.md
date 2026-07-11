<div align="center">

```
              ___               _    ___ ____   ___   _  __
             / _ \ _ __   ___ | |  / _ \___ \ / _ \ | |/ /
            | | | | '_ \ / _ \| | | | | |__) | | | || ' / 
            | |_| | |_) | (_) | | | |_|  __/| |_| || . \ 
             \___/| .__/ \___/|_|  \___/____/ \___/ |_|\_\
                  |_|
```

![Version](https://img.shields.io/badge/VERSION-2.0.0-blue?style=flat-square)
![Platform](https://img.shields.io/badge/PLATFORM-Termux%20%7C%20Linux-green?style=flat-square)
![Node.js](https://img.shields.io/badge/NODE-%3E%3D18-brightgreen?style=flat-square)
![Python](https://img.shields.io/badge/PYTHON-3.10+-yellow?style=flat-square)
![License](https://img.shields.io/badge/LICENSE-MIT-red?style=flat-square)

---

### **GLOBAL BUSINESS SCRAPING + AUTO WHATSAPP DM + AI AUTO-REPLY**

Scrape businesses worldwide → Send DM in their language → Auto-reply → Stop at 3 clients

[Quick Start](#-quick-start) · [Features](#-features) · [How It Works](#-how-it-works) · [Configuration](#-configuration) · [FAQ](#-faq)

</div>

---

## Features

| | Feature | Description |
|---|---|---|
| 🌍 | **200+ Global Locations** | Scrape businesses across 80+ countries, 12+ languages |
| 💬 | **Auto WhatsApp DM** | Personalized DMs matching the business's local language |
| 🤖 | **AI Auto-Reply** | Multilingual conversation flow (ID/EN/ES/PT/FR/DE/AR/HI) |
| ⏱️ | **Rate Limiting** | 70 DM/hour cap, auto-pause 10 min to prevent ban |
| 🔍 | **Smart Filtering** | Skip brands, platforms, and businesses with websites |
| 🎯 | **Acc Tracking** | Auto-stop DM when 3 clients accept, auto-reply stays on |
| 📋 | **Sent Tracking** | Never DM the same business twice (permanent) |
| 🔑 | **Pairing Code Login** | No QR scan — just enter code on your phone |
| 🔄 | **24/7 Daemon** | Runs in background, scrapes & sends automatically |

---

## How It Works

```
+================================================================+
|                    ASTRAL — WORKFLOW PIPELINE                   |
+================================================================+
|                                                                |
|   [1] SCRAPE                                                   |
|       └─→  Google / DuckDuckGo  ──→  Business Data             |
|                                                                |
|   [2] FILTER                                                   |
|       └─→  Skip brands, platforms, big corps                   |
|                                                                |
|   [3] DETECT LANGUAGE                                          |
|       └─→  ID / EN / ES / PT / FR / DE / AR / HI / TH / TR     |
|                                                                |
|   [4] QUEUE DM                                                 |
|       └─→  Store in wa_queue.json (with language tag)           |
|                                                                |
|   [5] SEND DM                                                  |
|       └─→  Baileys daemon picks up queue & sends               |
|                                                                |
|   [6] AUTO-REPLY                                               |
|       └─→  Listen for responses, reply in same language        |
|                                                                |
|   [7] TRACK ACC                                                |
|       └─→  Stop DM at 3 accepts, auto-reply stays active       |
|                                                                |
+================================================================+
```

---

## Quick Start

### Prerequisites

- **Termux** (Android) or **Linux** terminal
- **Node.js** >= 18
- **Python** >= 3.10
- **WhatsApp** account (secondary number recommended)

### Step 1 — Install

```bash
git clone https://github.com/AstralXCode/auto-scrape-dm-whatsapp-business-map.git
cd auto-scrape-dm-whatsapp-business-map
npm install @whiskeysockets/baileys pino @hapi/boom csvtojson
pip install requests beautifulsoup4
```

### Step 2 — Login WhatsApp

```bash
python3 scrape.py
```

> Select **Setting WhatsApp** → **Login (Pairing Code)**
> Enter your phone number → Check WhatsApp → Enter the 8-digit code

### Step 3 — Run

```bash
python3 scrape.py
```

> Select **Scrape & Auto DM** → Type `y`

### What Happens

```
  Baileys daemon starts     (background)
  ↓
  Global scraper runs       (200+ locations)
  ↓
  Businesses filtered       (skip brands/platforms)
  ↓
  DM sent in local language  (rate limited 70/hr)
  ↓
  Auto-reply listens         (multilingual)
  ↓
  Stops at 3 accepts         (auto-reply stays on)
```

### Step 4 — Stop

Press `Ctrl+C` to stop gracefully.

---

## Configuration

### Rate Limits

| Setting | Default | File |
|---|---|---|
| Max DM/hour | 70 | `astral_wa.js` → `RATE_LIMIT` |
| Pause duration | 10 min | Auto when limit hit |
| Max accepted clients | 3 | `astral_wa.js` → `MAX_ACC` |
| Delay between DMs | 5-8 sec | Randomized |

### DM Templates

Edit `scrape.py` → `DM_TEMPLATES`:

```python
DM_TEMPLATES = {
    "id": "Halo {name}, ...",
    "en": "Hello {name}, ...",
    "es": "Hola {name}, ...",
    # Add more languages...
}
```

### Business Keywords

Edit `scrape.py` → `BIZ_KEYWORDS` to add business types per language.

### Locations

Edit `scrape.py` → `GLOBAL_LOCATIONS`:

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
auto-scrape-dm-whatsapp-business-map/
│
├── scrape.py                # Main Python script
│                             #   ├── UI (2-menu navigation)
│                             #   ├── Global scraper (200+ locations)
│                             #   ├── Language detection
│                             #   ├── DM queue writer
│                             #   └── Rate limit checker
│
├── astral_wa.js             # Node.js Baileys bot
│                             #   ├── WhatsApp pairing login
│                             #   ├── Send DM from queue
│                             #   ├── Auto-reply (7 languages)
│                             #   ├── Sent tracking
│                             #   └── Acc tracking
│
├── package.json             # Node.js dependencies
│
├── astral_data/             # Runtime data (gitignored)
│   ├── wa_status.json       #   Connection status
│   ├── wa_sent.json         #   Sent phone numbers
│   ├── wa_acc.json          #   Accepted clients
│   ├── wa_chats.json        #   Chat history
│   └── wa_queue.json        #   Message queue
│
├── .astral_auth/            # Baileys session (gitignored)
├── README.md
└── LICENSE
```

---

## Menu UI

```
+============================================================+
|                                                            |
|           █████╗ █████╗ ████████╗ ██████╗                  |
|          ██╔════╝██╔══██╗╚══██╔══╝██╔════╝                  |
|          ██║     ███████║   ██║   ██║                       |
|          ██║     ██╔══██║   ██║   ██║                       |
|          ╚██████╗██║  ██║   ██║   ╚██████╗                  |
|           ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝                |
|                                                            |
|          Global UMKM Scraper + Auto WhatsApp DM            |
|                                                            |
+============================================================+
|                                                            |
|  [0] Scrape & Auto DM                                      |
|      Scrape global UMKM + kirim DM otomatis                |
|                                                            |
|  [1] Setting WhatsApp                                      |
|      Login / Logout / Switch Number / Status               |
|                                                            |
+============================================================+
```

---

## Supported Languages

| Code | Language | DM | Auto-Reply | Keywords |
|:---:|---|:---:|:---:|:---:|
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
ASTRAL uses rate limiting (70 DM/hour) and randomized delays to minimize risk. Use a secondary number if possible.

**Q: Can I scrape only specific countries?**
Edit `GLOBAL_LOCATIONS` in `scrape.py` to add/remove countries and business types.

**Q: How do I reset the sent tracking?**
Delete `astral_data/wa_sent.json` to DM previously contacted businesses again.

**Q: How do I reset the accepted clients count?**
Press `r` when "Max acc reached" appears, or delete `astral_data/wa_acc.json`.

**Q: Can I run this on a VPS?**
Yes. Works on any Linux system with Node.js 18+ and Python 3.10+.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| [Baileys](https://github.com/WhiskeySockets/Baileys) | WhatsApp Web API (no browser) |
| Python 3.10+ | Scraping, filtering, UI |
| Node.js 18+ | WhatsApp daemon, auto-reply |
| BeautifulSoup | HTML parsing |
| Google / DuckDuckGo | Business search engines |

---

## License

MIT — use freely.

---

<div align="center">

**Built with 💜 by [AstralXCode](https://github.com/AstralXCode)**

</div>
