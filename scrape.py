#!/usr/bin/env python3
import sys, os, time, itertools, random, json, re, csv, subprocess, termios, tty

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
WIDTH = 47

MENU = [
    ("Scrape & Auto DM",         "Scrape semua kota + auto DM 24/7 otomatis"),
    ("Setting WhatsApp",         "Login/logout, ganti nomor, pairing"),
    ("Exit",                     "Keluar dari program"),
]

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

def flash_banner(color):
    print()
    for l in BANNER: print(f"  {color}{l}{R}")
    print(f"\n  {color}{SUBTITLE}{R}")

def loading():
    spinner = random.choice([["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"],["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"],["◐","◓","◑","◒"],["◰","◳","◲","◱"]])
    phases = ["Memuat modul","Init ASTRAL","Connect server","Load resources","Prepare engine","Finalisasi"]
    bar_len, phase_time = 30, 100/len(phases)
    for i, frame in enumerate(itertools.cycle(spinner)):
        pct = min(i*2, 100)
        phase = phases[min(int(pct/phase_time), len(phases)-1)]
        filled = int(bar_len*pct/100)
        color = RAINBOW[i%len(RAINBOW)]
        bar = f"{color}{'█'*filled}{D}{'░'*(bar_len-filled)}{R}"
        sys.stdout.write(f"\r  {B}{color}{frame}{R} {phase}... {bar} {B}{color}{pct}%{R}")
        sys.stdout.flush()
        if pct >= 100: break
        time.sleep(0.04)
    sys.stdout.write("\r"+" "*80+"\r"); sys.stdout.flush()
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

def print_menu(sel):
    print()
    print(f"  {B}{M}+{'='*WIDTH}+{R}")
    for i, (name, desc) in enumerate(MENU):
        c = f"{B}{G}" if i==sel else D
        tag = "[●]" if i==sel else "[○]"
        print(box_line(f"{tag} {name}", c))
        print(box_line(f"    {desc}", c))
        if i < len(MENU)-1: print(box_line(""))
    print(box_line(""))
    print(box_line("↑/↓ pilih  Enter OK  q keluar", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}")

def menu_select():
    sel = 0
    while True:
        clear(); rainbow_banner(); print_menu(sel)
        key = get_key()
        if key=="UP": sel = (sel-1)%len(MENU)
        elif key=="DOWN": sel = (sel+1)%len(MENU)
        elif key=="ENTER": return sel
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

# Global location queries (per region)
GLOBAL_LOCATIONS = [
    # Indonesia
    ("toko", "Indonesia"), ("restoran", "Indonesia"), ("cafe", "Indonesia"),
    ("laundry", "Indonesia"), ("bengkel", "Indonesia"), ("salon", "Indonesia"),
    # Malaysia
    ("kedai", "Malaysia"), ("restoran", "Malaysia"), ("kedai kopi", "Malaysia"),
    # Philippines
    ("tindahan", "Philippines"), ("restaurant", "Philippines"), ("carinderia", "Philippines"),
    # Thailand
    ("ร้าน", "Thailand"), ("ร้านอาหาร", "Thailand"), ("คาเฟ่", "Thailand"),
    # Vietnam
    ("cửa hàng", "Vietnam"), ("quán ăn", "Vietnam"), ("café", "Vietnam"),
    # India
    ("दुकान", "India"), ("restaurant", "India"), ("कैफे", "India"),
    # Pakistan
    ("دکان", "Pakistan"), ("restaurant", "Pakistan"),
    # Bangladesh
    ("দোকান", "Bangladesh"), ("restaurant", "Bangladesh"),
    # Sri Lanka
    ("shop", "Sri Lanka"), ("restaurant", "Sri Lanka"),
    # Nepal
    ("पसल", "Nepal"), ("restaurant", "Nepal"),
    # Myanmar
    ("ဆိုင်", "Myanmar"), ("ресторан", "Myanmar"),
    # Cambodia
    ("ហាង", "Cambodia"), ("ភោជនីយដ្ឋាន", "Cambodia"),
    # Laos
    ("ຮ້ານ", "Laos"),
    # China
    ("商店", "China"), ("餐厅", "China"), ("咖啡", "China"),
    # Japan
    ("店", "Japan"), ("レストラン", "Japan"), ("カフェ", "Japan"),
    # South Korea
    ("가게", "South Korea"), ("식당", "South Korea"), ("카페", "South Korea"),
    # Taiwan
    ("商店", "Taiwan"), ("餐廳", "Taiwan"), ("咖啡", "Taiwan"),
    # Hong Kong
    ("商店", "Hong Kong"), ("餐廳", "Hong Kong"),
    # Singapore
    ("shop", "Singapore"), ("restaurant", "Singapore"), ("cafe", "Singapore"),
    # Australia
    ("shop", "Australia"), ("restaurant", "Australia"), ("cafe", "Australia"),
    ("salon", "Australia"), ("gym", "Australia"), ("bakery", "Australia"),
    # New Zealand
    ("shop", "New Zealand"), ("restaurant", "New Zealand"), ("cafe", "New Zealand"),
    # USA
    ("shop", "USA"), ("restaurant", "USA"), ("cafe", "USA"), ("bakery", "USA"),
    ("salon", "USA"), ("gym", "USA"), ("plumber", "USA"), ("electrician", "USA"),
    ("cleaning", "USA"), ("landscaping", "USA"), ("painting", "USA"),
    ("pizza", "USA"), ("taco", "USA"), ("sushi", "USA"), ("burger", "USA"),
    ("florist", "USA"), ("boutique", "USA"), ("pet store", "USA"),
    # Canada
    ("shop", "Canada"), ("restaurant", "Canada"), ("cafe", "Canada"),
    # UK
    ("shop", "UK"), ("restaurant", "UK"), ("cafe", "UK"), ("pub", "UK"),
    ("salon", "UK"), ("bakery", "UK"),
    # Europe
    ("shop", "Germany"), ("restaurant", "Germany"), ("cafe", "Germany"),
    ("shop", "France"), ("restaurant", "France"), ("cafe", "France"),
    ("shop", "Spain"), ("restaurant", "Spain"), ("cafe", "Spain"),
    ("shop", "Italy"), ("restaurant", "Italy"), ("cafe", "Italy"),
    ("shop", "Portugal"), ("restaurant", "Portugal"), ("cafe", "Portugal"),
    ("shop", "Netherlands"), ("restaurant", "Netherlands"), ("cafe", "Netherlands"),
    ("shop", "Belgium"), ("restaurant", "Belgium"), ("cafe", "Belgium"),
    ("shop", "Poland"), ("restaurant", "Poland"), ("cafe", "Poland"),
    ("shop", "Czech Republic"), ("restaurant", "Czech Republic"),
    ("shop", "Austria"), ("restaurant", "Austria"), ("cafe", "Austria"),
    ("shop", "Switzerland"), ("restaurant", "Switzerland"),
    ("shop", "Sweden"), ("restaurant", "Sweden"), ("cafe", "Sweden"),
    ("shop", "Norway"), ("restaurant", "Norway"), ("cafe", "Norway"),
    ("shop", "Denmark"), ("restaurant", "Denmark"), ("cafe", "Denmark"),
    ("shop", "Finland"), ("restaurant", "Finland"), ("cafe", "Finland"),
    # Middle East
    ("محل", "UAE"), ("مطعم", "UAE"), ("كافيه", "UAE"),
    ("محل", "Saudi Arabia"), ("مطعم", "Saudi Arabia"),
    ("محل", "Qatar"), ("مطعم", "Qatar"),
    ("محل", "Kuwait"), ("مطعم", "Kuwait"),
    ("محل", "Bahrain"), ("مطعم", "Bahrain"),
    ("محل", "Oman"), ("مطعم", "Oman"),
    # Africa
    ("shop", "South Africa"), ("restaurant", "South Africa"), ("cafe", "South Africa"),
    ("shop", "Nigeria"), ("restaurant", "Nigeria"), ("cafe", "Nigeria"),
    ("shop", "Kenya"), ("restaurant", "Kenya"), ("cafe", "Kenya"),
    ("shop", "Egypt"), ("restaurant", "Egypt"), ("cafe", "Egypt"),
    ("shop", "Morocco"), ("restaurant", "Morocco"), ("cafe", "Morocco"),
    ("shop", "Ghana"), ("restaurant", "Ghana"),
    ("shop", "Tanzania"), ("restaurant", "Tanzania"),
    ("shop", "Ethiopia"), ("restaurant", "Ethiopia"),
    # Latin America
    ("tienda", "Mexico"), ("restaurante", "Mexico"), ("cafe", "Mexico"),
    ("tienda", "Brazil"), ("restaurante", "Brazil"), ("cafe", "Brazil"),
    ("tienda", "Argentina"), ("restaurante", "Argentina"), ("cafe", "Argentina"),
    ("tienda", "Colombia"), ("restaurante", "Colombia"), ("cafe", "Colombia"),
    ("tienda", "Chile"), ("restaurante", "Chile"), ("cafe", "Chile"),
    ("tienda", "Peru"), ("restaurante", "Peru"), ("cafe", "Peru"),
    ("tienda", "Ecuador"), ("restaurante", "Ecuador"),
    ("tienda", "Venezuela"), ("restaurante", "Venezuela"),
    ("tienda", "Panama"), ("restaurante", "Panama"),
    ("tienda", "Costa Rica"), ("restaurante", "Costa Rica"),
    ("tienda", "Guatemala"), ("restaurante", "Guatemala"),
    ("tienda", "Honduras"), ("restaurante", "Honduras"),
    ("tienda", "El Salvador"), ("restaurante", "El Salvador"),
    ("tienda", "Nicaragua"), ("restaurante", "Nicaragua"),
    ("tienda", "Dominican Republic"), ("restaurante", "Dominican Republic"),
    ("tienda", "Cuba"), ("restaurante", "Cuba"),
    # Turkey
    ("dukkan", "Turkey"), ("restoran", "Turkey"), ("kafe", "Turkey"),
    # Russia
    ("магазин", "Russia"), ("ресторан", "Russia"), ("кафе", "Russia"),
    # Ukraine
    ("магазин", "Ukraine"), ("ресторан", "Ukraine"), ("кафе", "Ukraine"),
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

def scrape_google_maps(query, max_results=20):
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return [], "pip install requests beautifulsoup4 dulu"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    }

    businesses = []
    seen_names = set()
    skipped_count = {"no_phone": 0, "has_website": 0, "not_umkm": 0, "duplicate": 0}

    def _add(name, phone="", address="", rating="", reviews="", website="", category="", source="", snippet=""):
        nonlocal skipped_count
        name = name.strip()
        if not name or len(name) < 3: return
        key = name.lower()
        if key in seen_names:
            skipped_count["duplicate"] += 1; return
        
        # Check if it's a platform domain in name
        for dom in PLATFORM_DOMAINS:
            if dom in key:
                return

        # FILTER: Skip jika sudah ada website
        has_web = _check_has_website(website, snippet)
        if not has_web:
            for ext in [".com",".co",".org",".net",".io",".shop",".store"]:
                if ext in snippet.lower() and not any(p in snippet.lower() for p in PLATFORM_DOMAINS):
                    has_web = True; break
        if has_web:
            skipped_count["has_website"] += 1; return

        # FILTER: Global UMKM target
        is_target, lang = _is_global_target(name, address, snippet)
        if not is_target:
            skipped_count["not_umkm"] += 1; return

        seen_names.add(key)
        businesses.append({
            "name": name, "phone": phone.strip(), "address": address.strip(),
            "rating": str(rating), "reviews": str(reviews),
            "website": website.strip(), "category": category.strip(),
            "lang": lang,
        })

    # ── Source 1: DuckDuckGo (try, handle 403) ──
    print(f"  {C}[1/4] DuckDuckGo...{R}")
    try:
        ddg_queries = [
            f"{query} nomor telepon",
            f"{query} kontak wa alamat",
            f"{query} terdepat buka",
            f"UMKM {query} telepon",
        ]
        ddg_ok = False
        for qq in ddg_queries:
            try:
                resp = requests.post("https://html.duckduckgo.com/html/",
                                     data={"q": qq}, headers=headers, timeout=12)
                if resp.status_code == 403:
                    print(f"    {D}→ DDG block, skip...{R}")
                    break
                ddg_ok = True
                soup = BeautifulSoup(resp.text, "html.parser")
                for r in soup.find_all("div", class_="result"):
                    title_el = r.find("a", class_="result__a")
                    snippet_el = r.find("a", class_="result__snippet")
                    if not title_el: continue
                    title = title_el.get_text(strip=True)
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                    url = title_el.get("href", "")
                    phones = re.findall(r'(?:\+62|62|0)\d[\d\s\-]{7,15}', snippet)
                    phone = phones[0].strip() if phones else ""
                    name = re.sub(r'[^a-zA-Z0-9\s\-\(\)&]', '', title).strip()
                    if name and len(name) > 3:
                        _add(name, phone=phone, address=snippet[:120], website=url,
                             source="duckduckgo", snippet=snippet)
                time.sleep(1)  # Delay antar query
            except Exception as e:
                continue
        print(f"    {D}→ {len(businesses)} hasil{R}")
    except Exception as e:
        print(f"    {RED}→ Error: {e}{R}")

    # ── Source 2: Google Search ──
    print(f"  {C}[2/4] Google search...{R}")
    try:
        for qq in [f"{query} telepon WhatsApp", f"{query} alamat kontak"]:
            resp = requests.get(f"https://www.google.com/search?q={qq.replace(' ','+')}&hl=id&gl=id",
                               headers=headers, timeout=12)
            # Extract from search result blocks
            blocks = re.findall(r'<div[^>]*>(.*?)</div>', resp.text, re.DOTALL)
            for block in blocks:
                phones = re.findall(r'(?:\+62|62|0)\d[\d\s\-]{7,15}', block)
                if phones:
                    # Get nearby text as name
                    text = re.sub(r'<[^>]+>', ' ', block).strip()
                    words = [w for w in text.split() if len(w) > 2 and not w.startswith(('http','www'))]
                    if words:
                        name = ' '.join(words[:5])
                        _add(name, phone=phones[0].strip(), source="google")
            # Extract from aria-labels
            labels = re.findall(r'aria-label="([^"]{5,80})"', resp.text)
            for lb in labels:
                if not any(s in lb.lower() for s in SKIP_WORDS):
                    _add(lb.strip(), source="google_aria")
        print(f"    {D}→ {len(businesses)} hasil{R}")
    except Exception as e:
        print(f"    {RED}→ Error: {e}{R}")

    # ── Source 3: Google Maps (try embedded data) ──
    print(f"  {C}[3/4] Google Maps embedded...{R}")
    try:
        resp = requests.get(f"https://www.google.com/maps/search/{query.replace(' ','+')}/@-6.9,107.6,13z?hl=id",
                           headers=headers, timeout=15)
        # Method: AF_initDataCallback
        for m in re.finditer(r"AF_initDataCallback\(\{key:\s*'ds:1'.*?data:(.*?)\}\);", resp.text, re.DOTALL):
            try:
                data = json.loads(m.group(1))
                for b in _parse_ds1(data):
                    _add(b["name"], phone=b.get("phone",""), address=b.get("address",""),
                         rating=b.get("rating",""), reviews=b.get("reviews",""),
                         website=b.get("website",""), category=b.get("category",""),
                         source="maps_json")
            except: continue

        # Method: aria-labels
        labels = re.findall(r'aria-label="([^"]{5,80})"', resp.text)
        phones = re.findall(r'(?:\+62|62|0)\d[\d\s\-]{7,15}', resp.text)
        pi = 0
        for lb in labels:
            if any(s in lb.lower() for s in SKIP_WORDS): continue
            ph = phones[pi] if pi < len(phones) else ""
            pi += 1
            _add(lb.strip(), phone=ph.strip() if ph else "", source="maps_aria")
        print(f"    {D}→ {len(businesses)} hasil{R}")
    except Exception as e:
        print(f"    {RED}→ Error: {e}{R}")

    # ── Source 4: Business directories ──
    print(f"  {C}[4/4] Business directories...{R}")
    try:
        for dir_url in [
            f"https://www.google.com/search?q={query.replace(' ','+')}&hl=id",
        ]:
            resp = requests.get(dir_url, headers=headers, timeout=12)
            # Extract phone patterns from full page
            all_phones = re.findall(r'(?:\+62|62|0)\d[\d\s\-\(\)]{8,20}', resp.text)
            all_phones = list(set([p.strip() for p in all_phones if len(re.sub(r'\D','',p)) >= 10]))

            # Extract business-like titles
            titles = re.findall(r'<(?:h[1-6]|span|div)[^>]*>([^<]{5,80})</(?:h[1-6]|span|div)>', resp.text)
            for t in titles:
                clean = re.sub(r'<[^>]+>', '', t).strip()
                if clean and not any(s in clean.lower() for s in SKIP_WORDS):
                    # Try to find associated phone
                    idx = resp.text.find(clean)
                    if idx >= 0:
                        nearby = resp.text[max(0,idx-200):idx+200]
                        n_phones = re.findall(r'(?:\+62|62|0)\d[\d\s\-]{7,15}', nearby)
                        ph = n_phones[0].strip() if n_phones else ""
                        _add(clean, phone=ph, source="directory")
        print(f"    {D}→ {len(businesses)} hasil{R}")
    except Exception as e:
        print(f"    {RED}→ Error: {e}{R}")

    # ── Deduplicate & filter ──
    final = []
    for b in businesses:
        b.pop("source", None)
        final.append(b)

    print(f"\n  {G}✓ Total: {len(final)} UMKM target{R}")
    print(f"    {Y}⊘ tanpa website{R}")
    if skipped_count["has_website"]:
        print(f"    {D}  skip sudah ada web: {skipped_count['has_website']}{R}")
    if skipped_count["no_phone"]:
        print(f"    {D}  skip tanpa no HP: {skipped_count['no_phone']}{R}")
    if skipped_count["not_umkm"]:
        print(f"    {D}  skip bukan UMKM: {skipped_count['not_umkm']}{R}")
    if skipped_count["duplicate"]:
        print(f"    {D}  skip duplikat: {skipped_count['duplicate']}{R}")
    return final[:max_results], None

def _parse_ds1(data):
    results = []
    try:
        if not isinstance(data, list) or len(data) < 4: return []
        container = data[3] if isinstance(data[3], list) else []
        items = container[0] if container and isinstance(container[0], list) else []
        for item in items:
            if not isinstance(item, list): continue
            try:
                b = {}
                if len(item)>11 and isinstance(item[11],list) and item[11]: b["name"]=str(item[11][0]).strip()
                elif len(item)>2 and isinstance(item[2],str): b["name"]=item[2].strip()
                else: continue
                b["address"] = str(item[14][0]).strip() if len(item)>14 and isinstance(item[14],list) and item[14] else ""
                b["phone"]   = str(item[17][0]).strip() if len(item)>17 and isinstance(item[17],list) and item[17] else ""
                b["rating"]  = str(item[4][7]) if len(item)>4 and isinstance(item[4],list) and len(item[4])>7 and item[4][7] else ""
                b["reviews"] = str(item[4][8]) if len(item)>4 and isinstance(item[4],list) and len(item[4])>8 and item[4][8] else ""
                b["website"] = str(item[7][2]).strip() if len(item)>7 and isinstance(item[7],list) and len(item[7])>2 and item[7][2] else ""
                b["category"]= str(item[13][0]).strip() if len(item)>13 and isinstance(item[13],list) and item[13] else ""
                if b.get("name"): results.append(b)
            except: continue
    except: pass
    return results

# ──────────────────────────────────────────────────────────────
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

def run_node(script, args=[], timeout=30):
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
    for line in DEFAULT_MSG.split("\\n"):
        print(f"    {D}{line}{R}")
    print()

    msg = input(f"  {G}▸ Pesan (Enter=default): {R}").strip()
    if not msg: msg = DEFAULT_MSG

    # Preview
    sample_name = "Restoran Sederhana"
    preview = msg.replace("{name}", sample_name).replace("{nama}", sample_name)
    print(f"\n  {Y}Preview ke '{sample_name}':{R}")
    for line in preview.split("\\n")[:6]:
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

def flow_status():
    clear(); rainbow_banner()
    s = read_status()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("STATUS WHATSAPP", f"{B}{G}"))
    print(box_line(""))

    if not s:
        print(box_line("Belum ada data status.", Y))
        print(box_line("Jalankan pairing dulu.", D))
    else:
        conn = "✓ Terhubung" if s.get("connected") else "✗ Putus"
        c = G if s.get("connected") else RED
        print(box_line(f"Koneksi: {conn}", c))

        if s.get("paired") or s.get("paired"): print(box_line("Status: Paired", G))
        elif s.get("pairing"): print(box_line(f"Pairing code: {s.get('code','???')}", Y))
        else: print(box_line("Status: Belum paired", Y))

        if s.get("sending"):
            print(box_line(f"Mengirim: {s.get('cur',0)}/{s.get('total',0)}", C))
            print(box_line(f"Target: {s.get('target','')}", D))
            print(box_line(f"OK: {s.get('ok',0)} | Gagal: {s.get('fail',0)}", D))
        elif s.get("done"):
            print(box_line(f"Selesai: {s.get('ok',0)} ok, {s.get('fail',0)} gagal", G))

        if s.get("error"): print(box_line(f"Error: {s['error']}", RED))
        if s.get("ts"): print(box_line(f"Update: {s['ts']}", D))

    print(box_line(""))
    print(f"  {B}{M}+{'='*WIDTH}+{R}")
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

def flow_daemon():
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("MODE BOT 24/7 (DAEMON)", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Bot akan jalan terus menerus", Y))
    print(box_line("otomatis kirim dari wa_queue.json", Y))
    print(box_line(""))
    print(box_line("Untuk berhenti: tekan Ctrl+C", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    confirm = input(f"  {G}▸ Jalankan daemon? (y/n): {R}").strip().lower()
    if confirm != "y": print(f"  {D}Dibatalkan.{R}"); return

    print(f"\n  {C}[*] Menjalankan Baileys daemon 24/7...{R}")
    print(f"  {D}Tekan Ctrl+C untuk berhenti{R}\n")
    try:
        subprocess.run(["node", WA_SCRIPT, "daemon"], cwd=HOME)
    except KeyboardInterrupt:
        print(f"\n  {D}Daemon dihentikan.{R}")
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

def flow_scrape_auto_dm():
    """ONE-CLICK: Scrape + Auto DM + Auto Reply - Jalan otomatis 24/7"""
    clear(); rainbow_banner()
    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("SCRAPE & AUTO DM 24/7", f"{B}{G}"))
    print(box_line(""))
    print(box_line("Semua jalan otomatis:", Y))
    print(box_line("  1. Scrape UMKM tanpa website", Y))
    print(box_line("  2. Auto DM rate-limited (70/jam)", Y))
    print(box_line("  3. Auto-reply kalau klien balas", Y))
    print(box_line("  4. Stop otomatis saat 3 klien acc", Y))
    print(box_line(""))
    print(box_line("Tekan Ctrl+C untuk berhenti", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    # Cek status WA dulu
    wa_ok = False
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f: st = json.load(f)
            if st.get("connected"): wa_ok = True
        except: pass

    if not wa_ok:
        print(f"  {RED}[!] WhatsApp belum terhubung!{R}")
        print(f"  {D}Pilih 'Setting WhatsApp' dulu untuk login.{R}")
        input(f"\n  {D}Tekan Enter untuk kembali...{R}"); return

    # Tampilkan stats
    sent = load_sent()
    acc = load_acc()
    today_sent = sum(1 for v in sent.values()
                    if time.time() - time.mktime(time.strptime(v["ts"][:19], "%Y-%m-%dT%H:%M:%S")) < 86400)
    print(f"  {C}📊 Stats:{R}")
    print(f"     Nomor sudah DM (24 jam): {today_sent}")
    print(f"     Klien acc: {len(acc)}/3")
    print(f"     Lokasi: {len(LOCI)} kota/kategori")
    print(f"     Rate limit: 70 DM/jam")
    print()

    confirm = input(f"  {G}▸ Jalankan? (y/n): {R}").strip().lower()
    if confirm != "y": print(f"  {D}Dibatalkan.{R}"); return

    # Jalankan Baileys daemon di background
    print(f"\n  {C}[*] Menjalankan WhatsApp daemon...{R}")
    wa_proc = subprocess.Popen(
        ["node", WA_SCRIPT, "daemon"],
        cwd=HOME,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    print(f"  {G}✓ WhatsApp daemon aktif (PID: {wa_proc.pid}){R}")

    print(f"\n  {C}[*] Mulai scrape & auto DM...{R}")
    print(f"  {D}Tekan Ctrl+C untuk berhenti{R}\n")

    try:
        cycle = 0
        while True:
            # Cek apakah max acc tercapai
            if is_max_acc_reached():
                acc_count = get_acc_count()
                print(f"\n  {G}[🎯] {acc_count} klien ACC! DM berhenti, auto-reply tetap aktif.{R}")
                print(f"  {D}Ketik 'r' untuk reset acc, Enter untuk cek status, Ctrl+C keluar.{R}")
                user_in = input(f"  {G}▸ {R}").strip().lower()
                if user_in == "r":
                    with open(ACC_FILE, "w") as f: json.dump([], f)
                    print(f"  {G}✓ Acc count direset. Lanjut scrape...{R}")
                continue

            cycle += 1
            print(f"\n{'='*50}")
            print(f"  {G}🔄 CYCLE #{cycle} - {time.strftime('%H:%M:%S')}{R}")
            print(f"{'='*50}")

            for qi, (query, kota) in enumerate(LOCI):
                # Cek apakah max acc tercapai di tengah cycle
                if is_max_acc_reached():
                    print(f"\n  {Y}[!] Max acc tercapai, hentikan cycle.{R}")
                    break

                # Cek rate limit
                recent = sum(1 for v in load_sent().values()
                            if time.time() - time.mktime(time.strptime(v["ts"][:19], "%Y-%m-%dT%H:%M:%S")) < 3600)
                if recent >= 70:
                    print(f"\n  {Y}[!] Rate limit 70/jam. Pause 10 menit...{R}")
                    time.sleep(600)

                print(f"\n  {C}[{qi+1}/{len(LOCI)}] {query}{R}")
                businesses, err = scrape_google_maps(query, max_results=10)
                if err:
                    print(f"  {RED}[!] Error: {err}{R}")
                    continue
                if not businesses:
                    print(f"  {D}[!] Tidak ada hasil{R}")
                    continue

                # Filter: hanya yang belum dikirim DAN punya nomor HP
                new_targets = []
                for b in businesses:
                    ph = b["phone"].replace(" ","").replace("-","")
                    if not ph or len(ph) < 8: continue
                    if ph.startswith("0"): ph = "62" + ph[1:]
                    elif not ph.startswith("62"): ph = "62" + ph
                    if not is_sent(ph):
                        b["phone_clean"] = ph
                        new_targets.append(b)

                if not new_targets:
                    print(f"  {D}[!] Semua sudah dikirim, skip{R}")
                    continue

                print(f"  {G}[✓] {len(new_targets)} target baru{R}")

                # Simpan ke CSV
                ts = time.strftime("%Y%m%d_%H%M%S")
                fn = f"{query.replace(' ','_')}_{ts}.csv"
                save_csv(new_targets, fn)

                # Kirim ke Baileys daemon via wa_queue.json
                queue = read_queue() if os.path.exists(QUEUE_FILE) else []
                for b in new_targets:
                    lang = b.get("lang", "en")
                    queue.append({
                        "name": b["name"],
                        "phone": b["phone_clean"],
                        "address": b.get("address", ""),
                        "lang": lang,
                    })
                write_queue(queue)
                print(f"  {G}[✓] Queue: {len(queue)} target{R}")

                # Delay antar kota
                time.sleep(random.randint(3, 5))

            print(f"\n  {C}[*] Cycle #{cycle} selesai. Lanjut...{R}")
            time.sleep(10)

    except KeyboardInterrupt:
        print(f"\n  {D}Dihentikan.{R}")
    finally:
        if wa_proc:
            wa_proc.terminate()
            print(f"  {D}WhatsApp daemon dihentikan.{R}")
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

    businesses, err = scrape_google_maps(query, max_r)
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

    print(f"\n  {B}{M}+{'='*WIDTH}+{R}")
    print(box_line("[1] Kirim WhatsApp DM", f"{B}{G}"))
    print(box_line("[2] Kembali ke menu", D))
    print(f"  {B}{M}+{'='*WIDTH}+{R}\n")

    ch = input(f"  {G}▸ Pilih: {R}").strip()
    if ch == "1": flow_send()
    input(f"\n  {D}Tekan Enter untuk kembali...{R}")

# ──────────────────────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────────────────────

def main():
    clear(); print(); loading(); time.sleep(0.3)
    for _ in range(3):
        for color in FLASH:
            clear(); flash_banner(color); time.sleep(0.15)

    os.makedirs(DATA_DIR, exist_ok=True)

    flows = {
        0: flow_scrape_auto_dm,
        1: flow_settings,
    }

    while True:
        choice = menu_select()
        if choice == -1 or choice == 2:
            clear(); rainbow_banner(); print(f"\n  {D}Bye!{R}\n"); sys.exit(0)
        if choice in flows:
            flows[choice]()

if __name__ == "__main__":
    main()
