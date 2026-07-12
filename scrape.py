#!/usr/bin/env python3
import sys, os, time, itertools, random, json, re, csv, subprocess, termios, tty, math, requests

RAINBOW = [
    "\033[38;5;196m","\033[38;5;202m","\033[38;5;208m","\033[38;5;214m",
    "\033[38;5;220m","\033[38;5;226m","\033[38;5;190m","\033[38;5;154m",
    "\033[38;5;118m","\033[38;5;82m", "\033[38;5;46m", "\033[38;5;47m",
    "\033[38;5;48m", "\033[38;5;49m", "\033[38;5;50m", "\033[38;5;51m",
    "\033[38;5;45m", "\033[38;5;39m", "\033[38;5;33m", "\033[38;5;27m",
    "\033[38;5;21m", "\033[38;5;57m", "\033[38;5;93m", "\033[38;5;129m",
    "\033[38;5;165m","\033[38;5;201m","\033[38;5;199m","\033[38;5;197m",
]
FLASH = [
    "\033[1;31m","\033[1;33m","\033[1;32m","\033[1;36m",
    "\033[1;34m","\033[1;35m","\033[1;91m","\033[1;93m",
    "\033[1;92m","\033[1;95m",
]
R="\033[0m"; B="\033[1m"; D="\033[2m"; G="\033[1;32m"; Y="\033[1;33m"
C="\033[1;36m"; M="\033[1;35m"; RED="\033[1;31m"

BANNER = [
    r"           _____ _______ _____            _        ",
    r"    /\    / ____|__   __|  __ \     /\   | |       ",
    r"   /  \  | (___    | |  | |__) |   /  \  | |       ",
    r"  / /\ \  \___ \   | |  |  _  /   / /\ \ | |       ",
    r" / ____ \ ____) |  | |  | | \ \  / ____ \| |____   ",
    r"/_/    \_\_____/   |_|  |_|  \_\/_/    \_\______|  ",
]
SUBTITLE = "        ~ Scraper + Auto WA DM v2.0 ~"

HOME = os.path.expanduser("~")
DATA_DIR = os.path.join(HOME, "astral_data")
WA_SCRIPT = os.path.join(HOME, "astral_wa.js")
STATUS_FILE = os.path.join(DATA_DIR, "wa_status.json")
QUEUE_FILE = os.path.join(DATA_DIR, "wa_queue.json")
API_CONFIG_FILE = os.path.join(DATA_DIR, "api_config.json")
WIDTH = 47

def _load_api_keys():
    """Load API keys from config file"""
    if os.path.exists(API_CONFIG_FILE):
        try:
            with open(API_CONFIG_FILE) as f:
                data = json.load(f)
                keys = data.get("serpapi_keys", [])
                if keys: return keys
        except: pass
    return []

def _save_api_keys(keys):
    """Save API keys to config file"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(API_CONFIG_FILE, "w") as f:
        json.dump({"serpapi_keys": keys}, f, indent=2)

SERP_API_KEYS = _load_api_keys()
SERP_API_KEY = SERP_API_KEYS[0] if SERP_API_KEYS else None
STORAGE_DIR = "/sdcard/ASTRAL_DATA"
LICENSE_FILE = os.path.join(DATA_DIR, "license.json")
TRIAL_DAYS = 3

MENU = [
    ("Scrape & Auto DM",         "Scrape semua kota + auto DM 24/7 otomatis"),
    ("Setting WhatsApp",         "Login/logout, ganti nomor, pairing"),
    ("Setting API",              "Kelola API key SerpApi (multi-key fallback)"),
    ("Exit",                     "Keluar dari program"),
]

# ── LICENSE SYSTEM ──
def _get_device_id():
    """Get unique device ID from Termux prefix"""
    try:
        import hashlib
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        return hashlib.md5(prefix.encode()).hexdigest()[:12]
    except:
        return "default"

def _verify_license(key, device_id):
    """Verify license key"""
    import hashlib
    secret = "ASTRAL_X7K9M2"
    for days in [365, 180, 90, 60, 30, 14, 7, 3, 1]:
        raw = f"{device_id}:{secret}:{days}"
        expected = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()
        expected_fmt = f"ASTRAL-{expected[:4]}-{expected[4:8]}-{expected[8:12]}-{expected[12:]}"
        if key.upper() == expected_fmt:
            return True
    return False

def _load_license():
    """Load license info"""
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE) as f:
                return json.load(f)
        except: pass
    return {}

def _save_license(data):
    """Save license info"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _check_license():
    """Check if license is valid. Returns (is_valid, is_trial, days_left)"""
    device_id = _get_device_id()
    lic = _load_license()

    # Check full license
    if lic.get("type") == "full" and lic.get("key"):
        if _verify_license(lic["key"], device_id):
            return True, False, -1  # Valid, not trial, unlimited

    # Check trial
    if lic.get("type") == "trial":
        start = lic.get("start_ts", 0)
        elapsed = time.time() - start
        remaining = (TRIAL_DAYS * 86400) - elapsed
        if remaining > 0:
            days_left = remaining / 86400
            return True, True, days_left
        else:
            return False, True, 0  # Trial expired

    # No license at all - return False so setup can ask
    return False, False, 0

def _first_time_setup():
    """Setup wizard untuk pertama kali"""
    lic_valid, lic_trial, lic_days = _check_license()

    # Cek apakah sudah ada API key
    keys = _load_api_keys()

    # Jika license full (bukan trial), langsung ke API key
    if lic_valid and not lic_trial:
        if keys:
            return True  # Sudah lengkap
        # Lanjut ke API key setup di bawah
    elif lic_trial and lic_days > 0:
        # Trial aktif, tapi tetap tawarkan upgrade ke full
        pass
    else:
        # Belum ada license sama sekali
        pass

    # Tampilkan license screen SELALU kecuali sudah full + ada API key
    if not (lic_valid and not lic_trial and keys):
        clear()
        print()
        for l in BANNER: print(f"  {rainbow_line(l)}")
        print()
        device_id = _get_device_id()

        if lic_valid and lic_trial and lic_days > 0:
            # Sudah trial, tawarkan upgrade
            print(f"  {Y}┌─────────────────────────────────────────┐{R}")
            print(f"  {Y}│  TRIAL AKTIF - {lic_days:.1f} hari tersisa          │{R}")
            print(f"  {Y}└─────────────────────────────────────────┘{R}")
            print()
            print(f"  {D}Device ID kamu:{R} {G}{device_id}{R}")
            print()
            print(f"  {C}[1]{R} Upgrade ke full license")
            print(f"  {C}[2]{R} Lanjut dengan trial")
            print()
            ch = input(f"  {G}▸ Pilih: {R}").strip()

            if ch == "1":
                while True:
                    key = input(f"  {G}▸ Masukkan license key: {R}").strip().upper()
                    if not key:
                        print(f"  {RED}[!] Kosong.{R}")
                        continue
                    if _verify_license(key, device_id):
                        _activate_license(key)
                        print(f"  {G}[✓] License activated!{R}")
                        time.sleep(1)
                        break
                    else:
                        print(f"  {RED}[!] License key tidak valid.{R}")
                        print(f"  {D}Kirim Device ID ke penjual untuk generate key{R}")
        else:
            # Belum ada license
            print(f"  {Y}┌─────────────────────────────────────────┐{R}")
            print(f"  {Y}│  AKTIVASI LICENSE                       │{R}")
            print(f"  {Y}└─────────────────────────────────────────┘{R}")
            print()
            print(f"  {D}Device ID kamu:{R} {G}{device_id}{R}")
            print()
            print(f"  {C}[1]{R} Masukkan license key dari penjual")
            print(f"  {C}[2]{R} Mulai trial GRATIS 3 hari")
            print()
            ch = input(f"  {G}▸ Pilih: {R}").strip()

            if ch == "1":
                while True:
                    key = input(f"  {G}▸ Masukkan license key: {R}").strip().upper()
                    if not key:
                        print(f"  {RED}[!] Kosong.{R}")
                        continue
                    if _verify_license(key, device_id):
                        _activate_license(key)
                        print(f"  {G}[✓] License activated!{R}")
                        time.sleep(1)
                        break
                    else:
                        print(f"  {RED}[!] License key tidak valid.{R}")
                        print(f"  {D}Kirim Device ID ke penjual untuk generate key{R}")
            else:
                _save_license({
                    "type": "trial",
                    "start_ts": time.time(),
                    "device_id": device_id,
                })
                print(f"  {G}[✓] Trial 3 hari dimulai!{R}")
                time.sleep(1)

    # Cek API key
    if not keys:
        clear()
        print()
        for l in BANNER: print(f"  {rainbow_line(l)}")
        print()
        print(f"  {Y}┌─────────────────────────────────────────┐{R}")
        print(f"  {Y}│  SETUP API KEY                          │{R}")
        print(f"  {Y}│  Masukkan API key SerpApi Anda          │{R}")
        print(f"  {Y}└─────────────────────────────────────────┘{R}")
        print()
        print(f"  {C}Dapatkan API key GRATIS di:{R}")
        print(f"  {D}https://serpapi.com/manage-api-key{R}")
        print(f"  {D}Free tier: 100 pencarian/bulan{R}")
        print()
        print(f"  {D}Tip: Daftar banyak akun = banyak key gratis!{R}")
        print()

        while True:
            api_key = input(f"  {G}▸ Masukkan SerpApi key: {R}").strip()
            if not api_key:
                print(f"  {RED}[!] Kosong.{R}")
                continue

            # Verify key works
            print(f"  {C}[*] Verifikasi key...{R}")
            try:
                import requests
                resp = requests.get("https://serpapi.com/account",
                                  params={"api_key": api_key}, timeout=10)
                data = resp.json()
                if "plan_name" in data or "account_id" in data:
                    plan = data.get('plan_name', data.get('plan', 'free'))
                    print(f"  {G}[✓] Key valid! Plan: {plan}{R}")
                    _save_api_keys([api_key])
                    time.sleep(1)
                    return True
                else:
                    print(f"  {RED}[!] Key tidak valid. Coba lagi.{R}")
            except Exception as e:
                print(f"  {RED}[!] Error verifikasi: {e}{R}")
                print(f"  {D}Simpan key anyway? (y/n){R}")
                if input(f"  {G}▸ {R}").strip().lower() == "y":
                    _save_api_keys([api_key])
                    return True

    return True

def _activate_license(key):
    """Activate full license"""
    device_id = _get_device_id()
    if _verify_license(key, device_id):
        _save_license({
            "type": "full",
            "key": key,
            "device_id": device_id,
            "activated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        return True
    return False

def _show_license_screen():
    """Show license/activation screen"""
    is_valid, is_trial, days_left = _check_license()

    if is_valid and not is_trial:
        return True  # Full license, skip screen

    clear()
    print()
    for l in BANNER: print(f"  {rainbow_line(l)}")
    print()

    if is_trial and days_left > 0:
        print(f"  {Y}┌─────────────────────────────────────────┐{R}")
        print(f"  {Y}│  TRIAL MODE - {days_left:.1f} hari tersisa          │{R}")
        print(f"  {Y}│  Fitur lengkap, semua bisa dipakai      │{R}")
        print(f"  {Y}│  Setelah habis, beli full version       │{R}")
        print(f"  {Y}└─────────────────────────────────────────┘{R}")
        print()
        print(f"  {D}Tekan Enter untuk lanjut (trial)...{R}")
        input()
        return True

    # Trial expired
    print(f"  {RED}┌─────────────────────────────────────────┐{R}")
    print(f"  {RED}│  TRIAL HABIS!                           │{R}")
    print(f"  {RED}│  Silakan beli full version              │{R}")
    print(f"  {RED}│  Hub: @AstralXCode (WhatsApp/Telegram)  │{R}")
    print(f"  {RED}└─────────────────────────────────────────┘{R}")
    print()

    device_id = _get_device_id()
    print(f"  {C}Device ID: {device_id}{R}")
    print(f"  {D}Kirim Device ID ini ke penjual untuk beli license{R}")
    print()

    print(f"  [1] Masukkan license key")
    print(f"  [0] Keluar")
    print()
    ch = input(f"  {G}▸ Pilih: {R}").strip()

    if ch == "1":
        print()
        key = input(f"  {G}▸ Masukkan license key: {R}").strip()
        if _activate_license(key):
            print(f"\n  {G}[✓] License activated! Selamat menggunakan ASTRAL.{R}")
            time.sleep(2)
            return True
        else:
            print(f"\n  {RED}[!] License key tidak valid.{R}")
            time.sleep(2)
            return False
    return False

def _export_pdf(businesses, filename="businesses.pdf"):
    """Export businesses to PDF with Unicode support"""
    try:
        from fpdf import FPDF
    except ImportError:
        print(f"  {RED}[!] fpdf2 belum terinstall. Jalankan: pip install fpdf2{R}")
        return None

    os.makedirs(STORAGE_DIR, exist_ok=True)
    pdf_path = os.path.join(STORAGE_DIR, filename)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add Unicode font
    font_path = None
    for p in ["/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              os.path.join(HOME, "DejaVuSans.ttf")]:
        if os.path.exists(p):
            font_path = p
            break

    if font_path and os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        bold_path = font_path.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf")
        if os.path.exists(bold_path):
            pdf.add_font("DejaVu", "B", bold_path, uni=True)
        else:
            pdf.add_font("DejaVu", "B", font_path, uni=True)
        font_name = "DejaVu"
    else:
        font_name = "Helvetica"

    # Title page
    pdf.add_page()
    pdf.set_font(font_name, "B", 24)
    pdf.cell(0, 15, "ASTRAL Business Directory", ln=True, align="C")
    pdf.set_font(font_name, "", 12)
    pdf.cell(0, 10, f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.cell(0, 10, f"Total: {len(businesses)} businesses", ln=True, align="C")
    pdf.ln(10)

    # Business entries
    for i, b in enumerate(businesses):
        if pdf.get_y() > 250:
            pdf.add_page()

        pdf.set_font(font_name, "B", 11)
        name = str(b.get("name", "N/A"))[:80]
        pdf.cell(0, 7, f"{i+1}. {name}", ln=True)

        pdf.set_font(font_name, "", 9)
        phone = str(b.get("phone", "-"))
        address = str(b.get("address", "-"))[:100]
        category = str(b.get("category", "-"))
        rating = str(b.get("rating", "-"))
        reviews = str(b.get("reviews", "-"))
        website = str(b.get("website", "-"))

        pdf.cell(0, 5, f"   Phone: {phone}  |  Rating: {rating} ({reviews})", ln=True)
        pdf.cell(0, 5, f"   Address: {address}", ln=True)
        pdf.cell(0, 5, f"   Category: {category}  |  Website: {website}", ln=True)
        pdf.ln(3)

    pdf.output(pdf_path)
    return pdf_path

def clear(): os.system("cls" if os.name=="nt" else "clear")

def rainbow_line(text):
    out, idx = "", 0
    for ch in text:
        if ch == " ": out += ch
        else: out += f"{RAINBOW[idx%len(RAINBOW)]}{ch}{R}"; idx += 1
    return out

def rainbow_banner():
    print()
    for l in BANNER: print(f"  {rainbow_line(l)}")
    print()
    out = "  "
    for i, ch in enumerate(SUBTITLE):
        out += ch if ch==" " else f"{RAINBOW[(i+10)%len(RAINBOW)]}{ch}{R}"
    print(out)

def _banner_typewriter():
    """Animasi typewriter untuk ASCII art + subtitle"""
    # Type plain ASCII art line by line
    for line in BANNER:
        for ci in range(len(line)):
            sys.stdout.write(f"\r  {line[:ci+1]}")
            sys.stdout.flush()
            _bell()
            time.sleep(0.005)
        sys.stdout.write("\n")
        sys.stdout.flush()

    # Type subtitle with color
    sys.stdout.write("  ")
    for i, ch in enumerate(SUBTITLE):
        if ch == " ":
            sys.stdout.write(ch)
        else:
            color = RAINBOW[(i+10) % len(RAINBOW)]
            sys.stdout.write(f"{color}{ch}{R}")
        sys.stdout.flush()
        _bell()
        time.sleep(0.03)
    sys.stdout.write("\n\n")
    sys.stdout.flush()
    time.sleep(0.8)

def _play_sound(name):
    """Play sound effect (non-blocking)"""
    sound_path = os.path.join(DATA_DIR, f"{name}.wav")
    if os.path.exists(sound_path):
        try:
            subprocess.Popen(
                ["termux-media-player", "play", sound_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except: pass

def _bell():
    """Instant tick sound via paplay"""
    tick_path = os.path.join(DATA_DIR, "tick.wav")
    if os.path.exists(tick_path):
        try:
            subprocess.Popen(
                ["paplay", tick_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except: pass

def loading():
    _play_sound("beep")
    spinner = random.choice([["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"],["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"],["◐","◓","◑","◒"],["◰","◳","◲","◱"]])
    phases = ["Memuat modul","Init ASTRAL","Connect server","Load resources","Prepare engine","Finalisasi"]
    bar_len, phase_time = 30, 100/len(phases)
    last_phase = -1
    for i, frame in enumerate(itertools.cycle(spinner)):
        pct = min(i*2, 100)
        cur_phase = min(int(pct/phase_time), len(phases)-1)
        phase = phases[cur_phase]
        if cur_phase != last_phase:
            _play_sound("tick")
            last_phase = cur_phase
        filled = int(bar_len*pct/100)
        color = RAINBOW[i%len(RAINBOW)]
        bar = f"{color}{'█'*filled}{D}{'░'*(bar_len-filled)}{R}"
        sys.stdout.write(f"\r  {B}{color}{frame}{R} {phase}... {bar} {B}{color}{pct}%{R}")
        sys.stdout.flush()
        if pct >= 100: break
        time.sleep(0.04)
    sys.stdout.write("\r"+" "*80+"\r"); sys.stdout.flush()
    _play_sound("success")
    for j, txt in enumerate(["Modul loaded","ASTRAL init","Server OK","Resources ready","Engine ready","All systems go"]):
        print(f"  {RAINBOW[j*4%len(RAINBOW)]}[✓] {txt}{R}"); time.sleep(0.12)
    time.sleep(0.3)

def get_key():
    fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd); ch = sys.stdin.read(1)
        if ch=="\x1b":
            sys.stdin.read(1); code = sys.stdin.read(1)
            return "UP" if code=="A" else "DOWN" if code=="B" else ""
        return "ENTER" if ch in ("\r","\n") else "QUIT" if ch in ("q","Q") else ""
    finally: termios.tcsetattr(fd, termios.TCSADRAIN, old)

def box_line(text, color=""):
    pad = WIDTH - len(text) - 4
    return f"  {color}|  {text}{' '*max(pad,0)}|{R}"

def print_menu(sel, typewriter_idx=-1):
    print()
    print(f"  {B}{M}+{'='*WIDTH}+{R}")
    for i, (name, desc) in enumerate(MENU):
        is_sel = (i == sel)
        c = f"{B}{G}" if is_sel else D
        tag = "[●]" if is_sel else "[○]"

        if is_sel and typewriter_idx >= 0:
            # Typewriter effect untuk item terpilih
            display_name = name[:typewriter_idx+1]
            pad_name = WIDTH - len(f"{tag} {name}") - 4
            name_line = f"  {c}|  {tag} {display_name}{' '*max(pad_name - len(display_name), 0)}|{R}"
            print(name_line)
            pad_desc = WIDTH - len(f"    {desc}") - 4
            desc_line = f"  {c}|    {desc}{' '*max(pad_desc, 0)}|{R}"
            print(desc_line)
        else:
            print(box_line(f"{tag} {name}", c))
            print(box_line(f"    {desc}", c))

        if i < len(MENU)-1: print(box_line(""))
    print(box_line(""))
    print(box_line("↑/↓ pilih  Enter OK  q keluar", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}")

def menu_select():
    sel = 0
    old_sel = -1
    clear(); rainbow_banner(); print_menu(sel)
    while True:
        key = get_key()
        if key=="UP":
            _bell()
            sel = (sel-1)%len(MENU)
            clear(); rainbow_banner(); print_menu(sel)
            old_sel = sel
        elif key=="DOWN":
            _bell()
            sel = (sel+1)%len(MENU)
            clear(); rainbow_banner(); print_menu(sel)
            old_sel = sel
        elif key=="ENTER":
            _bell()
            return sel
        elif key=="QUIT": return -1

# ──────────────────────────────────────────────────────────────
#  GLOBAL UMKM SCRAPER + MULTILINGUAL DM
#  Target: Bisnis kecil di SELURUH DUNIA yang belum punya website
# ──────────────────────────────────────────────────────────────

# Platform domains (skip - bukan website bisnis sendiri)
PLATFORM_DOMAINS = [
    "instagram.com","facebook.com","twitter.com","tiktok.com","youtube.com",
    "wikipedia.org","shopee.","tokopedia.","bukalapak.","blibli.",
    "google.com","maps.google","tripadvisor.","zomato.","grab.","gojek.",
    "traveloka.","yelp.","foursquare.","pinterest.","reddit.","quora.",
    "medium.com","academia.edu","scribd.","slideshare","linkedin.",
    "indeed.","glassdoor.","uber.","lyft.","doordash.","grubhub.",
]

# Big brand names (skip - sudah besar, gak butuh jasa kita)
BIG_BRANDS = [
    "mcdonald","starbucks","kfc","pizza hut","subway","burger king","wendys",
    "taco bell","dunkin","baskin robbins","dominos","papa john",
    "nike","adidas","puma","reebok","new balance","converse","vans",
    "zara","h&m","uniqlo","gap","forever 21","shein","temu",
    "apple","samsung","sony","lg","panasonic","philips","bose",
    "toyota","honda","ford","bmw","mercedes","tesla","hyundai",
    "ikea","home depot","lowes","walmart","costco","target","amazon",
    "coca cola","pepsi","nestle","unilever","procter gamble",
    "visa","mastercard","paypal","stripe","square",
    "airbnb","booking.com","expedia","kayak","skyscanner",
    "netflix","spotify","disney","hbo","hulu","prime video",
    "uber","lyft","dididi","grab","gojek","careem",
    "fedex","ups","dhl","usps","amazon logistics",
]

# Business keywords per language (UMKM yang butuh website)
BIZ_KEYWORDS = {
    # Indonesian
    "id": ["toko","warung","kedai","cafe","kopi","restoran","rumah makan",
           "laundry","bengkel","apotek","salon","barbershop","fotografi",
           "kursus","les","sewa","rental","jasa","service","catering",
           "konveksi","jahit","butik","fashion","distro","sepatu","tas",
           "furniture","elektronik","optik","pet shop","florist","dekorasi",
           "cuci","setrika","oven","kue","roti","bakso","sate","mie"],
    # English
    "en": ["shop","store","cafe","coffee","restaurant","bar","pub",
           "laundry","repair","salon","barbershop","photography","studio",
           "gym","fitness","yoga","tutor","lessons","rental","hire",
           "plumber","electrician","cleaning","landscaping","painting",
           "bakery","pizza","taco","sushi","burger","steak","seafood",
           "florist","flower","gift","boutique","fashion","clothing",
           "shoe","bag","jewelry","watch","optic","pet","grooming",
           "catering","food truck","market","grocery","deli"],
    # Spanish
    "es": ["tienda","restaurante","cafe","cafeteria","panaderia","taller",
           "salon","peluqueria","fotografia","gimnasio","academia",
           "alquiler","renta","plomero","electricista","limpieza",
           "pizzeria","taqueria","sushi","hamburguesa","cerveceria",
           "floristeria","boutique","moda","zapateria","joyeria",
           "mascota","veterinaria","catering","mercado","abarrotes"],
    # Portuguese
    "pt": ["loja","restaurante","cafeteria","padaria","oficina","salao",
           "barbearia","fotografia","academia","escola","locacao",
           "encanador","eletricista","limpeza","jardinagem","pintura",
           "pizzaria","hamburgueria","sushi","cervejaria","confeitaria",
           "floricultura","boutique","moda","sapataria","joalheria",
           "pet shop","veterinario","catering","mercado","mercearia"],
    # French
    "fr": ["boutique","restaurant","cafe","boulangerie","atelier","salon",
           "coiffure","photographie","gym","ecole","location",
           "plombier","electricien","nettoyage","jardinage","peinture",
           "pizzeria","brasserie","sushi","boulangerie","patisserie",
           "fleuriste","mode","chaussures","bijoux","optique",
           "animalerie","traiteur","marche","epicerie"],
    # German
    "de": ["geschäft","restaurant","cafe","bäckerei","werkstatt","salon",
           "fotografie","fitness","schule","vermietung","verleih",
           "klempner","elektriker","reinigung","garten","malerei",
           "pizzeria","brauerei","sushi","konditorei","kuchen",
           "blumenladen","mode","schuhe","schmuck","optik",
           "tierhandlung","catering","markt","lebensmittel"],
    # Arabic
    "ar": ["محل","مطعم","كافيه","مخبز","ورشة","صالون",
           "تصوير","جيم","مدرسة","ايجار","تاجير",
           "سباك","كهرباء","تنظيف","حدائق","دهان",
           "بيتزا","مخبز","حلويات","ورد","أزياء",
           "أحذية","مجوهرات","نظارات","حيوانات","تموين"],
    # Hindi
    "hi": ["दुकान","रेस्तरां","कैफे","बेकरी","वर्कशॉप","सैलून",
           "फोटोग्राफी","जिम","स्कूल","किराया","प्लंबर",
           "बिजली","सफाई","बगीचा","पिज्जा","बेकरी",
           "फूल","फैशन","जूते","गहने","पालतू","केटरिंग"],
    # Thai
    "th": ["ร้าน","ร้านอาหาร","คาเฟ่","เบเกอรี่","อู่ซ่อม","ร้านเสริมสวย",
           "ถ่ายภาพ","ฟิตเนส","โรงเรียน","ให้เช่า","ช่างประปา",
           "ช่างไฟฟ้า","ทำความสะอาด","สวน","พิซซ่า","เบเกอรี่",
           "ร้านดอกไม้","แฟชั่น","รองเท้า","เครื่องประดับ","สัตว์เลี้ยง"],
    # Turkish
    "tr": ["dukkan","restoran","kafe","firin","atölye","kuaför",
           "fotoğraf","spor","okul","kiralık","tesisatçı",
           "elektrikçi","temizlik","peyzaj","pizza","pastane",
           "çiçek","moda","ayakkabı","takı","gözlük","pet","catering"],
}

# DM templates per language
DM_TEMPLATES = {
    "id": (
        "Halo Kak! 👋\n\n"
        "Saya lihat usaha {name} dari pencarian lokal. "
        "Saya developer yang bantu UMKM punya website profesional.\n\n"
        "Banyak UMKM yang belum punya website, padahal:\n"
        "- Pelanggan gampang nemuin via Google\n"
        "- Tampilkan produk/menu + harga langsung\n"
        "- Tambah kredibilitas & kepercayaan\n\n"
        "Mulai dari Rp 500rb (free maintenance 3 bulan). "
        "Mau saya buatkan contoh desain gratis? 🙏"
    ),
    "en": (
        "Hi there! 👋\n\n"
        "I found {name} while browsing local businesses. "
        "I'm a web developer who helps small businesses go online.\n\n"
        "Most small businesses don't have a website yet, which means:\n"
        "- Customers can't find you on Google\n"
        "- You can't showcase your products/menu\n"
        "- You miss out on online visibility\n\n"
        "I can build a professional website for you starting at $50. "
        "Want me to create a free mockup? 🙏"
    ),
    "es": (
        "¡Hola! 👋\n\n"
        "Encontré {name} en una búsqueda local. "
        "Soy desarrollador y ayudo a negocios pequeños a tener presencia online.\n\n"
        "Muchos negocios pequeños aún no tienen sitio web:\n"
        "- Los clientes no te encuentran en Google\n"
        "- No puedes mostrar tus productos/menú\n"
        "- Pierdes visibilidad en línea\n\n"
        "Puedo crear un sitio web profesional desde $50. "
        "¿Quieres que te haga un mockup gratis? 🙏"
    ),
    "pt": (
        "Olá! 👋\n\n"
        "Encontrei {name} em uma pesquisa local. "
        "Sou desenvolvedor e ajudo pequenos negócios a terem presença online.\n\n"
        "Muitos negócios ainda não têm site:\n"
        "- Clientes não encontram você no Google\n"
        "- Não pode mostrar seus produtos/cardápio\n"
        "- Perde visibilidade online\n\n"
        "Posso criar um site profissional a partir de $50. "
        "Quer que eu faça um mockup grátis? 🙏"
    ),
    "fr": (
        "Bonjour! 👋\n\n"
        "J'ai trouvé {name} dans une recherche locale. "
        "Je suis développeur et j'aide les petites entreprises à avoir une présence en ligne.\n\n"
        "Beaucoup de petites entreprises n'ont pas encore de site:\n"
        "- Les clients ne vous trouvent pas sur Google\n"
        "- Vous ne pouvez pas montrer vos produits/menu\n"
        "- Vous perdez en visibilité en ligne\n\n"
        "Je peux créer un site professionnel à partir de 50€. "
        "Voulez-vous que je fasse un maquette gratuite? 🙏"
    ),
    "de": (
        "Hallo! 👋\n\n"
        "Ich habe {name} in einer lokalen Suche gefunden. "
        "Ich bin Entwickler und helfe kleinen Unternehmen, online präsent zu sein.\n\n"
        "Viele kleine Unternehmen haben noch keine Website:\n"
        "- Kunden finden Sie nicht bei Google\n"
        "- Sie können Ihre Produkte nicht zeigen\n"
        "- Sie verlieren Online-Sichtbarkeit\n\n"
        "Ich kann eine professionelle Website ab $50 erstellen. "
        "Soll ich ein kostenloses Mockup erstellen? 🙏"
    ),
    "ar": (
        "!مرحبا 👋\n\n"
        "وجدت {name} في بحث محلي. "
        "أنا مطور مساعد للشركات الصغيرة للحصول على حضور على الإنترنت.\n\n"
        "الكثير من الشركات الصغيرة ليس لها موقع بعد:\n"
        "- العملاء لا يجدونك على Google\n"
        "- لا يمكنك عرض منتجاتك/قائمة الطعام\n"
        "- تخسر الرؤية عبر الإنترنت\n\n"
        "يمكنني إنشاء موقع احترافي يبدأ من $50. "
        "هل تريد أن أعمل نموذج مجاني? 🙏"
    ),
    "hi": (
        "!नमस्ते 👋\n\n"
        "मैंने {name} को स्थानीय खोज में पाया। "
        "मैं एक वेब डेवलपर हूं जो छोटे व्यवसायों को ऑनलाइन उपस्थिति दिलाने में मदद करता हूं।\n\n"
        "कई छोटे व्यवसायों के पास अभी वेबसाइट नहीं है:\n"
        "- ग्राहक आपको Google पर नहीं ढूंढ पाते\n"
        "- आप अपने उत्पाद नहीं दिखा सकते\n"
        "- आप ऑनलाइन दृश्यता खो देते हैं\n\n"
        "मैं $50 से शुरू होकर एक पेशेवर वेबसाइट बना सकता हूं। "
        "क्या आप चाहते हैं कि मैं एक मुफ्त मॉकअप बनाऊं? 🙏"
    ),
    "th": (
        "สวัสดีครับ! 👋\n\n"
        "ผมพบ {name} จากการค้นหาในพื้นที่ "
        "ผมเป็นนักพัฒนาเว็บไซต์ที่ช่วยธุรกิจขนาดเล็กมีตัวตนบนออนไลน์\n\n"
        "ธุรกิจขนาดเล็กหลายแห่งยังไม่มีเว็บไซต์:\n"
        "- ลูกค้าหาคุณไม่เจอใน Google\n"
        "- ไม่สามารถแสดงสินค้า/เมนูได้\n"
        "- สูญเสียการมองเห็นบนออนไลน์\n\n"
        "ผมสามารถสร้างเว็บไซต์มืออาชีพเริ่มต้นที่ $50 "
        "ต้องการให้ผมทำ mockup ฟรีไหม? 🙏"
    ),
    "tr": (
        "Merhaba! 👋\n\n"
        "{name} yerel bir aramada bulundu. "
        "Küçük işletmelerin çevrimiçi varlık sahibi olmasına yardımcı olan bir web geliştiricisiyim.\n\n"
        "Birçok küçük işletmenin henüz web sitesi yok:\n"
        "- Müşteriler sizi Google'da bulamıyor\n"
        "- Ürünlerinizi gösteremiyorsunuz\n"
        "- Çevrimiçi görünürlük kaybediyorsunuz\n\n"
        "$50'den başlayan fiyatlarla profesyonel web sitesi yapabilirim. "
        "Ücretsiz bir mockup yapayım mı? 🙏"
    ),
}

# Global UMKM queries (specific small business types, not generic)
GLOBAL_LOCATIONS = [
    # Indonesia - warung/toko kecil
    ("warung", "Indonesia"), ("toko kelontong", "Indonesia"), ("warung kopi", "Indonesia"),
    ("laundry kiloan", "Indonesia"), ("bengkel motor", "Indonesia"), ("potong rambut", "Indonesia"),
    ("tukang jahit", "Indonesia"), ("toko bangunan", "Indonesia"), ("apotek", "Indonesia"),
    ("tokoh obat", "Indonesia"), ("warung makan", "Indonesia"), ("les privat", "Indonesia"),
    ("service AC", "Indonesia"), ("toko hp", "Indonesia"), ("cuci mobil", "Indonesia"),
    # Malaysia - kedai kecil
    ("kedai runcit", "Malaysia"), ("kedai gunting", "Malaysia"), ("kedai basikal", "Malaysia"),
    ("service motor", "Malaysia"), ("kedai kopi", "Malaysia"), ("restoran", "Malaysia"),
    ("kedai ubat", "Malaysia"), ("kedai emas", "Malaysia"),
    # Philippines - small shops
    ("sari-sari store", "Philippines"), ("carinderia", "Philippines"), ("ukay-ukay", "Philippines"),
    ("water refill", "Philippines"), ("vulcanizing shop", "Philippines"), ("computer shop", "Philippines"),
    ("laundry shop", "Philippines"), ("mini grocery", "Philippines"),
    # Thailand - ร้านเล็ก
    ("ร้านซ่อม", "Thailand"), ("ร้านตัดผม", "Thailand"), ("ร้านขายยา", "Thailand"),
    ("ร้านอาหารตามสั่ง", "Thailand"), ("ร้านกาแฟ", "Thailand"), ("ซักรีด", "Thailand"),
    ("ร้านโชห่วย", "Thailand"), ("ร้านขายของชำ", "Thailand"),
    # Vietnam - tiệm nhỏ
    ("tiệm sửa xe", "Vietnam"), ("quán phở", "Vietnam"), ("tiệm cắt tóc", "Vietnam"),
    ("quán nước", "Vietnam"), ("tiệm thuốc", "Vietnam"), ("tiệm giặt ủi", "Vietnam"),
    ("quán nhậu", "Vietnam"), ("tiệm tạp hóa", "Vietnam"),
    # India - choti dukan
    ("kirana store", "India"), ("pan shop", "India"), ("tailor shop", "India"),
    ("medical store", "India"), ("tea stall", "India"), ("cycle repair", "India"),
    ("saloon", "India"), ("hardware store", "India"),
    # Pakistan
    ("kirana", "Pakistan"), ("dukan", "Pakistan"), ("tailor", "Pakistan"),
    ("medical store", "Pakistan"), ("tea shop", "Pakistan"),
    # Bangladesh
    ("mudir dokan", "Bangladesh"), ("pharmacy", "Bangladesh"), ("tailor", "Bangladesh"),
    ("tea stall", "Bangladesh"), ("hardware", "Bangladesh"),
    # Middle East
    ("محل صغير", "UAE"), ("محل خياطة", "UAE"), ("محل صيانة", "UAE"),
    ("محل خضرة", "UAE"), ("بقالة", "Saudi Arabia"), ("محل صغير", "Saudi Arabia"),
    ("خياط", "Saudi Arabia"), ("صيدلية", "Saudi Arabia"),
    # Latin America - tiendas pequeñas
    ("tlapaleria", "Mexico"), ("abarrotes", "Mexico"), ("taller mecánico", "Mexico"),
    ("papelería", "Mexico"), ("farmacia", "Mexico"), ("lavandería", "Mexico"),
    ("minisuper", "Mexico"), ("taquería", "Mexico"),
    ("mercadinho", "Brazil"), ("barbearia", "Brazil"), ("lanchonete", "Brazil"),
    ("oficina", "Brazil"), ("pet shop", "Brazil"), ("salão de beleza", "Brazil"),
    ("kiosco", "Argentina"), ("rotisería", "Argentina"), ("carnicería", "Argentina"),
    ("verdulería", "Argentina"), ("librería", "Argentina"),
    ("tienda", "Colombia"), ("taller", "Colombia"), ("droguería", "Colombia"),
    ("papelería", "Colombia"), ("sastrería", "Colombia"),
    # Africa - small shops
    ("spaza shop", "South Africa"), ("tuck shop", "South Africa"), ("hair salon", "South Africa"),
    ("phone repair", "Nigeria"), ("provision store", "Nigeria"), ("barbing salon", "Nigeria"),
    ("chemist", "Kenya"), ("dukka", "Kenya"), ("mpesa shop", "Kenya"),
    # Turkey - küçük dükkan
    ("bakkal", "Turkey"), ("berber", "Turkey"), ("terzi", "Turkey"),
    ("eczane", "Turkey"), ("tamirhane", "Turkey"), ("çay bahçesi", "Turkey"),
    # Russia - маленький магазин
    ("продукты", "Russia"), ("парикмахерская", "Russia"), ("аптека", "Russia"),
    ("автомастерская", "Russia"), ("школьный", "Russia"),
    # Europe - small local shops
    ("bäckerei", "Germany"), ("metzgerei", "Germany"), ("friseur", "Germany"),
    ("boulangerie", "France"), ("boucherie", "France"), ("coiffeur", "France"),
    ("panadería", "Spain"), ("carnicería", "Spain"), ("peluquería", "Spain"),
    ("forno", "Italy"), ("macelleria", "Italy"), ("parrucchiere", "Italy"),
    ("padaria", "Portugal"), ("barbearia", "Portugal"), ("serralharia", "Portugal"),
    # Australia/NZ - local shops
    ("milk bar", "Australia"), ("fish and chips", "Australia"), ("kebab shop", "Australia"),
    ("bakery", "Australia"), ("hairdresser", "Australia"), ("chemist", "Australia"),
    ("dairy", "New Zealand"), ("fish and chip shop", "New Zealand"), ("bakery", "New Zealand"),
    # USA - small local businesses
    ("convenience store", "USA"), ("laundromat", "USA"), ("barber shop", "USA"),
    ("nail salon", "USA"), ("auto repair", "USA"), ("dry cleaner", "USA"),
    ("liquor store", "USA"), ("check cashing", "USA"),
    # ── Service businesses yang butuh website/aplikasi ──
    # Foto & Video
    ("studio foto", "Indonesia"), ("fotografer", "Indonesia"), ("videografer", "Indonesia"),
    ("cetak foto", "Indonesia"), ("photo booth", "Indonesia"),
    ("photo studio", "Malaysia"), ("photographer", "Philippines"),
    ("photo studio", "Thailand"), (" nhiếp ảnh", "Vietnam"),
    ("studio foto", "Mexico"), ("fotógrafo", "Argentina"), ("photographer", "USA"),
    ("photo studio", "UK"), ("fotograf", "Germany"), ("fotógrafo", "Brazil"),
    # Event & Wedding
    ("wedding organizer", "Indonesia"), ("event organizer", "Indonesia"),
    ("catering", "Indonesia"), ("dekorasi", "Indonesia"), ("mua", "Indonesia"),
    ("wedding planner", "Malaysia"), ("event planner", "Philippines"),
    ("แต่งงาน", "Thailand"), (" wedding organizer", "India"),
    ("bodas", "Indonesia"), ("resepsi", "Indonesia"),
    ("wedding organizer", "Mexico"), ("event planner", "USA"),
    ("wedding planner", "UK"), ("event agentur", "Germany"),
    # Salon & Kecantikan
    ("salon kecantikan", "Indonesia"), ("skin care", "Indonesia"),
    ("lash extension", "Indonesia"), ("nail art", "Indonesia"),
    ("klinik kecantikan", "Indonesia"), ("barbershop", "Indonesia"),
    ("beauty salon", "Malaysia"), ("nail salon", "Philippines"),
    ("เสริมสวย", "Thailand"), ("beauty parlor", "India"),
    ("salón de belleza", "Mexico"), ("esthetician", "USA"),
    ("beauty salon", "UK"), ("kosmetikstudio", "Germany"),
    # Fitness & Olahraga
    ("gym", "Indonesia"), ("yoga studio", "Indonesia"),
    ("personal trainer", "Indonesia"), ("fitness center", "Indonesia"),
    ("crossfit", "Indonesia"), ("pilates", "Indonesia"),
    ("gym", "Malaysia"), ("fitness", "Philippines"), ("ฟิตเนส", "Thailand"),
    ("gym", "Mexico"), ("gimnasio", "Argentina"), ("gym", "USA"),
    ("fitness studio", "UK"), ("fitnessstudio", "Germany"),
    # Kursus & Pelatihan
    ("kursus", "Indonesia"), ("bimbel", "Indonesia"), ("les privat", "Indonesia"),
    ("training center", "Indonesia"), ("lembaga kursus", "Indonesia"),
    ("tutor", "Malaysia"), ("cram school", "Philippines"),
    ("โรงเรียนกวดวิชา", "Thailand"), ("coaching center", "India"),
    ("academy", "Indonesia"), ("sekolah musik", "Indonesia"),
    ("music school", "Malaysia"), ("dance studio", "Philippines"),
    ("kursus", "Mexico"), ("academia", "Argentina"), ("tutoring", "USA"),
    # Otomotif & Teknisi
    ("bengkel cat", "Indonesia"), ("bengkel las", "Indonesia"),
    ("tuned shop", "Indonesia"), ("custom shop", "Indonesia"),
    ("speed shop", "Indonesia"), ("detailing mobil", "Indonesia"),
    ("auto detailing", "Malaysia"), ("car wash", "Philippines"),
    ("อู่ซ่อมรถ", "Thailand"), ("garage", "India"),
    ("taller", "Mexico"), ("mechanic shop", "USA"),
    ("workshop", "UK"), ("werkstatt", "Germany"),
    # Properti & Real Estate
    ("agen properti", "Indonesia"), ("konsultan properti", "Indonesia"),
    ("perumahan", "Indonesia"), ("real estate", "Indonesia"),
    ("property agent", "Malaysia"), ("real estate agent", "Philippines"),
    ("นายหน้าอสังหา", "Thailand"), ("real estate", "India"),
    ("inmobiliaria", "Mexico"), ("imobiliária", "Brazil"),
    ("real estate agent", "USA"), ("estate agent", "UK"),
    ("immobilien", "Germany"), ("agence immobilière", "France"),
    # Konsultan & Profesional
    ("konsultan", "Indonesia"), ("klinik hukum", "Indonesia"),
    ("kantor notaris", "Indonesia"), ("akuntan", "Indonesia"),
    ("konsultan pajak", "Indonesia"), ("management consulting", "Indonesia"),
    ("lawyer", "Malaysia"), ("accountant", "Philippines"),
    ("ทนายความ", "Thailand"), ("CA firm", "India"),
    ("consultor", "Mexico"), ("advogado", "Brazil"),
    ("consultant", "USA"), ("solicitor", "UK"),
    ("berater", "Germany"), ("consultant", "France"),
    # Travel & Tour
    ("agen travel", "Indonesia"), ("tour travel", "Indonesia"),
    ("paket wisata", "Indonesia"), ("rental mobil", "Indonesia"),
    ("travel agent", "Malaysia"), ("tour operator", "Philippines"),
    ("บริษัทท่องเที่ยว", "Thailand"), ("travel agent", "India"),
    ("agencia de viajes", "Mexico"), ("agência de viagem", "Brazil"),
    ("travel agency", "USA"), ("tour operator", "UK"),
    ("reisebüro", "Germany"), ("agence de voyage", "France"),
    # Gadget & Elektronik
    ("service hp", "Indonesia"), ("service laptop", "Indonesia"),
    ("toko aksesoris", "Indonesia"), ("counter pulsa", "Indonesia"),
    ("phone repair", "Malaysia"), ("computer shop", "Philippines"),
    ("ร้านซ่อม", "Thailand"), ("mobile repair", "India"),
    ("celular", "Mexico"), ("cell phone repair", "USA"),
    # Food & Beverage (spesifik)
    ("cake shop", "Indonesia"), ("kue tart", "Indonesia"),
    ("frozen food", "Indonesia"), ("katering", "Indonesia"),
    ("cloud kitchen", "Indonesia"), ("ghost kitchen", "Indonesia"),
    ("bakery", "Indonesia"), ("roti bakar", "Indonesia"),
    ("bakery", "Malaysia"), ("boulangerie", "France"),
    ("panadería", "Spain"), ("bäckerei", "Germany"),
    ("patisserie", "UK"), ("bakery", "USA"),
]

def detect_language(text):
    """Deteksi bahasa dari text (sederhana)"""
    text = text.lower()
    # Check for specific scripts
    if re.search(r'[\u0E00-\u0E7F]', text): return 'th'  # Thai
    if re.search(r'[\u0600-\u06FF]', text): return 'ar'  # Arabic
    if re.search(r'[\u0900-\u097F]', text): return 'hi'  # Hindi
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text): return 'ja'  # Japanese
    if re.search(r'[\uAC00-\uD7AF]', text): return 'ko'  # Korean
    if re.search(r'[\u4E00-\u9FFF]', text): return 'zh'  # Chinese
    if re.search(r'[\u1000-\u109F]', text): return 'my'  # Myanmar
    if re.search(r'[\u1780-\u17FF]', text): return 'km'  # Khmer
    if re.search(r'[\u0E80-\u0EFF]', text): return 'lo'  # Lao
    if re.search(r'[\u0400-\u04FF]', text): return 'ru'  # Russian/Cyrillic
    
    # Check for common words
    for lang, keywords in BIZ_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return lang
    
    # Default to English
    return 'en'

def get_dm_template(lang):
    """Dapatkan DM template berdasarkan bahasa"""
    return DM_TEMPLATES.get(lang, DM_TEMPLATES["en"])

def _is_global_target(name, address="", snippet=""):
    """Cek apakah bisnis ini target global (UMKM yang butuh website)"""
    text = f"{name} {address} {snippet}".lower()
    name_lower = name.lower()
    
    # Skip platform domains
    for dom in PLATFORM_DOMAINS:
        if dom in text:
            return False, "platform"
    
    # Skip big brands
    for brand in BIG_BRANDS:
        if brand in name_lower:
            return False, f"brand: {brand}"
    
    # Check if it's a small business (any language)
    for lang, keywords in BIZ_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return True, lang
    
    # Default: assume it's a small business if name is short
    if len(name) < 50:
        return True, "en"
    
    return False, "not target"

def _check_has_website(url, snippet=""):
    """Cek apakah bisnis sudah punya website"""
    if not url: return False
    url_lower = url.lower()
    
    # Skip platforms
    for dom in PLATFORM_DOMAINS:
        if dom in url_lower:
            return False
    
    # Check for actual website domains
    for ext in [".com",".co",".org",".net",".io",".shop",".store",
                ".id",".co.id",".web.id",".co.th",".co.jp",".co.kr",
                ".com.au",".co.uk",".de",".fr",".es",".it",".pt",
                ".ru",".ua",".pl",".cz",".nl",".be",".at",".ch",
                ".se",".no",".dk",".fi",".ie",".nz",".za",
                ".com.br",".com.ar",".com.mx",".com.co",".com.pe",
                ".ae",".sa",".qa",".kw",".bh",".om",
                ".com.ng",".co.ke",".co.za",".com.gh",
                ".tr",".pk",".bd",".lk",".np"]:
        if ext in url_lower:
            return True
    
    return False

def _get(data, *indices, default=None):
    """Safe nested list access."""
    current = data
    for idx in indices:
        if not isinstance(current, (list, tuple)): return default
        if idx < 0 or idx >= len(current): return default
        current = current[idx]
    return current if current is not None else default

def _build_maps_search_url(query, lat, lng, zoom=13, lang="en", gl="us", page_size=20, start=0):
    """Build Google Maps internal tbm=map search URL with protobuf pb parameter."""
    from urllib.parse import quote
    span = 360 / (2 ** zoom)
    d_value = span * 111320
    pb = (
        f"!4m12!1m3!1d{d_value}!2d{lng}!3d{lat}"
        f"!2m3!1f0!2f0!3f0!3m2!1i1280!2i593!4f13.1"
        f"!7i{page_size}"
    )
    if start > 0:
        pb += f"!8i{start}"
    pb += (
        "!10b1"
        "!12m25!1m5!18b1!30b1!31m1!1b1!34e1!2m4!5m1!6e2!20e3!39b1"
        "!10b1!12b1!13b1!16b1!17m1!3e1!20m3!5e2!6b1!14b1!46m1!1b0!96b1!99b1"
        "!19m4!2m3!1i360!2i120!4i8"
        "!20m65!2m2!1i203!2i100!3m2!2i4!5b1"
        "!6m6!1m2!1i86!2i86!1m2!1i408!2i240"
        "!7m33!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3"
        "!1m3!1e8!2b0!3e3!1m3!1e10!2b0!3e3!1m3!1e10!2b1!3e2"
        "!1m3!1e10!2b0!3e4!1m3!1e9!2b1!3e2!2b1!9b0"
        "!15m16!1m7!1m2!1m1!1e2!2m2!1i195!2i195!3i20"
        "!1m7!1m2!1m1!1e2!2m2!1i195!2i195!3i20"
        "!22m2!1sdummy!7e81"
        "!24m109!1m27!13m9!2b1!3b1!4b1!6i1!8b1!9b1!14b1!20b1!25b1"
        "!18m16!3b1!4b1!5b1!6b1!9b1!13b1!14b1!17b1!20b1!21b1!22b1"
        "!32b1!33m1!1b1!34b1!36e2"
        "!10m1!8e3!11m1!3e1!17b1!20m2!1e3!1e6"
        "!24b1!25b1!26b1!27b1!29b1!30m1!2b1!36b1!37b1"
        "!39m3!2m2!2i1!3i1!43b1!52b1!54m1!1b1!55b1!56m1!1b1"
        "!61m2!1m1!1e1!65m5!3m4!1m3!1m2!1i224!2i298"
        "!72m22!1m8!2b1!5b1!7b1!12m4!1b1!2b1!4m1!1e1!4b1"
        "!8m10!1m6!4m1!1e1!4m1!1e3!4m1!1e4"
        "!3sother_user_google_review_posts__and__hotel_and_vr_partner_review_posts"
        "!6m1!1e1!9b1!89b1!90m2!1m1!1e2"
        "!98m3!1b1!2b1!3b1!103b1!113b1!114m3!1b1!2m1!1b1"
        "!117b1!122m1!1b1!126b1!127b1!128m1!1b0"
        "!26m4!2m3!1i80!2i92!4i8"
        "!30m28!1m6!1m2!1i0!2i0!2m2!1i530!2i593"
        "!1m6!1m2!1i1230!2i0!2m2!1i1280!2i593"
        "!1m6!1m2!1i0!2i0!2m2!1i1280!2i20"
        "!1m6!1m2!1i0!2i573!2m2!1i1280!2i593"
        "!34m19!2b1!3b1!4b1!6b1!8m6!1b1!3b1!4b1!5b1!6b1!7b1"
        "!9b1!12b1!14b1!20b1!23b1!25b1!26b1!31b1"
        "!37m1!1e81!42b1!47m0"
        "!49m10!3b1!6m2!1b1!2b1!7m2!1e3!2b1!8b1!9b1!10e2"
        "!50m4!2e2!3m2!1b1!3b1"
        "!67m5!7b1!10b1!14b1!15m1!1b0!69i775!77b1"
    )
    return (
        f"https://www.google.com/search?tbm=map&authuser=0&hl={lang}&gl={gl}"
        f"&pb={pb}&q={quote(query)}&tch=1&ech=1&psi=dummy.{int(time.time()*1000)}.1"
    )

def _build_maps_place_url(place_id, lat, lng, lang="en", gl="us"):
    """Build Google Maps place detail URL with protobuf pb parameter."""
    from urllib.parse import quote
    enc_pid = quote(place_id, safe="")
    return (
        f"https://www.google.com/maps/preview/place?authuser=0&hl={lang}&gl={gl}"
        f"&pb=!1m6!1s{enc_pid}!3m1!1d1000"
        f"!4m2!3d{lat}!4d{lng}!3m1!1e3"
    )

def _is_real_phone(s):
    """Filter out Google internal IDs from phone numbers."""
    if not s or not isinstance(s, str): return False
    s = s.strip()
    if len(s) < 8 or len(s) > 25: return False
    if re.search(r'http|html|script|gstatic|google|png|svg|\.com|\.org', s.lower()): return False
    digits = re.sub(r'[\s\-\(\)\+\.\/]', '', s)
    if not digits.isdigit(): return False
    if len(digits) < 7 or len(digits) > 15: return False
    # Google IDs are raw long digit strings without separators
    has_separators = bool(re.search(r'[\s\-\(\)\+\.\/]', s))
    if not has_separators and len(digits) >= 12:
        return False
    return True

def _parse_maps_search_response(raw_text):
    """Parse Google Maps tbm=map search response. Returns list of business dicts."""
    try:
        if raw_text.startswith(")]}'"):
            raw_text = raw_text[4:].lstrip("\n")
        decoder = json.JSONDecoder()
        outer, _ = decoder.raw_decode(raw_text)
        inner_text = outer["d"] if isinstance(outer, dict) and "d" in outer else raw_text
        if inner_text.startswith(")]}'"):
            inner_text = inner_text[4:].lstrip("\n")
        data = json.loads(inner_text)
    except:
        return []

    # Find listings array (biggest array with many list entries)
    listings = []
    if isinstance(data, list):
        for i in range(len(data) - 1, -1, -1):
            elem = data[i]
            if not isinstance(elem, list): continue
            for entry in elem:
                if isinstance(entry, list) and len(entry) >= 2:
                    if isinstance(entry[1], list) and len(entry[1]) > 50:
                        listings = elem
                        break
            if listings: break

    results = []
    for item in listings:
        if not (isinstance(item, list) and isinstance(item[1], list)):
            continue
        pd = item[1]
        if len(pd) < 20: continue
        name = _get(pd, 11, default="")
        pid = _get(pd, 10, default="")
        if not name or not pid: continue
        addr = _get(pd, 18, default="")
        cat_list = _get(pd, 13, default=[])
        cat = cat_list[0] if isinstance(cat_list, list) and cat_list else ""
        rating = _get(pd, 4, 7, default=0)
        reviews = _get(pd, 4, 8, default=0)
        lat_v = _get(pd, 9, 2, default=0)
        lng_v = _get(pd, 9, 3, default=0)
        # Website from search (if available)
        website = _get(pd, 7, 0, default="")
        if isinstance(website, list): website = _get(pd, 7, 0, 0, default="")
        if not isinstance(website, str): website = ""
        if not website.startswith("http"): website = ""

        results.append({
            "name": name,
            "place_id": pid,
            "address": addr,
            "category": cat,
            "rating": rating,
            "reviews": reviews,
            "lat": lat_v,
            "lng": lng_v,
            "website": website,
        })
    return results

def _parse_maps_place_detail(raw_text):
    """Parse Google Maps place detail response. Returns dict with phone, website, email."""
    result = {"phone": "", "website": "", "email": ""}
    try:
        if raw_text.startswith(")]}'"):
            raw_text = raw_text[4:].lstrip("\n")
        data = json.loads(raw_text)
    except:
        return result

    # Phone at data[6][178][0][0]
    phone = _get(data, 6, 178, 0, 0, default="")
    if _is_real_phone(phone):
        result["phone"] = phone
    else:
        # Recursive search for phone in top-level array
        def _find_phone(obj, d=0):
            if d > 8: return ""
            if isinstance(obj, str) and _is_real_phone(obj): return obj
            if isinstance(obj, list):
                for item in obj[:100]:
                    r = _find_phone(item, d+1)
                    if r: return r
            return ""
        result["phone"] = _find_phone(data)

    # Website at data[6][7][0]
    web_list = _get(data, 6, 7, default=[])
    if isinstance(web_list, list) and web_list:
        website = _get(web_list, 0, default="")
        if isinstance(website, str) and website.startswith("http"):
            result["website"] = website

    # Email at data[6][178][0][2] or recursive
    email = _get(data, 6, 178, 0, 2, default="")
    if isinstance(email, str) and "@" in email and "." in email:
        result["email"] = email
    else:
        def _find_email(obj, d=0):
            if d > 8: return ""
            if isinstance(obj, str):
                m = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', obj)
                if m and "google.com" not in m.group(0):
                    return m.group(0)
            if isinstance(obj, list):
                for item in obj[:50]:
                    r = _find_email(item, d+1)
                    if r: return r
            return ""
        result["email"] = _find_email(data)

    return result

def scrape_google_maps(query, max_results=20, lat=0, lng=0, zoom=13, lang="en", gl="us"):
    """Scrape Google Maps using SerpApi (primary) + tbm=map (fallback).
    
    Strategy:
    1. SerpApi Google Maps search → structured results with phones
    2. Fallback: tbm=map search + place detail enrichment
    3. Filter: skip platforms, big brands, businesses with websites
    """
    try:
        import requests
    except ImportError:
        return [], "pip install requests dulu"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    businesses = []
    seen_names = set()
    seen_phones = set()
    stats = {"total": 0, "no_phone": 0, "has_website": 0, "not_target": 0, "duplicate": 0}

    def _add(name, phone="", address="", rating="", reviews="", website="", category="", snippet=""):
        nonlocal stats
        name = name.strip()
        if not name or len(name) < 3: return
        key = name.lower().strip()
        if key in seen_names:
            stats["duplicate"] += 1; return
        for dom in PLATFORM_DOMAINS:
            if dom in key: return
        if _check_has_website(website, snippet):
            stats["has_website"] += 1; return
        is_target, det_lang = _is_global_target(name, address, snippet)
        if not is_target:
            stats["not_target"] += 1; return
        ph_clean = re.sub(r'[\s\-\(\)\+]', '', phone) if phone else ""
        if ph_clean:
            ph_digits = re.sub(r'\D', '', ph_clean)
            if len(ph_digits) < 8 or len(ph_digits) > 15:
                ph_clean = ""
        if ph_clean:
            ph_digits = re.sub(r'\D', '', ph_clean)
            if ph_digits in seen_phones:
                stats["duplicate"] += 1; return
            seen_phones.add(ph_digits)
        seen_names.add(key)
        businesses.append({
            "name": name, "phone": ph_clean, "address": address.strip(),
            "rating": str(rating), "reviews": str(reviews),
            "website": website.strip(), "category": category.strip(),
            "lang": det_lang, "snippet": snippet[:200] if snippet else "",
        })

    # ── Source 1: SerpApi (primary, multi-key fallback) ──
    print(f"  {C}[1/3] SerpApi Google Maps search...{R}")
    serp_count = 0

    def _try_serpapi(api_key, query, lat, lng, zoom):
        """Try SerpApi with single key, return results"""
        params = {
            "engine": "google_maps",
            "q": query,
            "ll": f"@{lat},{lng},{zoom}z",
            "type": "search",
            "api_key": api_key,
        }
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        return resp.json()

    def _parse_serpapi_results(data):
        """Parse SerpApi results into businesses"""
        nonlocal serp_count
        results = []
        if "local_results" in data:
            for r in data["local_results"]:
                results.append({
                    "name": r.get("title", ""),
                    "phone": r.get("phone", ""),
                    "address": r.get("address", ""),
                    "rating": r.get("rating", ""),
                    "reviews": r.get("reviews", ""),
                    "website": r.get("website", ""),
                    "category": r.get("type", ""),
                    "snippet": r.get("place_id_search", ""),
                })
        return results

    # Try each key until one works
    keys = _load_api_keys()
    for ki, api_key in enumerate(keys):
        masked = api_key[:8] + "..." + api_key[-6:] if len(api_key) > 20 else api_key
        print(f"    {D}→ Coba key [{ki+1}/{len(keys)}]: {masked}{R}")
        try:
            data = _try_serpapi(api_key, query, lat, lng, zoom)

            # Check if key hit rate limit
            if "error" in data:
                err_msg = data.get("error", "")
                if "429" in err_msg or "rate" in err_msg.lower() or "limit" in err_msg.lower():
                    print(f"    {Y}→ Key [{ki+1}] limit! Coba key berikutnya...{R}")
                    continue
                else:
                    print(f"    {RED}→ SerpApi error: {err_msg}{R}")
                    continue

            # Parse results
            results = _parse_serpapi_results(data)
            for r in results:
                _add(r["name"], phone=r["phone"], address=r["address"],
                     rating=r["rating"], reviews=r["reviews"], website=r["website"],
                     category=r["category"], snippet=r["snippet"])
            serp_count = len(results)

            # Pagination - get next pages
            if "serpapi_pagination" in data and serp_count > 0:
                next_pages = data["serpapi_pagination"].get("other_pages", {})
                for page_key, page_url in list(next_pages.items())[:2]:
                    try:
                        resp2 = requests.get(page_url, timeout=20)
                        data2 = resp2.json()
                        if "local_results" in data2:
                            for r in data2["local_results"]:
                                _add(r.get("title",""), phone=r.get("phone",""),
                                     address=r.get("address",""), rating=r.get("rating",""),
                                     reviews=r.get("reviews",""), website=r.get("website",""),
                                     category=r.get("type",""))
                            serp_count += len(data2["local_results"])
                        time.sleep(0.5)
                    except: break

            print(f"    {G}→ {serp_count} hasil dari SerpApi (key {ki+1}){R}")
            break  # Success! Don't try next key

        except requests.exceptions.RequestException as e:
            if "429" in str(e) or "rate" in str(e).lower():
                print(f"    {Y}→ Key [{ki+1}] rate limited! Coba key berikutnya...{R}")
                continue
            else:
                print(f"    {RED}→ Key [{ki+1}] error: {e}{R}")
                continue
        except Exception as e:
            print(f"    {RED}→ Key [{ki+1}] error: {e}{R}")
            continue

    if serp_count == 0 and keys:
        print(f"    {Y}→ Semua key limit/gagal, fallback ke tbm=map{R}")

    # ── Source 2: tbm=map search (fallback / supplement) ──
    if serp_count == 0:
        print(f"  {C}[2/3] Google Maps tbm=map search (fallback)...{R}")
        try:
            search_url = _build_maps_search_url(query, lat, lng, zoom=zoom, lang=lang, gl=gl, page_size=20)
            resp = requests.get(search_url, headers=headers, timeout=15)
            search_results = _parse_maps_search_response(resp.text)
            for sr in search_results:
                key = sr["name"].lower().strip()
                if key in seen_names: continue
                is_t, det_lang = _is_global_target(sr["name"], sr["address"], sr.get("category",""))
                if not is_t: continue
                if _check_has_website(sr["website"]):
                    stats["has_website"] += 1; continue
                businesses.append({
                    "name": sr["name"], "phone": "", "address": sr["address"],
                    "rating": str(sr.get("rating","")), "reviews": str(sr.get("reviews","")),
                    "website": sr["website"], "category": sr.get("category",""),
                    "lang": det_lang, "place_id": sr["place_id"],
                    "lat": sr["lat"], "lng": sr["lng"], "snippet": "",
                })
                seen_names.add(key)
            print(f"    {D}→ {len(search_results)} hasil dari tbm=map{R}")
        except Exception as e:
            print(f"    {RED}→ Error: {e}{R}")
    else:
        print(f"  {C}[2/3] SerpApi cukup, skip tbm=map{R}")

    # ── Source 3: Enrich phone via place detail (only for tbm=map results without phone) ──
    need_enrich = [b for b in businesses if not b.get("phone") and b.get("place_id")]
    if need_enrich:
        print(f"  {C}[3/3] Enriching {len(need_enrich)} nomor via place detail...{R}")
        enriched = 0
        for b in need_enrich[:20]:
            pid = b.pop("place_id", "")
            lat_v = b.pop("lat", 0)
            lng_v = b.pop("lng", 0)
            if not pid or not lat_v: continue
            try:
                det_url = _build_maps_place_url(pid, lat_v, lng_v, lang=lang, gl=gl)
                det_resp = requests.get(det_url, headers=headers, timeout=12)
                detail = _parse_maps_place_detail(det_resp.text)
                if detail["phone"] and _is_real_phone(detail["phone"]):
                    ph = re.sub(r'[\s\-\(\)\+]', '', detail["phone"])
                    b["phone"] = ph
                    enriched += 1
                if detail["website"] and not b["website"]:
                    b["website"] = detail["website"]
                time.sleep(0.3)
            except: continue
        print(f"    {D}→ {enriched} nomor ditemukan{R}")
    else:
        print(f"  {C}[3/3] Semua sudah ada nomor, skip enrichment{R}")

    # Filter: only with phone
    with_phone = [b for b in businesses if b.get("phone")]
    without_phone = [b for b in businesses if not b.get("phone")]

    print(f"\n  {G}✓ Total: {len(with_phone)} target dengan nomor HP{R}")
    if without_phone:
        print(f"    {D}  tanpa nomor: {len(without_phone)} (dihapus){R}")
    if stats["has_website"]:
        print(f"    {D}  skip sudah ada web: {stats['has_website']}{R}")
    if stats["not_target"]:
        print(f"    {D}  skip bukan target: {stats['not_target']}{R}")
    if stats["duplicate"]:
        print(f"    {D}  skip duplikat: {stats['duplicate']}{R}")

    return with_phone[:max_results], None

def _generate_grid_cells(lat, lng, zoom=13, grid_size=3):
    """Generate grid cells around a center point for better coverage.
    
    At zoom 13, the visible area is ~5km. Split into grid_size x grid_size cells.
    Each cell covers ~1.7km which is perfect for finding neighborhood businesses.
    """
    # Approximate degrees per km at this latitude
    km_per_deg_lat = 111.0
    km_per_deg_lng = 111.0 * abs(math.cos(math.radians(lat)))
    
    # Visible area at zoom 13 ≈ 5km x 5km
    visible_km = 5.0
    cell_km = visible_km / grid_size
    
    cells = []
    for i in range(grid_size):
        for j in range(grid_size):
            cell_lat = lat + (i - grid_size/2 + 0.5) * cell_km / km_per_deg_lat
            cell_lng = lng + (j - grid_size/2 + 0.5) * cell_km / km_per_deg_lng
            cells.append((cell_lat, cell_lng))
    return cells

def scrape_grid(query, max_results=20, lat=0, lng=0, zoom=13, lang="en", gl="us", grid_size=3):
    """Grid-based search: split area into cells, search each for better coverage."""
    try:
        import requests
    except ImportError:
        return [], "pip install requests dulu"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    businesses = []
    seen_names = set()
    seen_phones = set()
    stats = {"total": 0, "no_phone": 0, "has_website": 0, "not_target": 0, "duplicate": 0}

    def _add(name, phone="", address="", rating="", reviews="", website="", category="", snippet=""):
        nonlocal stats
        name = name.strip()
        if not name or len(name) < 3: return
        key = name.lower().strip()
        if key in seen_names:
            stats["duplicate"] += 1; return
        for dom in PLATFORM_DOMAINS:
            if dom in key: return
        if _check_has_website(website, snippet):
            stats["has_website"] += 1; return
        is_target, det_lang = _is_global_target(name, address, snippet)
        if not is_target:
            stats["not_target"] += 1; return
        ph_clean = re.sub(r'[\s\-\(\)\+]', '', phone) if phone else ""
        if ph_clean:
            ph_digits = re.sub(r'\D', '', ph_clean)
            if len(ph_digits) < 8 or len(ph_digits) > 15:
                ph_clean = ""
        if ph_clean:
            ph_digits = re.sub(r'\D', '', ph_clean)
            if ph_digits in seen_phones:
                stats["duplicate"] += 1; return
            seen_phones.add(ph_digits)
        seen_names.add(key)
        businesses.append({
            "name": name, "phone": ph_clean, "address": address.strip(),
            "rating": str(rating), "reviews": str(reviews),
            "website": website.strip(), "category": category.strip(),
            "lang": det_lang, "snippet": snippet[:200] if snippet else "",
        })

    cells = _generate_grid_cells(lat, lng, zoom, grid_size)
    print(f"  {C}Grid: {grid_size}x{grid_size} = {len(cells)} cells{R}")

    for ci, (cell_lat, cell_lng) in enumerate(cells):
        if len(businesses) >= max_results:
            break

        # SerpApi for this cell with multi-key fallback
        if SERP_API_KEYS:
            key_used = False
            for api_key in SERP_API_KEYS:
                try:
                    params = {
                        "engine": "google_maps",
                        "q": query,
                        "ll": f"@{cell_lat},{cell_lng},{zoom}z",
                        "type": "search",
                        "api_key": api_key,
                    }
                    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
                data = resp.json()
                if "local_results" in data:
                    for r in data["local_results"]:
                        name = r.get("title", "")
                        phone = r.get("phone", "")
                        address = r.get("address", "")
                        rating = r.get("rating", "")
                        reviews = r.get("reviews", "")
                        website = r.get("website", "")
                        category = r.get("type", "")
                        _add(name, phone=phone, address=address, rating=rating,
                             reviews=reviews, website=website, category=category)
                    # Get next pages
                    if "serpapi_pagination" in data:
                        next_pages = data["serpapi_pagination"].get("other_pages", {})
                        for page_url in list(next_pages.values())[:1]:
                            try:
                                resp2 = requests.get(page_url, timeout=20)
                                data2 = resp2.json()
                                if "local_results" in data2:
                                    for r in data2["local_results"]:
                                        _add(r.get("title",""), phone=r.get("phone",""),
                                             address=r.get("address",""), rating=r.get("rating",""),
                                             reviews=r.get("reviews",""), website=r.get("website",""),
                                             category=r.get("type",""))
                                time.sleep(0.3)
                            except: break
                    time.sleep(0.5)
                    key_used = True
                    break  # Key worked, stop trying others
                except:
                    continue  # This key failed, try next
            if not key_used:
                # All keys failed, try tbm=map fallback
                try:
                    search_url = _build_maps_search_url(query, cell_lat, cell_lng, zoom=zoom, lang=lang, gl=gl, page_size=20)
                    resp = requests.get(search_url, headers=headers, timeout=15)
                    search_results = _parse_maps_search_response(resp.text)
                    for sr in search_results:
                        key = sr["name"].lower().strip()
                        if key in seen_names: continue
                        is_t, det_lang = _is_global_target(sr["name"], sr["address"], sr.get("category",""))
                        if not is_t: continue
                        if _check_has_website(sr["website"]):
                        stats["has_website"] += 1; continue
                    businesses.append({
                        "name": sr["name"], "phone": "", "address": sr["address"],
                        "rating": str(sr.get("rating","")), "reviews": str(sr.get("reviews","")),
                        "website": sr["website"], "category": sr.get("category",""),
                        "lang": det_lang, "place_id": sr["place_id"],
                        "lat": sr["lat"], "lng": sr["lng"], "snippet": "",
                    })
                    seen_names.add(key)
                time.sleep(0.3)
            except: continue

    # Enrich phones for tbm=map results without phone
    need_enrich = [b for b in businesses if not b.get("phone") and b.get("place_id")]
    if need_enrich:
        print(f"  {C}Enriching {len(need_enrich)} phones...{R}")
        for b in need_enrich[:15]:
            pid = b.pop("place_id", "")
            lat_v = b.pop("lat", 0)
            lng_v = b.pop("lng", 0)
            if not pid or not lat_v: continue
            try:
                det_url = _build_maps_place_url(pid, lat_v, lng_v, lang=lang, gl=gl)
                det_resp = requests.get(det_url, headers=headers, timeout=12)
                detail = _parse_maps_place_detail(det_resp.text)
                if detail["phone"] and _is_real_phone(detail["phone"]):
                    b["phone"] = re.sub(r'[\s\-\(\)\+]', '', detail["phone"])
                time.sleep(0.3)
            except: continue

    # Filter: only with phone
    with_phone = [b for b in businesses if b.get("phone")]
    print(f"\n  {G}✓ Grid: {len(with_phone)} target dengan nomor HP{R}")
    if stats["has_website"]:
        print(f"    {D}  skip sudah ada web: {stats['has_website']}{R}")
    if stats["not_target"]:
        print(f"    {D}  skip bukan target: {stats['not_target']}{R}")
    if stats["duplicate"]:
        print(f"    {D}  skip duplikat: {stats['duplicate']}{R}")

    return with_phone[:max_results], None
#  CSV
# ──────────────────────────────────────────────────────────────

def save_csv(businesses, filename):
    os.makedirs(DATA_DIR, exist_ok=True)
    fp = os.path.join(DATA_DIR, filename)
    fields = ["name","address","phone","rating","reviews","website","category"]
    with open(fp,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for b in businesses: w.writerow({k: b.get(k,"") for k in fields})
    return fp

def list_csv():
    if not os.path.exists(DATA_DIR): return []
    return [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

# ──────────────────────────────────────────────────────────────
#  DISPLAY
# ──────────────────────────────────────────────────────────────

def display_results(biz):
    print(f"\n  {B}{C}{'='*60}{R}")
    print(f"  {B}{C}  HASIL: {len(biz)} bisnis ditemukan{R}")
    print(f"  {B}{C}{'='*60}{R}\n")
    for i, b in enumerate(biz, 1):
        print(f"  {B}{RAINBOW[i%len(RAINBOW)]}[{i}]{R} {B}{b.get('name','N/A')}{R}")
        if b.get("category"): print(f"      {D}Kategori:{R}  {b['category']}")
        if b.get("address"):  print(f"      {D}Alamat:{R}    {b['address']}")
        if b.get("phone"):    print(f"      {D}Telepon:{R}   {b['phone']}")
        if b.get("rating"):   print(f"      {D}Rating:{R}    ★ {b['rating']}" + (f" ({b['reviews']} ulasan)" if b.get("reviews") else ""))
        if b.get("website"):  print(f"      {D}Website:{R}   {b['website']}")
        print()

# ──────────────────────────────────────────────────────────────
#  WHATSAPP (via Baileys Node.js)
# ──────────────────────────────────────────────────────────────

def run_node(script, args=None, timeout=30):
    if args is None: args = []
    cmd = ["node", script] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=HOME)
        return r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", -1
    except Exception as e:
        return "", str(e), -1

def read_status():
    if not os.path.exists(STATUS_FILE): return {}
    try:
        with open(STATUS_FILE) as f: return json.load(f)
    except: return {}

def is_wa_connected():
    s = read_status()
    return s.get("connected", False)

def flow_settings():
    """WhatsApp Settings: Login, Logout, Ganti Nomor, Status"""
    while True:
        clear(); rainbow_banner()
        print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
        print(box_line("SETTING WHATSAPP", f"{B}{G}"))
        print(box_line(""))

        # Cek status
        wa_status = "❌ Belum terhubung"
        wa_phone = "-"
        wa_acc_count = 0
        if os.path.exists(STATUS_FILE):
            try:
                with open(STATUS_FILE) as f: st = json.load(f)
                if st.get("connected"):
                    wa_status = "✅ Terhubung"
                    wa_phone = st.get("phone", "-")
            except: pass
        if os.path.exists(ACC_FILE):
            try:
                with open(ACC_FILE) as f: wa_acc_count = len(json.load(f))
            except: pass

        print(box_line(f"Status: {wa_status}", C))
        print(box_line(f"Nomor: {wa_phone}", C))
        print(box_line(f"Klien acc: {wa_acc_count}/3", C))
        print(box_line(""))
        print(box_line("[1] Login / Pair WhatsApp", Y))
        print(box_line("[2] Logout (reset sesi)", Y))
        print(box_line("[3] Ganti nomor WhatsApp", Y))
        print(box_line("[4] Cek status detail", Y))
        print(box_line("[0] Kembali", D))
        print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

        ch = input(f"  {G}▸ Pilih: {R}").strip()

        if ch == "1":
            _pair_whatsapp()
        elif ch == "2":
            _logout_whatsapp()
        elif ch == "3":
            _switch_number()
        elif ch == "4":
            _show_status()
        elif ch == "0":
            return

def _pair_whatsapp():
    """Pair WhatsApp baru"""
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("PAIR WHATSAPP", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Cara pairing:", Y))
    print(box_line("1. Buka WhatsApp di HP", D))
    print(box_line("2. Settings > Linked Devices", D))
    print(box_line("3. Link a Device", D))
    print(box_line("4. Link with Phone Number Instead", D))
    print(box_line("5. Masukkan kode yang muncul", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    input(f"  {G}▸ Tekan Enter untuk mulai pairing...{R}")
    print(f"\n  {C}[*] Menjalankan Baileys pairing...{R}")
    print(f"  {D}(Tunggu sampai kode muncul, lalu masukkan di WhatsApp){R}\n")

    proc = subprocess.Popen(
        ["node", WA_SCRIPT, "pair"],
        cwd=HOME, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    try:
        for line in proc.stdout:
            print(f"  {D}{line.rstrip()}{R}")
    except KeyboardInterrupt:
        proc.terminate()
    proc.wait()
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

def _logout_whatsapp():
    """Logout / reset sesi WhatsApp"""
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("LOGOUT WHATSAPP", f"{B}{RED}"))
    print(box_line(""))
    print(box_line("Ini akan menghapus sesi WhatsApp.", RED))
    print(box_line("Anda perlu login ulang untuk mengirim DM.", RED))
    print(box_line(""))
    print(box_line("[1] Ya, logout", RED))
    print(box_line("[0] Batal", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    ch = input(f"  {G}▸ Pilih: {R}").strip()
    if ch != "1":
        print(f"  {D}Dibatalkan.{R}"); time.sleep(1); return

    # Hapus sesi
    import shutil
    auth_dir = os.path.expanduser("~/.astral_auth")
    if os.path.exists(auth_dir):
        shutil.rmtree(auth_dir)
        print(f"  {G}✓ Sesi WhatsApp dihapus.{R}")

    # Reset status
    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)
        print(f"  {G}✓ Status direset.{R}")

    print(f"\n  {Y}WhatsApp sudah logout. Pilih 'Login / Pair WhatsApp' untuk login ulang.{R}")
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

def _switch_number():
    """Ganti nomor WhatsApp"""
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("GANTI NOMOR WHATSAPP", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Logout sesi lama, lalu pair nomor baru.", Y))
    print(box_line(""))

    # Logout dulu
    import shutil
    auth_dir = os.path.expanduser("~/.astral_auth")
    if os.path.exists(auth_dir):
        shutil.rmtree(auth_dir)
        print(f"  {G}✓ Sesi lama dihapus.{R}")

    if os.path.exists(STATUS_FILE):
        os.remove(STATUS_FILE)

    print(f"\n  {C}Sekarang pair nomor baru.{R}")
    input(f"  {G}▸ Tekan Enter untuk mulai pairing...{R}")

    proc = subprocess.Popen(
        ["node", WA_SCRIPT, "pair"],
        cwd=HOME, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    try:
        for line in proc.stdout:
            print(f"  {D}{line.rstrip()}{R}")
    except KeyboardInterrupt:
        proc.terminate()
    proc.wait()
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

def _show_status():
    """Tampilkan status detail"""
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("STATUS WHATSAPP", f"{B}{G}"))
    print(box_line(""))

    if not os.path.exists(STATUS_FILE):
        print(box_line("Belum ada data status.", RED))
    else:
        try:
            with open(STATUS_FILE) as f: st = json.load(f)
            print(box_line(f"Connected: {st.get('connected', False)}", C))
            print(box_line(f"Paired: {st.get('paired', False)}", C))
            print(box_line(f"Phone: {st.get('phone', '-')}", C))
            print(box_line(f"Last update: {st.get('ts', '-')}", D))
        except: pass

    # ACC status
    if os.path.exists(ACC_FILE):
        try:
            with open(ACC_FILE) as f: acc = json.load(f)
            print(box_line(""))
            print(box_line(f"Klien acc: {len(acc)}/3", G))
            for a in acc:
                print(box_line(f"  ✓ {a['name']} ({a['phone']})", G))
        except: pass

    # Sent stats
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE) as f: sent = json.load(f)
            today = sum(1 for v in sent.values()
                       if time.time() - time.mktime(time.strptime(v["ts"][:19], "%Y-%m-%dT%H:%M:%S")) < 86400)
            print(box_line(""))
            print(box_line(f"Total nomor dikirim: {len(sent)}", C))
            print(box_line(f"Dikirim hari ini: {today}", C))
        except: pass

    print(f"  {B}{M}+{'='*WIDTH}+{R}")
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

def flow_send():
    clear(); rainbow_banner()
    csvs = list_csv()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("KIRIM WA DM BULK (Baileys)", f"{B}{G}"))
    print(box_line(""))

    if not csvs:
        print(box_line("Belum ada data scrape!", RED))
        print(box_line("Scrape Google Maps dulu.", D))
        print(f"  {B}{M}+{'='*WIDTH}+{R}")
        input(f"\n  {D}Tekan Enter untuk kembali...{R}")
        return

    for i, f in enumerate(csvs):
        print(box_line(f"[{i+1}] {f}", C))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    choice = input(f"  {G}▸ Pilih nomor CSV: {R}").strip()
    if not choice.isdigit() or int(choice)<1 or int(choice)>len(csvs):
        print(f"  {RED}[!] Pilihan invalid.{R}"); time.sleep(1); return
    csv_file = os.path.join(DATA_DIR, csvs[int(choice)-1])

    DEFAULT_MSG = (
        "Halo, Kak 👋\n\n"
        "Saya lihat usaha {name} dari pencarian lokal. "
        "Kebetulan saya developer yang fokus bantu UMKM punya website profesional.\n\n"
        "Saya perhatikan banyak UMKM yang belum punya website, padahal:\n"
        "- Calon pelanggan gampang nemuin usaha via Google\n"
        "- Bisa tampilkan menu/produk + harga langsung\n"
        "  (cocok banget buat UMKM yang belum ada di Shopee/Tokopedia)\n"
        "- Pelanggan bisa chat langsung tanpa harus datang\n"
        "- Tambah kredibilitas & kepercayaan usaha\n\n"
        "Saya bisa buatkan website + domain sendiri + hosting 1 tahun, "
        "mulai dari Rp 500rb (satu kali bayar, free maintenance 3 bulan).\n\n"
        "Contoh: warung, kafe, laundry, bengkel, salon, toko, dll. "
        "Semua bisa saya buatkan.\n\n"
        "Kalau berkenan, saya bisa kirim contoh desain yang sesuai "
        "dengan bidang usaha Kakak. Gratis, no SPAM. 🙏"
    )

    print(f"\n  {D}Gunakan {{name}} untuk nama bisnis{R}")
    print(f"  {D}Tekan Enter untuk pakai template default{R}\n")
    print(f"  {Y}Template default:{R}")
    for line in DEFAULT_MSG.split("\n"):
        print(f"    {D}{line}{R}")
    print()

    msg = input(f"  {G}▸ Pesan (Enter=default): {R}").strip()
    if not msg: msg = DEFAULT_MSG

    # Preview
    sample_name = "Restoran Sederhana"
    preview = msg.replace("{name}", sample_name).replace("{nama}", sample_name)
    print(f"\n  {Y}Preview ke '{sample_name}':{R}")
    for line in preview.split("\n")[:6]:
        print(f"    {D}{line}{R}")
    print()

    delay_in = input(f"  {G}▸ Delay antar pesan (ms, default 8000): {R}").strip()
    delay_ms = delay_in if delay_in.isdigit() else "8000"

    confirm = input(f"\n  {G}▸ Kirim? (y/n): {R}").strip().lower()
    if confirm != "y": print(f"  {D}Dibatalkan.{R}"); return

    print(f"\n  {C}[*] Menjalankan Baileys sender...{R}\n")
    proc = subprocess.Popen(
        ["node", WA_SCRIPT, "send", csv_file, msg, delay_ms],
        cwd=HOME, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    try:
        for line in proc.stdout:
            print(f"  {line.rstrip()}")
    except KeyboardInterrupt:
        proc.terminate()
    proc.wait()
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

# ──────────────────────────────────────────────────────────────
#  CONTINUOUS SCRAPE + AUTO DM (Tanpa Henti)
# ──────────────────────────────────────────────────────────────

SENT_FILE = os.path.join(DATA_DIR, "wa_sent.json")
ACC_FILE = os.path.join(DATA_DIR, "wa_acc.json")  # Klien yang acc

def load_acc():
    """Load klien yang sudah acc"""
    if os.path.exists(ACC_FILE):
        try:
            with open(ACC_FILE) as f: return json.load(f)
        except: pass
    return []

def get_acc_count():
    """Hitung jumlah klien yang sudah acc"""
    return len(load_acc())

def is_max_acc_reached():
    """Cek apakah max acc (3) sudah tercapai"""
    return get_acc_count() >= 3

# Daftar lokasi GLOBAL yang akan di-scrape otomatis
LOCI = GLOBAL_LOCATIONS  # Use global locations list

# Approximate center coordinates per country for the protobuf search
COUNTRY_COORDS = {
    "Indonesia": (-6.2, 106.8, 12, "en", "id"),
    "Malaysia": (3.14, 101.69, 12, "en", "my"),
    "Philippines": (14.6, 120.98, 12, "en", "ph"),
    "Thailand": (13.75, 100.52, 12, "en", "th"),
    "Vietnam": (10.82, 106.63, 12, "en", "vn"),
    "India": (19.08, 72.88, 12, "hi", "in"),
    "Pakistan": (33.69, 73.04, 12, "en", "pk"),
    "Bangladesh": (23.68, 90.36, 12, "en", "bd"),
    "Sri Lanka": (7.87, 80.77, 12, "en", "lk"),
    "Nepal": (27.72, 85.32, 12, "en", "np"),
    "Myanmar": (19.76, 96.08, 12, "en", "mm"),
    "Cambodia": (11.56, 104.92, 12, "en", "kh"),
    "Laos": (17.97, 102.63, 12, "en", "la"),
    "China": (39.9, 116.4, 12, "zh", "cn"),
    "Japan": (35.68, 139.69, 12, "ja", "jp"),
    "South Korea": (37.57, 126.98, 12, "ko", "kr"),
    "Taiwan": (25.03, 121.57, 12, "zh", "tw"),
    "Hong Kong": (22.32, 114.17, 12, "en", "hk"),
    "Singapore": (1.35, 103.82, 13, "en", "sg"),
    "Brazil": (-15.78, -47.93, 12, "pt", "br"),
    "Mexico": (19.43, -99.13, 12, "es", "mx"),
    "Argentina": (-34.6, -58.38, 12, "es", "ar"),
    "Colombia": (4.71, -74.07, 12, "es", "co"),
    "Chile": (-33.45, -70.67, 12, "es", "cl"),
    "Peru": (-12.05, -77.04, 12, "es", "pe"),
    "Ecuador": (-0.18, -78.47, 12, "es", "ec"),
    "Venezuela": (10.48, -66.9, 12, "es", "ve"),
    "Dominican Republic": (18.47, -69.9, 12, "es", "do"),
    "Cuba": (23.11, -82.37, 12, "es", "cu"),
    "Nigeria": (9.08, 7.49, 12, "en", "ng"),
    "Kenya": (-1.29, 36.82, 12, "en", "ke"),
    "Ghana": (5.6, -0.19, 12, "en", "gh"),
    "South Africa": (-33.93, 18.42, 12, "en", "za"),
    "Egypt": (30.04, 31.24, 12, "ar", "eg"),
    "Morocco": (33.97, -6.85, 12, "ar", "ma"),
    "Tunisia": (36.81, 10.17, 12, "ar", "tn"),
    "Algeria": (36.75, 3.06, 12, "ar", "dz"),
    "Turkey": (39.93, 32.85, 12, "tr", "tr"),
    "Saudi Arabia": (24.71, 46.67, 12, "ar", "sa"),
    "UAE": (25.2, 55.27, 13, "en", "ae"),
    "Qatar": (25.29, 51.53, 12, "en", "qa"),
    "Kuwait": (29.38, 47.99, 12, "ar", "kw"),
    "Bahrain": (26.07, 50.55, 13, "en", "bh"),
    "Oman": (23.59, 58.55, 12, "en", "om"),
    "Jordan": (31.95, 35.93, 12, "ar", "jo"),
    "Lebanon": (33.89, 35.5, 12, "ar", "lb"),
    "Iraq": (33.31, 44.37, 12, "ar", "iq"),
    "Pakistan": (33.69, 73.04, 12, "en", "pk"),
    "Bangladesh": (23.68, 90.36, 12, "en", "bd"),
    "Russia": (55.76, 37.62, 12, "ru", "ru"),
    "Ukraine": (50.45, 30.52, 12, "uk", "ua"),
    "Poland": (52.23, 21.01, 12, "pl", "pl"),
    "Czech Republic": (50.08, 14.44, 12, "cs", "cz"),
    "Romania": (44.43, 26.1, 12, "ro", "ro"),
    "Hungary": (47.5, 19.04, 12, "hu", "hu"),
    "Germany": (52.52, 13.41, 12, "de", "de"),
    "France": (48.86, 2.35, 12, "fr", "fr"),
    "Spain": (40.42, -3.7, 12, "es", "es"),
    "Italy": (41.9, 12.5, 12, "it", "it"),
    "Portugal": (38.72, -9.14, 12, "pt", "pt"),
    "Netherlands": (52.37, 4.9, 12, "nl", "nl"),
    "Belgium": (50.85, 4.35, 12, "fr", "be"),
    "Sweden": (59.33, 18.07, 12, "sv", "se"),
    "Norway": (59.91, 10.75, 12, "no", "no"),
    "Denmark": (55.68, 12.57, 12, "da", "dk"),
    "Finland": (60.17, 24.94, 12, "fi", "fi"),
    "Greece": (37.97, 23.73, 12, "el", "gr"),
    "Austria": (48.21, 16.37, 12, "de", "at"),
    "Switzerland": (46.95, 7.45, 12, "de", "ch"),
    "Ireland": (53.35, -6.26, 12, "en", "ie"),
    "UK": (51.51, -0.13, 12, "en", "gb"),
    "USA": (38.9, -77.04, 12, "en", "us"),
    "Canada": (45.42, -75.7, 12, "en", "ca"),
    "Australia": (-33.87, 151.21, 12, "en", "au"),
    "New Zealand": (-41.29, 174.78, 12, "en", "nz"),
}

def load_sent():
    """Load nomor yang sudah dikirim"""
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE) as f: return json.load(f)
        except: pass
    return {}

def save_sent(sent):
    """Simpan nomor yang sudah dikirim"""
    with open(SENT_FILE, "w") as f: json.dump(sent, f, indent=2)

def is_sent(phone):
    """Cek apakah nomor sudah pernah dikirim"""
    sent = load_sent()
    return phone in sent

def mark_sent(phone, name):
    """Tandai nomor sudah dikirim"""
    sent = load_sent()
    sent[phone] = {"name": name, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    save_sent(sent)

def read_queue():
    """Baca wa_queue.json"""
    if not os.path.exists(QUEUE_FILE): return []
    try:
        with open(QUEUE_FILE) as f: return json.load(f)
    except: return []

def write_queue(queue):
    """Tulis wa_queue.json"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(QUEUE_FILE, "w") as f: json.dump(queue, f, indent=2)

def flow_scrape_auto_dm():
    """ONE-CLICK: Scrape 3-5 targets → DM langsung → repeat. Natural flow."""
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("SCRAPE & AUTO DM 24/7", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Flow natural (anti-ban):", Y))
    print(box_line("  1. Scrape 3-5 bisnis baru", Y))
    print(box_line("  2. DM langsung 1-1 (delay 30s)", Y))
    print(box_line("  3. Tunggu terkirim, lalu scrape lagi", Y))
    print(box_line("  4. Auto-reply kalau klien balas", Y))
    print(box_line("  5. Stop saat 3 klien acc", Y))
    print(box_line(""))
    print(box_line("Kalau WA belum ready, scrape aja dulu", Y))
    print(box_line("DM otomatis jalan kalau WA udah connect", Y))
    print(box_line(""))
    print(box_line("Tekan Ctrl+C untuk berhenti", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    # Cek status WA
    wa_ok = False
    wa_restricted = False
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f: st = json.load(f)
            if st.get("connected") and not st.get("error"): wa_ok = True
            elif st.get("error") == "logged_out": wa_restricted = True
        except: pass

    # Tampilkan stats
    sent = load_sent()
    acc = load_acc()
    today_sent = sum(1 for v in sent.values()
                    if time.time() - time.mktime(time.strptime(v["ts"][:19], "%Y-%m-%dT%H:%M:%S")) < 86400)
    print(f"  {C}📊 Stats:{R}")
    print(f"     Nomor sudah DM: {len(sent)} (hari ini: {today_sent})")
    print(f"     Klien acc: {len(acc)}/3")
    print(f"     Lokasi: {len(LOCI)} kota/kategori")

    if wa_restricted:
        print(f"\n  {Y}[!] WA belum ready (restricted/logged out){R}")
        print(f"  {Y}    Mode: SCRAPE ONLY (simpan CSV){R}")
        print(f"  {Y}    DM otomatis jalan kalau WA connect{R}")
    elif wa_ok:
        print(f"\n  {G}✓ WA ready! Mode: SCRAPE + DM{R}")
    else:
        print(f"\n  {Y}[!] WA belum terhubung{R}")
        print(f"  {Y}    Mode: SCRAPE ONLY (simpan CSV){R}")
    print()

    confirm = input(f"  {G}▸ Jalankan? (y/n): {R}").strip().lower()
    if confirm != "y": print(f"  {D}Dibatalkan.{R}"); return

    # Clear queue lama dulu
    write_queue([])

    # Jalankan Baileys daemon di background (kalau WA ready)
    wa_proc = None
    daemon_ready = False
    if wa_ok:
        print(f"\n  {C}[*] Menjalankan WhatsApp daemon...{R}")
        wa_proc = subprocess.Popen(
            ["node", WA_SCRIPT, "daemon"],
            cwd=HOME,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(5)
        print(f"  {G}✓ WhatsApp daemon aktif (PID: {wa_proc.pid}){R}")
        daemon_ready = True
    else:
        print(f"\n  {D}[*] WA belum ready. Scrape only mode.{R}")
        print(f"  {D}    DM otomatis aktif kalau WA connect.{R}")

    print(f"\n  {C}[*] Mulai scrape flow...{R}")
    print(f"  {D}Setiap target: scrape → DM (kalau ready) → repeat{R}")
    print(f"  {D}Tekan Ctrl+C untuk berhenti{R}\n")

    BATCH_SIZE = 3
    total_sent = 0
    total_scraped = 0
    all_targets = []  # Simpan semua target untuk DM nanti

    try:
        cycle = 0
        loc_idx = 0

        while True:
            # Cek max acc
            if is_max_acc_reached():
                acc_count = get_acc_count()
                print(f"\n  {G}[🎯] {acc_count} klien ACC! DM berhenti, auto-reply tetap aktif.{R}")
                print(f"  {D}Ketik 'r' untuk reset acc, Enter untuk cek status, Ctrl+C keluar.{R}")
                user_in = input(f"  {G}▸ {R}").strip().lower()
                if user_in == "r":
                    with open(ACC_FILE, "w") as f: json.dump([], f)
                    print(f"  {G}✓ Acc count direset. Lanjut scrape...{R}")
                continue

            # Cek rate limit (kalau DM aktif)
            if daemon_ready:
                recent = sum(1 for v in load_sent().values()
                            if time.time() - time.mktime(time.strptime(v["ts"][:19], "%Y-%m-%dT%H:%M:%S")) < 3600)
                if recent >= 65:
                    _play_sound("error")
                    print(f"\n  {Y}[!] Rate limit: {recent}/70 per jam. Pause 10 menit...{R}")
                    time.sleep(600)
                    continue

                # Cek WA masih connected
                try:
                    with open(STATUS_FILE) as f: st = json.load(f)
                    if st.get("error") == "logged_out":
                        print(f"\n  {Y}[!] Session logged out! Switch ke scrape-only mode...{R}")
                        daemon_ready = False
                        if wa_proc:
                            wa_proc.terminate()
                            wa_proc = None
                        time.sleep(5)
                        continue
                except: pass
            else:
                # Cek apakah WA udah connect (auto-switch ke DM mode)
                try:
                    with open(STATUS_FILE) as f: st = json.load(f)
                    if st.get("connected") and not st.get("error"):
                        print(f"\n  {G}[✓] WA udah connect! Switch ke DM mode...{R}")
                        wa_proc = subprocess.Popen(
                            ["node", WA_SCRIPT, "daemon"],
                            cwd=HOME,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        time.sleep(5)
                        daemon_ready = True
                        print(f"  {G}✓ WhatsApp daemon aktif! Mulai kirim DM...{R}")

                        # Kirim target yang sudah di-scrape sebelumnya
                        if all_targets:
                            print(f"\n  {C}[*] Kirim {len(all_targets)} target yang sudah di-scrape...{R}")
                            write_queue(all_targets[:5])  # Kirim 5 dulu
                            all_targets = all_targets[5:]
                            time.sleep(10)
                except: pass

            cycle += 1
            query, kota = LOCI[loc_idx % len(LOCI)]
            loc_idx += 1

            print(f"\n{'─'*WIDTH}")
            mode = "SCRAPE+DM" if daemon_ready else "SCRAPE ONLY"
            print(f"  {G}🔄 Cycle #{cycle} | {query} | [{mode}] | {time.strftime('%H:%M:%S')}{R}")
            print(f"{'─'*WIDTH}")

            # Scrape batch kecil
            coords = COUNTRY_COORDS.get(kota, (-6.2, 106.8, 12, "en", "id"))
            businesses, err = scrape_grid(query, max_results=BATCH_SIZE,
                lat=coords[0], lng=coords[1], zoom=coords[2], lang=coords[3], gl=coords[4])

            if err:
                _play_sound("error")
                print(f"  {RED}[!] Scrape error: {err}{R}")
                time.sleep(10)
                continue

            if not businesses:
                print(f"  {D}[!] Tidak ada hasil{R}")
                time.sleep(5)
                continue

            # Filter: belum dikirim + punya nomor
            new_targets = []
            for b in businesses:
                ph = b["phone"].replace(" ","").replace("-","").replace("+","").replace("(","").replace(")","")
                if not ph or len(ph) < 8: continue
                # Clean: keep only digits, ensure starts with country code
                ph = "".join(c for c in ph if c.isdigit())
                if ph.startswith("0"):
                    # Local number - skip (can't determine country)
                    continue
                if not is_sent(ph) and len(ph) >= 10:
                    b["phone_clean"] = ph
                    new_targets.append(b)

            if not new_targets:
                print(f"  {D}[!] Semua sudah dikirim, skip{R}")
                time.sleep(3)
                continue

            total_scraped += len(new_targets)
            _play_sound("ding")
            print(f"  {G}[✓] {len(new_targets)} target baru ditemukan (total: {total_scraped}){R}")

            # Simpan CSV
            ts = time.strftime("%Y%m%d_%H%M%S")
            fn = f"{query.replace(' ','_')}_{ts}.csv"
            save_csv(new_targets, fn)

            # Export PDF ke storage
            pdf_fn = f"ASTRAL_{query.replace(' ','_')}_{ts}.pdf"
            pdf_path = _export_pdf(new_targets, pdf_fn)
            if pdf_path:
                _play_sound("tick")
                print(f"  {G}[✓] PDF: {pdf_path}{R}")

            if daemon_ready:
                # DM langsung
                queue = []
                for b in new_targets:
                    lang = b.get("lang", "en")
                    queue.append({
                        "name": b["name"],
                        "phone": b["phone_clean"],
                        "address": b.get("address", ""),
                        "lang": lang,
                    })
                write_queue(queue)
                print(f"  {C}[*] Queue: {len(queue)} target. Menunggu DM...{R}")

                # Tunggu queue kosong
                max_wait = 300
                waited = 0
                while waited < max_wait:
                    time.sleep(15)
                    waited += 15
                    try:
                        with open(QUEUE_FILE) as f: q = json.load(f)
                    except: q = []

                    if len(q) == 0:
                        _play_sound("success")
                        print(f"  {G}✓ Semua DM terkirim!{R}")
                        total_sent += len(new_targets)
                        break
                    else:
                        print(f"  {D}  ... {len(q)} masih di queue ({waited}s){R}")

                if waited >= max_wait:
                    print(f"  {Y}[!] Timeout queue, lanjut...{R}")

                # Delay antar batch
                delay = random.randint(10, 20)
                print(f"  {D}⏳ Delay {delay}s sebelum batch berikutnya...{R}")
                time.sleep(delay)
            else:
                # Scrape only: simpan targets untuk DM nanti
                for b in new_targets:
                    lang = b.get("lang", "en")
                    all_targets.append({
                        "name": b["name"],
                        "phone": b["phone_clean"],
                        "address": b.get("address", ""),
                        "lang": lang,
                    })
                print(f"  {D}📦 Disimpan untuk DM nanti (total antrian: {len(all_targets)}){R}")
                time.sleep(3)

    except KeyboardInterrupt:
        print(f"\n  {D}Dihentikan.{R}")
    finally:
        write_queue([])
        if wa_proc:
            wa_proc.terminate()
            print(f"  {D}WhatsApp daemon dihentikan.{R}")
        print(f"\n  {C}📊 Total: {total_scraped} di-scrape, {total_sent} DM terkirim{R}")
        if all_targets:
            print(f"  {Y}📦 {len(all_targets)} target tersimpan untuk DM berikutnya{R}")
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

# ──────────────────────────────────────────────────────────────
#  SCRAPE FLOW
# ──────────────────────────────────────────────────────────────

def flow_scrape():
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("SCRAPE GOOGLE MAPS", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Masukkan keyword pencarian", D))
    print(box_line("contoh: restoran di Bandung", D))
    print(box_line("contoh: toko online shop Jakarta", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    query = input(f"  {G}▸ Keyword: {R}").strip()
    if not query: print(f"  {RED}[!] Kosong.{R}"); time.sleep(1); return

    mx = input(f"  {G}▸ Maks hasil (default 20): {R}").strip()
    max_r = int(mx) if mx.isdigit() else 20

    businesses, err = scrape_google_maps(query, max_r, lat=-6.2, lng=106.8, zoom=12, lang="en", gl="id")
    if err: print(f"\n  {RED}[!] {err}{R}"); input(f"\n  {D}Enter...{R}"); return
    if not businesses:
        print(f"\n  {Y}[!] Tidak ada hasil untuk '{query}'.{R}")
        print(f"  {D}Coba keyword lain atau lebih spesifik.{R}")
        input(f"\n  {D}Enter...{R}"); return

    display_results(businesses)

    ts = time.strftime("%Y%m%d_%H%M%S")
    fn = f"{query.replace(' ','_')}_{ts}.csv"
    fp = save_csv(businesses, fn)
    print(f"  {G}[✓] Tersimpan: {fp}{R}")

    # Export PDF ke storage
    pdf_fn = f"ASTRAL_{query.replace(' ','_')}_{ts}.pdf"
    pdf_path = _export_pdf(businesses, pdf_fn)
    if pdf_path:
        print(f"  {G}[✓] PDF: {pdf_path}{R}")

    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("[1] Kirim WhatsApp DM", f"{B}{G}"))
    print(box_line("[2] Kembali ke menu", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    ch = input(f"  {G}▸ Pilih: {R}").strip()
    if ch == "1": flow_send()
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

# ──────────────────────────────────────────────────────────────
#  API SETTINGS
# ──────────────────────────────────────────────────────────────

def flow_api_settings():
    """Kelola API key SerpApi: tambah, hapus, list, test"""
    global SERP_API_KEYS, SERP_API_KEY

    while True:
        clear(); rainbow_banner()
        print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
        print(box_line("SETTING API", f"{B}{G}"))
        print(box_line(""))
        print(box_line("SerpApi Multi-Key Fallback", C))
        print(box_line("Kalau key 1 limit, otomatis pakai key 2, dst", D))
        print(box_line(""))

        # Tampilkan semua keys
        keys = _load_api_keys()
        if keys:
            print(box_line(f"Total key: {len(keys)}", C))
            for i, k in enumerate(keys):
                masked = k[:8] + "..." + k[-6:] if len(k) > 20 else k
                active = " ✓ active" if k == SERP_API_KEY else ""
                print(box_line(f"  [{i+1}] {masked}{active}", Y if k == SERP_API_KEY else D))
        else:
            print(box_line(f"  {Y}[!] Belum ada API key{R}"))
        print(box_line(""))

        # Status usage
        print(box_line(f"Quota per key: 100 pencarian/bulan", D))
        print(box_line(f"Auto fallback: key limit → pakai key berikutnya", D))
        print(box_line(""))
        print(box_line("[1] Tambah API key baru", Y))
        print(box_line("[2] Hapus API key", Y))
        print(box_line("[3] Test semua key", Y))
        print(box_line("[4] Set active key", Y))
        print(box_line("[0] Kembali", D))
        print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

        ch = input(f"  {G}▸ Pilih: {R}").strip()

        if ch == "1":
            _add_api_key()
        elif ch == "2":
            _remove_api_key()
        elif ch == "3":
            _test_api_keys()
        elif ch == "4":
            _set_active_key()
        elif ch == "0":
            return

def _add_api_key():
    """Tambah API key baru"""
    global SERP_API_KEYS, SERP_API_KEY
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("TAMBAH API KEY", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Dapatkan key gratis di:", Y))
    print(box_line("  https://serpapi.com/manage-api-key", D))
    print(box_line(""))
    print(box_line("Free tier: 100 pencarian/bulan", D))
    print(box_line("Tip: daftar banyak akun = banyak key gratis!", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    key = input(f"  {G}▸ Masukkan API key: {R}").strip()
    if not key:
        print(f"  {RED}[!] Kosong.{R}")
        time.sleep(1); return

    keys = _load_api_keys()
    if key in keys:
        print(f"  {Y}[!] Key sudah ada.{R}")
        time.sleep(1); return

    keys.append(key)
    _save_api_keys(keys)
    SERP_API_KEYS = keys
    SERP_API_KEY = keys[0]
    print(f"  {G}[✓] Key ditambahkan! Total: {len(keys)} key{R}")
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

def _remove_api_key():
    """Hapus API key"""
    global SERP_API_KEYS, SERP_API_KEY
    keys = _load_api_keys()
    if not keys:
        print(f"  {Y}[!] Tidak ada key.{R}")
        time.sleep(1); return

    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("HAPUS API KEY", f"{B}{G}"))
    print(box_line(""))

    for i, k in enumerate(keys):
        masked = k[:8] + "..." + k[-6:] if len(k) > 20 else k
        print(box_line(f"  [{i+1}] {masked}", Y))
    print(box_line(""))
    print(box_line("[0] Batal", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    ch = input(f"  {G}▸ Nomor key: {R}").strip()
    if ch == "0" or not ch:
        return

    try:
        idx = int(ch) - 1
        if 0 <= idx < len(keys):
            removed = keys.pop(idx)
            _save_api_keys(keys)
            SERP_API_KEYS = keys
            SERP_API_KEY = keys[0] if keys else None
            print(f"  {G}[✓] Key dihapus! Sisa: {len(keys)} key{R}")
        else:
            print(f"  {RED}[!] Nomor invalid.{R}")
    except ValueError:
        print(f"  {RED}[!] Input invalid.{R}")
    time.sleep(1)

def _test_api_keys():
    """Test semua key SerpApi"""
    keys = _load_api_keys()
    if not keys:
        print(f"  {Y}[!] Tidak ada key.{R}")
        time.sleep(1); return

    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("TEST API KEY", f"{B}{G}"))
    print(box_line(""))

    for i, key in enumerate(keys):
        masked = key[:8] + "..." + key[-6:] if len(key) > 20 else key
        print(box_line(f"  Testing [{i+1}] {masked}...", C), end="", flush=True)

        try:
            resp = requests.get("https://serpapi.com/account", params={"api_key": key}, timeout=10)
            data = resp.json()
            plan = data.get("plan", "unknown")
            quota = data.get("total_searches_left", "?")
            used = data.get("total_searches", "?")
            print(f"\r  {G}[✓] [{i+1}] Plan: {plan} | Sisa: {quota} | Terpakai: {used}     {R}")
        except Exception as e:
            print(f"\r  {RED}[✗] [{i+1}] Error: {e}     {R}")

    print()
    input(f"  {D}Tekan Enter untuk kembali...{R}")

def _set_active_key():
    """Set key aktif"""
    global SERP_API_KEY
    keys = _load_api_keys()
    if not keys:
        print(f"  {Y}[!] Tidak ada key.{R}")
        time.sleep(1); return

    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("SET ACTIVE KEY", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Key aktif = key pertama yang dipakai", D))
    print(box_line("Kalau limit, otomatis fallback ke key berikutnya", D))
    print(box_line(""))

    for i, k in enumerate(keys):
        masked = k[:8] + "..." + k[-6:] if len(k) > 20 else k
        active = " ← active" if k == SERP_API_KEY else ""
        print(box_line(f"  [{i+1}] {masked}{active}", Y if k == SERP_API_KEY else D))
    print(box_line(""))
    print(box_line("[0] Batal", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    ch = input(f"  {G}▸ Nomor key: {R}").strip()
    if ch == "0" or not ch:
        return

    try:
        idx = int(ch) - 1
        if 0 <= idx < len(keys):
            SERP_API_KEY = keys[idx]
            print(f"  {G}[✓] Active key diubah!{R}")
        else:
            print(f"  {RED}[!] Nomor invalid.{R}")
    except ValueError:
        print(f"  {RED}[!] Input invalid.{R}")
    time.sleep(1)

# ──────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # License check
    if not _show_license_screen():
        sys.exit(0)

    # First time setup (API key)
    if not _first_time_setup():
        sys.exit(1)

    clear(); print(); loading(); time.sleep(0.3)

    # Typewriter banner animation
    _banner_typewriter()

    flows = {
        0: flow_scrape_auto_dm,
        1: flow_settings,
        2: flow_api_settings,
    }

    while True:
        choice = menu_select()
        if choice == -1 or choice == 3:
            clear(); rainbow_banner(); print(f"\n  {D}Bye!{R}\n"); sys.exit(0)
        if choice in flows:
            flows[choice]()
            clear(); rainbow_banner()  # Clear setelah kembali dari submenu

if __name__ == "__main__":
    main()
