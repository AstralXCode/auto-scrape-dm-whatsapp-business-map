#!/usr/bin/env node
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, makeCacheableSignalKeyStore, delay, Browsers, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const pino = require('pino');
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const path = require('path');
const csv = require('csvtojson');

const HOME = process.env.HOME || '/data/data/com.termux/files/home';
const AUTH_DIR = path.join(HOME, '.astral_auth');
const DATA_DIR = path.join(HOME, 'astral_data');
const STATUS_FILE = path.join(DATA_DIR, 'wa_status.json');
const QUEUE_FILE = path.join(DATA_DIR, 'wa_queue.json');
const SENT_FILE = path.join(DATA_DIR, 'wa_sent.json');
const ACC_FILE = path.join(DATA_DIR, 'wa_acc.json');
const logger = pino({ level: 'silent' });
const CHAT_FILE = path.join(DATA_DIR, 'wa_chats.json');
const MY_PHONE = '6283140461222';
const MAX_ACC = 3;

const RATE_LIMIT = 70;
const RATE_WINDOW = 60 * 60 * 1000;

const DM_TEMPLATES = {
    id: "Halo {name}, kami dari ASTRAL ingin menawarkan kerja sama pemasaran digital. GRATIS untuk UMKM! Mau info lebih lanjut?",
    en: "Hello {name}, we're from ASTRAL offering FREE digital marketing for small businesses. Interested?",
    es: "Hola {name}, somos de ASTRAL y ofrecemos marketing digital GRATIS para negocios pequeños. ¿Interesado?",
    pt: "Olá {name}, somos da ASTRAL e oferecemos marketing digital GRATUITO para pequenos negócios. Interessado?",
    fr: "Bonjour {name}, nous sommes d'ASTRAL et offrons un marketing digital GRATUIT pour petites entreprises. Intéressé?",
    de: "Hallo {name}, wir sind von ASTRAL und bieten KOSTENLOSES digitales Marketing für kleine Unternehmen an. Interessiert?",
    ar: "مرحبا {name}، نحن من ASTRAL ونقدم تسويقاً رقمياً مجاناً للشركات الصغيرة. مهتم؟",
    hi: "नमस्ते {name}, हम ASTRAL से हैं और छोटे व्यवसायों के लिए मुफ्त डिजिटल मार्केटिंग प्रदान करते हैं। रुचि है?",
    th: "สวัสดีครับ {name} เราจาก ASTRAL มีบริการการตลาดดิจิทัลฟรีสำหรับธุรกิจขนาดเล็ก สนใจไหม?",
    tr: "Merhaba {name}, ASTRAL'dan küçük işletmeler için ÜCRETSİZ dijital pazarlama sunuyoruz. İlginizi çekti mi?",
    ja: "こんにちは {name}、ASTRALから小規模ビジネス向けの無料デジタルマーケティングをご提供しています。興味はありますか？",
    ko: "안녕하세요 {name}, ASTRAL에서 소규모 비즈니스를 위한 무료 디지털 마케팅을 제공합니다. 관심 있으신가요?",
    zh: "你好 {name}，我们是ASTRAL，为小企业提供免费数字营销。感兴趣吗？",
};

function detectLanguage(text) {
    if (!text) return 'en';
    const sample = text.substring(0, 200);

    // Arabic
    if (/[\u0600-\u06FF]/.test(sample)) return 'ar';
    // Hindi
    if (/[\u0900-\u097F]/.test(sample)) return 'hi';
    // Thai
    if (/[\u0E00-\u0E7F]/.test(sample)) return 'th';
    // Japanese
    if (/[\u3040-\u309F\u30A0-\u30FF]/.test(sample)) return 'ja';
    // Korean
    if (/[\uAC00-\uD7AF]/.test(sample)) return 'ko';
    // Chinese
    if (/[\u4E00-\u9FFF]/.test(sample)) return 'zh';
    // Portuguese
    if (/\b(olá|oi|obrigado|obrigada|não|sim|também|muito|bom|dia|noite)\b/i.test(sample)) return 'pt';
    // Spanish
    if (/\b(hola|gracias|sí|no|también|muy|buenos|días|noches|por favor)\b/i.test(sample)) return 'es';
    // French
    if (/\b(bonjour|merci|oui|non|aussi|très|bon|jour|soir|s'il vous plaît)\b/i.test(sample)) return 'fr';
    // German
    if (/\b(hallo|danke|ja|nein|auch|sehr|guten|morgen|abend|bitte)\b/i.test(sample)) return 'de';
    // Turkish
    if (/\b(merhaba|teşekkür|evet|hayır|lütfen|günaydın|nasılsın|ben)\b/i.test(sample)) return 'tr';
    // Indonesian
    if (/\b(halo|terima kasih|ya|tidak|juga|sangat|selamat|pagi|sore|malam|kak|om|bu|pak)\b/i.test(sample)) return 'id';

    return 'en';
}

function getDMTemplate(lang) {
    return DM_TEMPLATES[lang] || DM_TEMPLATES['en'];
}

function ensureDirs() {
    [AUTH_DIR, DATA_DIR].forEach(d => fs.mkdirSync(d, { recursive: true }));
}

function writeStatus(obj) {
    fs.mkdirSync(path.dirname(STATUS_FILE), { recursive: true });
    fs.writeFileSync(STATUS_FILE, JSON.stringify({ ...obj, ts: new Date().toISOString() }, null, 2));
}

function readStatus() {
    try {
        return JSON.parse(fs.readFileSync(STATUS_FILE, 'utf8'));
    } catch {
        return { connected: false };
    }
}

function readQueue() {
    if (!fs.existsSync(QUEUE_FILE)) return [];
    try { return JSON.parse(fs.readFileSync(QUEUE_FILE, 'utf8')); } catch { return []; }
}

function writeQueue(q) { fs.writeFileSync(QUEUE_FILE, JSON.stringify(q, null, 2)); }

// ── Sent tracking: baca/tulis nomor yang sudah dikirim ──
function readSent() {
    if (!fs.existsSync(SENT_FILE)) return {};
    try { return JSON.parse(fs.readFileSync(SENT_FILE, 'utf8')); } catch { return {}; }
}

function writeSent(sent) {
    fs.writeFileSync(SENT_FILE, JSON.stringify(sent, null, 2));
}

function markSent(phone, name) {
    const sent = readSent();
    sent[phone] = { name, ts: new Date().toISOString() };
    writeSent(sent);
}

function isAlreadySent(phone) {
    const sent = readSent();
    return !!sent[phone];
}

// ── Rate limiter: cek berapa pesan terkirim dalam 1 jam terakhir ──
function getRecentSendCount() {
    const sent = readSent();
    const now = Date.now();
    let count = 0;
    for (const [phone, info] of Object.entries(sent)) {
        const sentTime = new Date(info.ts).getTime();
        if (now - sentTime < RATE_WINDOW) count++;
    }
    return count;
}

function cleanPhone(phone) {
    let p = phone.replace(/[^\d]/g, '');
    if (p.startsWith('0')) p = '62' + p.slice(1);
    if (!p.startsWith('62')) p = '62' + p;
    return p + '@s.whatsapp.net';
}

// ── ACC TRACKER ──
function readAcc() {
    if (!fs.existsSync(ACC_FILE)) return [];
    try { return JSON.parse(fs.readFileSync(ACC_FILE, 'utf8')); } catch { return []; }
}

function writeAcc(acc) {
    fs.writeFileSync(ACC_FILE, JSON.stringify(acc, null, 2));
}

function markAcc(phone, name) {
    const acc = readAcc();
    if (!acc.find(a => a.phone === phone)) {
        acc.push({ phone, name, ts: new Date().toISOString() });
        writeAcc(acc);
        console.log(`  [🎯 ACC] ${name} (${acc.length}/${MAX_ACC})`);
    }
    return acc.length;
}

function getAccCount() { return readAcc().length; }
function isMaxAccReached() { return getAccCount() >= MAX_ACC; }

// ── CHAT HISTORY ──
function readChats() {
    if (!fs.existsSync(CHAT_FILE)) return {};
    try { return JSON.parse(fs.readFileSync(CHAT_FILE, 'utf8')); } catch { return {}; }
}

function writeChats(chats) {
    fs.writeFileSync(CHAT_FILE, JSON.stringify(chats, null, 2));
}

function addChat(phone, role, text) {
    const chats = readChats();
    if (!chats[phone]) chats[phone] = [];
    chats[phone].push({ role, text, ts: new Date().toISOString() });
    if (chats[phone].length > 20) chats[phone] = chats[phone].slice(-20);
    writeChats(chats);
}

// ── MULTILINGUAL CONVERSATION FLOW ──
const FLOWS = {
    id: {  // Indonesian
        greetings: {
            patterns: [/^(halo|hai|hi|hey|pagi|siang|sore|malam|oke|ok|siap)/i],
            replies: [
                "Halo Kak! 😊 Terima kasih sudah balas. Saya dari ASTRAL, fokus bantu UMKM punya website profesional. Kak {name} lagi cari jasa buat website ya?",
                "Halo Kak! Thanks udah respon. Saya bantu UMKM bikin website biar usahanya makin gampang ditemuin pelanggan. Kebetulan usaha Kak {name} udah punya website belum?",
            ]
        },
        pricing: {
            patterns: [/harga|biaya|price|cost|berapa|bayar|tarif|mahal|murah/i],
            replies: ["Untuk harga, mulai dari Rp 500rb aja Kak (satu kali bayar, free maintenance 3 bulan). Udah termasuk domain, hosting, desain profesional. Mau saya jelaskan lebih detail?"]
        },
        features: {
            patterns: [/fitur|apa aja|bisa apa|kelebihan|untung/i],
            replies: ["Website bisa: muncul di Google, tampil bagus di HP, tombol WA langsung, tampilkan produk/menu, galeri foto, testimoni. Cocok buat warung, kafe, laundry, bengkel, salon, toko. Kak {name} usaha di bidang apa?"]
        },
        agreement: {
            patterns: [/acc|oke|setuju|siap|mau|berminat|deal|ya|gas|mantap|keren|bagus/i],
            replies: ["Alhamdulillah! 🎉 Terima kasih Kak {name} udah percaya. Saya langsung proses ya. Bisa kasih info usahanya? (nama, alamat, bidang)"]
        },
        default: {
            replies: [
                "Terima kasih infonya Kak! 🙏 Website bisa bantu usaha Kak {name} lebih gampang ditemuin di Google dan keliatan profesional. Mau saya buatkan contoh desain gratis dulu?",
                "Oke Kak, noted! 🙏 Untuk UMKM, website itu penting banget karena 80% pelanggan cari di Google dulu. Mau coba gratis dulu? Saya buatkan mockup sesuai bidang usaha Kak {name}.",
            ]
        }
    },
    en: {  // English
        greetings: {
            patterns: [/^(hi|hello|hey|good morning|good afternoon|good evening|ok|okay|sure)/i],
            replies: [
                "Hi there! 👋 Thanks for getting back to me. I'm from ASTRAL, we help small businesses go online with professional websites. Are you looking for a website for {name}?",
                "Hello! Thanks for responding. I help small businesses get found online. Does {name} already have a website?",
            ]
        },
        pricing: {
            patterns: [/price|cost|how much|pricing|expensive|cheap|quote|estimate/i],
            replies: ["Prices start at just $50 (one-time payment, 3 months free maintenance). That includes domain, hosting, professional design, Google visibility, and WhatsApp button. Want more details?"]
        },
        features: {
            patterns: [/feature|what do you|can you|benefit|include/i],
            replies: ["Websites can: appear on Google, look great on mobile, show your products/menu with prices, photo gallery, customer reviews, and WhatsApp button. Perfect for any small business. What type of business is {name}?"]
        },
        agreement: {
            patterns: [/acc|yes|sure|ok|deal|interested|let's do|sounds good|great|perfect/i],
            replies: ["Awesome! 🎉 Thanks for trusting us, {name}! I'll get started right away. Can you share some details about your business? (name, address, type of business)"]
        },
        default: {
            replies: [
                "Thanks for the info! 🙏 A website can help {name} get found on Google and look more professional. Want me to create a free mockup so you can see what it looks like?",
                "Got it! 🙏 For small businesses, a website is crucial because 80% of customers search Google first. Want to try it for free? I'll create a mockup based on your business type.",
            ]
        }
    },
    es: {  // Spanish
        greetings: {
            patterns: [/^(hola|buenos|buenas|hey|ok|vale|sure)/i],
            replies: [
                "¡Hola! 👋 Gracias por responder. Soy de ASTRAL, ayudamos a negocios pequeños a tener presencia online. ¿Estás buscando un sitio web para {name}?",
                "¡Hola! Gracias por contactarnos. Ayudamos a negocios pequeños a ser encontrados online. ¿{name} ya tiene sitio web?",
            ]
        },
        pricing: {
            patterns: [/precio|costo|cuanto|presupuesto|barato|caro/i],
            replies: ["Los precios empiezan desde $50 (pago único, 3 meses de mantenimiento免费). Incluye dominio, hosting, diseño profesional y visibilidad en Google. ¿Quieres más detalles?"]
        },
        features: {
            patterns: [/funcion|que incluye|beneficio|puede hacer/i],
            replies: ["El sitio puede: aparecer en Google, verse bien en celular, mostrar tus productos/menú, galería de fotos, reseñas de clientes y botón de WhatsApp. Perfecto para cualquier negocio. ¿Qué tipo de negocio es {name}?"]
        },
        agreement: {
            patterns: [/si|vale|ok|deal|interesado|me gusta|perfecto|genial/i],
            replies: ["¡Excelente! 🎉 Gracias por confiar en nosotros, {name}! Empiezo de inmediato. ¿Puedes compartir detalles de tu negocio? (nombre, dirección, tipo)"]
        },
        default: {
            replies: [
                "¡Gracias! 🙏 Un sitio web puede ayudar a {name} a ser encontrado en Google y verse más profesional. ¿Quieres que te haga un mockup gratis?",
                "¡Entendido! 🙏 Para negocios pequeños, un sitio web es crucial porque el 80% de los clientes buscan en Google primero. ¿Quieres probarlo gratis? Haré un mockup según tu negocio.",
            ]
        }
    },
    pt: {  // Portuguese
        greetings: {
            patterns: [/^(oi|olá|ola|bom dia|boa tarde|boa noite|ok|sim)/i],
            replies: [
                "Olá! 👋 Obrigado por responder. Sou da ASTRAL, ajudamos pequenos negócios a terem presença online. Você está procurando um site para {name}?",
                "Olá! Obrigado pelo contato. Ajudamos pequenos negócios a serem encontrados online. {name} já tem site?",
            ]
        },
        pricing: {
            patterns: [/preco|valor|quanto|orcamento|barato|caro/i],
            replies: ["Preços começam em $50 (pagamento único, 3 meses de manutenção免费). Inclui domínio, hospedagem, design profissional e visibilidade no Google. Quer mais detalhes?"]
        },
        features: {
            patterns: [/funcionalidade|o que inclui|beneficio|pode fazer/i],
            replies: ["O site pode: aparecer no Google, ficar bonito no celular, mostrar seus produtos/cardápio, galeria de fotos, avaliações e botão do WhatsApp. Perfeito para qualquer negócio. Que tipo de negócio é {name}?"]
        },
        agreement: {
            patterns: [/sim|ok|beleza|combinado|interessado|gostei|otimo|perfeito/i],
            replies: ["Ótimo! 🎉 Obrigado por confiar em nós, {name}! Vou começar agora. Pode compartilhar detalhes do seu negócio? (nome, endereço, tipo)"]
        },
        default: {
            replies: [
                "Obrigado! 🙏 Um site pode ajudar {name} a ser encontrado no Google e parecer mais profissional. Quer que eu faça um mockup grátis?",
                "Entendido! 🙏 Para pequenos negócios, um site é crucial porque 80% dos clientes procuram no Google primeiro. Quer experimentar grátis? Farei um mockup do seu negócio.",
            ]
        }
    },
    fr: {  // French
        greetings: {
            patterns: [/^(bonjour|salut|bonsoir|ok|oui|merci)/i],
            replies: [
                "Bonjour! 👋 Merci d'avoir répondu. Je suis d'ASTRAL, nous aidons les petites entreprises à avoir une présence en ligne. Vous cherchez un site web pour {name}?",
                "Bonjour! Merci de nous avoir contactés. Nous aidons les petites entreprises à être trouvées en ligne. {name} a déjà un site?",
            ]
        },
        pricing: {
            patterns: [/prix|tarif|combien|devis|cher|bon marche/i],
            replies: ["Les prix commencent à 50€ (paiement unique, 3 mois de maintenance免费). Cela inclut le nom de domaine, l'hébergement, le design professionnel et la visibilité sur Google. Voulez-vous plus de détails?"]
        },
        features: {
            patterns: [/fonctionnalite|que comprend|avantage|peut faire/i],
            replies: ["Le site peut: apparaître sur Google, être beau sur mobile, montrer vos produits/menu, galerie photos, avis clients et bouton WhatsApp. Parfait pour toute entreprise. Quel type d'entreprise est {name}?"]
        },
        agreement: {
            patterns: [/oui|ok|d'accord|super|interessant|j'aime|parfait|excellent/i],
            replies: ["Super! 🎉 Merci de nous faire confiance, {name}! Je commence tout de suite. Pouvez-vous partager des détails sur votre entreprise? (nom, adresse, type)"]
        },
        default: {
            replies: [
                "Merci! 🙏 Un site web peut aider {name} à être trouvé sur Google et paraître plus professionnel. Voulez-vous que je fasse une maquette gratuite?",
                "Compris! 🙏 Pour les petites entreprises, un site web est crucial car 80% des clients cherchent sur Google en premier. Voulez-vous essayer gratuitement? Je ferai une maquette.",
            ]
        }
    },
    de: {  // German
        greetings: {
            patterns: [/^(hallo|hi|guten morgen|guten tag|guten abend|ok|ja|danke)/i],
            replies: [
                "Hallo! 👋 Danke für Ihre Nachricht. Ich bin von ASTRAL, wir helfen kleinen Unternehmen, online präsent zu sein. Suchen Sie eine Website für {name}?",
                "Hallo! Vielen Dank für Ihre Kontaktaufnahme. Wir helfen kleinen Unternehmen, online gefunden zu werden. Hat {name} bereits eine Website?",
            ]
        },
        pricing: {
            patterns: [/preis|kosten|wie viel|angebot|teuer|guenstig/i],
            replies: ["Preise beginnen ab $50 (Einmalzahlung, 3 Monate Wartung免费). Enthalten sind Domain, Hosting, professionelles Design und Sichtbarkeit bei Google. Möchten Sie mehr Details?"]
        },
        features: {
            patterns: [/funktion|was beinhaltet|vorteil|kann machen/i],
            replies: ["Die Website kann: bei Google erscheinen, gut auf dem Handy aussehen, Ihre Produkte/Menu zeigen, Fotogalerie, Kundenbewertungen und WhatsApp-Button. Perfekt für jedes Unternehmen. Was für ein Unternehmen ist {name}?"]
        },
        agreement: {
            patterns: [/ja|ok|super|interessiert|gut|perfekt|toll|ausgezeichnet/i],
            replies: ["Super! 🎉 Vielen Dank für Ihr Vertrauen, {name}! Ich fange sofort an. Können Sie Details über Ihr Unternehmen teilen? (Name, Adresse, Art)"]
        },
        default: {
            replies: [
                "Danke! 🙏 Eine Website kann {name} helfen, bei Google gefunden zu werden und professioneller auszusehen. Soll ich ein kostenloses Mockup erstellen?",
                "Verstanden! 🙏 Für kleine Unternehmen ist eine Website entscheidend, weil 80% der Kunden zuerst bei Google suchen. Möchten Sie es kostenlos ausprobieren? Ich erstelle ein Mockup.",
            ]
        }
    },
    ar: {  // Arabic
        greetings: {
            patterns: [/^(مرحبا|السلام|اهلا|أهلا|morning|evening|ok|yes)/i],
            replies: [
                "مرحبا! 👋 شكراً لتواصلكم. أنا من ASTRAL، نساعد الشركات الصغيرة على الوجود عبر الإنترنت. هل تبحثون عن موقع لـ {name}؟",
                "مرحبا! شكراً لتواصلكم. نساعد الشركات الصغيرة على العثور عليها عبر الإنترنت. هل لدى {name} موقع بالفعل؟",
            ]
        },
        pricing: {
            patterns: [/سعر|تكلفة|كم|تقدير|غالي|رخيص/i],
            replies: ["الأسعار تبدأ من $50 (دفع واحد، 3 أشهر صيانة免费). يشمل النطاق والاستضافة والتصميم الاحترافي والظهور على Google. هل تريد المزيد من التفاصيل؟"]
        },
        features: {
            patterns: [/ميزة|ماذا يتضمن|فائدة|يمكن أن يفعل/i],
            replies: ["الموقع يمكنه: الظهور على Google، الشكل الجميل على الجوال، عرض منتجاتك/قائمة الطعام، معرض الصور، تقييمات العملاء وزر WhatsApp. مثالي لأي نوع من الأعمال. ما نوع عمل {name}؟"]
        },
        agreement: {
            patterns: [/نعم|موافق|ممتاز|مهتم|أحب|مثالي|رائع/i],
            replies: ["ممتاز! 🎉 شكراً لثقتكم بنا، {name}! سأبدأ فوراً. هل يمكنك مشاركة تفاصيل عن عملك؟ (الاسم، العنوان، النوع)"]
        },
        default: {
            replies: [
                "شكراً! 🙏 يمكن أن يساعد موقع الويب {name} على الظهور على Google والاحترافية أكثر. هل تريد مني إنشاء نموذج مجاني؟",
                "تم! 🙏 للشركات الصغيرة، موقع الويب أمر حاسم لأن 80% من العملاء يبحثون على Google أولاً. هل تريد تجربته مجاناً؟ سأقوم بإنشاء نموذج.",
            ]
        }
    },
    hi: {  // Hindi
        greetings: {
            patterns: [/^(नमस्ते|नमस्कार|हैलो|हाँ|ok|जी)/i],
            replies: [
                "नमस्ते! 🙏 जवाब देने के लिए धन्यवाद। मैं ASTRAL से हूं, हम छोटे व्यवसायों को ऑनलाइन उपस्थिति दिलाने में मदद करते हैं। क्या आप {name} के लिए वेबसाइट खोज रहे हैं?",
                "नमस्ते! संपर्क करने के लिए धन्यवाद। हम छोटे व्यवसायों को ऑनलाइन खोजने में मदद करते हैं। क्या {name} के पास पहले से वेबसाइट है?",
            ]
        },
        pricing: {
            patterns: [/कीमत|मूल्य|कितना|अनुमान|महंगा|सस्ता/i],
            replies: ["कीमतें $50 से शुरू होती हैं (एक बार का भुगतान, 3 महीने का मुफ्त रखरखाव)। इसमें डोमेन, होस्टिंग, पेशेवर डिज़ाइन और Google पर दृश्यता शामिल है। क्या आप अधिक विवरण चाहते हैं?"]
        },
        features: {
            patterns: [/विशेषता|क्या शामिल|लाभ|क्या कर सकता/i],
            replies: ["वेबसाइट: Google पर दिख सकती है, मोबाइल पर अच्छी दिखती है, आपके उत्पाद/मेनू दिखा सकती है, फोटो गैलरी, ग्राहक समीक्षाएं और WhatsApp बटन। किसी भी व्यवसाय के लिए बिल्कुल सही। {name} किस प्रकार का व्यवसाय है?"]
        },
        agreement: {
            patterns: [/हाँ|ok|बिल्कुल|सहमत|रुचि|अच्छा|बढ़िया|शानदार/i],
            replies: ["शानदार! 🎉 हम पर भरोसा करने के लिए धन्यवाद, {name}! मैं तुरंत शुरू करता हूं। क्या आप अपने व्यवसाय के बारे में विवरण साझा कर सकते हैं? (नाम, पता, प्रकार)"]
        },
        default: {
            replies: [
                "धन्यवाद! 🙏 वेबसाइट {name} को Google पर खोजने और अधिक पेशेवर दिखने में मदद कर सकती है। क्या आप चाहते हैं कि मैं एक मुफ्त मॉकअप बनाऊं?",
                "समझ गया! 🙏 छोटे व्यवसायों के लिए, वेबसाइट महत्वपूर्ण है क्योंकि 80% ग्राहक पहले Google पर खोजते हैं। क्या आप मुफ्त में आज़माना चाहेंगे? मैं एक मॉकअप बनाऊंगा।",
            ]
        }
    },
};

function findReply(text, name, lang) {
    const flow = FLOWS[lang] || FLOWS.en;
    const lower = text.toLowerCase();
    
    for (const [key, f] of Object.entries(flow)) {
        if (key === 'default') continue;
        if (f.patterns && f.patterns.some(p => p.test(lower))) {
            const reply = f.replies[Math.floor(Math.random() * f.replies.length)];
            return reply.replace(/\{name\}/gi, name);
        }
    }
    
    const defaults = flow.default.replies;
    const reply = defaults[Math.floor(Math.random() * defaults.length)];
    return reply.replace(/\{name\}/gi, name);
}

async function handleAutoReply(sock, msg) {
    try {
        const from = msg.key.remoteJid;
        const text = msg.message?.conversation || msg.message?.extendedTextMessage?.text || '';

        if (from.endsWith('@g.us') || from === 'status@broadcast') return;
        if (isMaxAccReached()) return;
        if (!text || text.length < 2) return;

        const sent = readSent();
        const sentInfo = sent[from];
        const name = sentInfo?.name || 'there';

        // Detect language from incoming message
        const lang = detectLanguage(text);
        console.log(`\n  [💬] ${name}: ${text.substring(0, 50)} [${lang}]`);

        addChat(from, 'client', text);

        // Check for conversion
        const isAcc = /acc|yes|sure|ok|deal|interested|setuju|berminat|oui|sim|ja|نعم|हाँ|ok|gas|keren|bagus|perfect|great|excellent|super|genial|toll|ممتاز|शानदार/i.test(text);
        if (isAcc) {
            const accCount = markAcc(from, name);
            if (accCount >= MAX_ACC) {
                console.log(`\n  [🎯] ${MAX_ACC} klien ACC! DM baru dihentikan.`);
                writeStatus({ connected: true, maxAccReached: true, accCount, message: `${MAX_ACC} klien acc` });
            }
        }

        // Generate reply in detected language
        const reply = findReply(text, name, lang);
        await delay(1000 + Math.floor(Math.random() * 2000));
        await sock.sendMessage(from, { text: reply });
        addChat(from, 'bot', reply);
        console.log(`  [✓] Reply [${lang}] terkirim ke ${name}`);
    } catch (e) {
        console.error(`  [!] Auto-reply error: ${e.message}`);
    }
}

const MAPS_MESSAGES = {
    id: "📍 Lihat lokasi usaha di Google Maps:\n{url}",
    en: "📍 See business location on Google Maps:\n{url}",
    es: "📍 Ver ubicación del negocio en Google Maps:\n{url}",
    pt: "📍 Veja a localização do negócio no Google Maps:\n{url}",
    fr: "📍 Voir l'emplacement de l'entreprise sur Google Maps:\n{url}",
    de: "📍 Firmenstandort auf Google Maps ansehen:\n{url}",
    ar: "📍 شاهد موقع العمل على خرائط جوجل:\n{url}",
    hi: "📍 Google Maps पर व्यवसाय का स्थान देखें:\n{url}",
    th: "📍 ดูตำแหน่งธุรกิจบน Google Maps:\n{url}",
    tr: "📍 İş yerini Google Maps'ta görüntüle:\n{url}",
    ja: "📍 Google Mapsで事業場所を確認:\n{url}",
    ko: "📍 Google Maps에서 사업장 위치 보기:\n{url}",
    zh: "📍 在Google Maps查看商家位置:\n{url}",
};

function getMapsMessage(lang, name, address) {
    const tpl = MAPS_MESSAGES[lang] || MAPS_MESSAGES['en'];
    const mapsQuery = encodeURIComponent(`${name} ${address}`);
    const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${mapsQuery}`;
    return tpl.replace('{url}', mapsUrl);
}

async function sendMessages(sock, queue, delayMs) {
    let ok = 0, fail = 0, skipped = 0;

    for (let i = 0; i < queue.length; i++) {
        // ── Cek session masih hidup ──
        const statusNow = readStatus();
        if (statusNow.error === 'logged_out' || statusNow.stopped) {
            console.log('  [!] Session sudah logged out. STOP mengirim.');
            break;
        }

        // ── Warm-up: first 5 messages slower ──
        let thisDelay = delayMs;
        if (ok < 5) {
            thisDelay = 35000 + Math.floor(Math.random() * 15000); // 35-50 detik
            console.log(`  [WARMUP] ${ok+1}/5 pesan pertama, delay ${Math.round(thisDelay/1000)}s`);
        }

        // ── Cek rate limit ──
        const recentCount = getRecentSendCount();
        if (recentCount >= RATE_LIMIT) {
            console.log(`\n  [!] RATE LIMIT: ${recentCount}/${RATE_LIMIT} pesan/jam tercapai`);
            console.log(`  [*] Pause 10 menit, lalu lanjut...`);
            writeStatus({ connected: true, sending: true, paused: true, rateLimit: true, sent: recentCount });
            await delay(10 * 60 * 1000); // Pause 10 menit
        }

        const item = queue[i];
        const phone = item.phone || item.telepon || item.number || '';
        const name = item.name || item.nama || 'Bisnis';
        const lang = item.lang || 'en';
        if (!phone || phone.replace(/\D/g, '').length < 8) {
            console.log(`  [SKIP] ${name} - nomor invalid`);
            skipped++;
            continue;
        }

        const clean = cleanPhone(phone);

        // ── Cek apakah sudah pernah dikirim ──
        if (isAlreadySent(clean)) {
            console.log(`  [SKIP] ${name} - sudah pernah dikirim`);
            skipped++;
            continue;
        }

        const msgTemplate = getDMTemplate(lang);
        const msg = msgTemplate.replace(/\{name\}/gi, name).replace(/\{nama\}/gi, name);

        writeStatus({ connected: true, sending: true, total: queue.length, cur: i + 1, ok, fail, skipped, target: name });

        try {
            const [exists] = await sock.onWhatsApp(clean);
            if (!exists?.exists) { console.log(`  [SKIP] ${name} - no WA`); fail++; continue; }

            await sock.sendMessage(clean, { text: msg });

            // Kirim Google Maps location
            const address = item.address || item.alamat || '';
            const mapsMsg = getMapsMessage(lang, name, address);
            await delay(1000);
            await sock.sendMessage(clean, { text: mapsMsg });

            // Tandai sudah dikirim
            markSent(clean, name);
            ok++;
            console.log(`  [✓] ${i + 1}/${queue.length} ${name} (${ok} ok, ${skipped} skip)`);
        } catch (e) {
            fail++;
            console.log(`  [✗] ${i + 1}/${queue.length} ${name} - ${e.message}`);
        }
        await delay(Math.floor(Math.random() * 3000) + delayMs);
    }
    writeStatus({ connected: true, sending: false, done: true, total: queue.length, ok, fail, skipped });
    console.log(`\n  Selesai: ${ok} ok, ${fail} gagal, ${skipped} skip`);
}

async function runDaemon(sock) {
    const accCount = getAccCount();
    console.log('\n  [✓] WhatsApp aktif. Mode daemon 24/7.');
    console.log('  [*] Rate limit: ' + RATE_LIMIT + ' DM/jam');
    console.log('  [*] Auto-reply: AKTIF (balas otomatis pesan masuk)');
    console.log('  [*] Auto-skip nomor yang sudah dikirim');
    console.log('  [*] Max acc: ' + MAX_ACC + ' klien (saat ini: ' + accCount + ')');
    console.log('  [*] Menunggu wa_queue.json untuk kirim pesan...\n');
    let sending = false;

    setInterval(async () => {
        if (sending) return;
        
        // ── Health check: pastikan masih connected ──
        const status = readStatus();
        if (!status.connected || status.error === 'logged_out' || status.stopped) {
            return; // Jangan coba kirim kalau session udah mati
        }
        
        // Cek apakah max acc tercapai
        if (isMaxAccReached()) {
            console.log(`  [!] Max acc (${MAX_ACC}) tercapai. DM baru dihentikan. Auto-reply tetap aktif.`);
            return;
        }
        
        const queue = readQueue();
        if (queue.length > 0) {
            sending = true;
            const recentCount = getRecentSendCount();
            console.log(`\n  [!] Queue ditemukan: ${queue.length} target (terkirim jam ini: ${recentCount}/${RATE_LIMIT})`);
            
                await sendMessages(sock, queue, 30000);
            writeQueue([]);
            sending = false;
            
            const newCount = getRecentSendCount();
            console.log(`  [*] Total terkirim jam ini: ${newCount}/${RATE_LIMIT}`);
            console.log('  [*] Menunggu queue berikutnya...\n');
        }
    }, 15000);
}

async function startSock(args, mode) {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version } = await fetchLatestBaileysVersion().catch(() => ({ version: [2, 3000, 1035194821] }));

    // Browsers.ubuntu('Chrome') → sends "Chrome (Ubuntu)" to WA
    // CONFIRMED working for pairing code (Issues #328, #2306)
    const sock = makeWASocket({
        auth: { creds: state.creds, keys: makeCacheableSignalKeyStore(state.keys, logger) },
        printQRInTerminal: false,
        logger,
        browser: Browsers.ubuntu('Chrome'),
        version,
        syncFullHistory: false,
        markOnlineOnConnect: false,
    });

    sock.ev.on('creds.update', saveCreds);

    // ── AUTO REPLY: Dengarkan pesan masuk ──
    sock.ev.on('messages.upsert', async ({ messages }) => {
        for (const msg of messages) {
            if (!msg.key.fromMe && msg.message) {
                await handleAutoReply(sock, msg);
            }
        }
    });

    let paired = state.creds.registered;
    let pairingRequested = false;

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        // Request pairing code ONLY on QR event (not during 'connecting')
        if (qr && !state.creds.registered && !pairingRequested && !paired) {
            pairingRequested = true;
            try {
                const phone = (args[1] || MY_PHONE).replace(/[^\d]/g, '');
                console.log(`\n  [*] Requesting pairing code untuk ${phone}...`);
                const code = await sock.requestPairingCode(phone);
                console.log('');
                console.log('  ╔═══════════════════════════════════════╗');
                console.log('  ║  PAIRING CODE: ' + code + '              ║');
                console.log('  ╠═══════════════════════════════════════╣');
                console.log('  ║  Buka WhatsApp di HP Anda             ║');
                console.log('  ║  Settings > Linked Devices             ║');
                console.log('  ║  > Link a Device                       ║');
                console.log('  ║  > Link with Phone Number Instead      ║');
                console.log('  ║  Masukkan kode di atas                 ║');
                console.log('  ╚═══════════════════════════════════════╝');
                console.log('');
                writeStatus({ connected: false, pairing: true, code, phone });
            } catch (e) {
                console.error('  [!] Pairing error:', e.message);
                writeStatus({ connected: false, pairing: false, error: e.message });
            }
        }

        if (connection === 'close') {
            const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;

            // restartRequired (515) = pairing succeeded, must reconnect
            if (reason === DisconnectReason.restartRequired) {
                console.log('\n  [✓] Pairing berhasil! Reconnecting...');
                writeStatus({ connected: true, paired: true, reconnecting: true });
                paired = true;
                return startSock(args, mode);
            }

            if (reason === DisconnectReason.loggedOut) {
                console.log('');
                console.log('  ╔══════════════════════════════════════════╗');
                console.log('  ║  [!] SESSION LOGGED OUT BY WHATSAPP      ║');
                console.log('  ║  WA mendeteksi spam & memutus session.   ║');
                console.log('  ║  Solusi:                                 ║');
                console.log('  ║  1. Jalankan: node astral_wa.js pair     ║');
                console.log('  ║  2. Pair ulang nomor WA Anda             ║');
                console.log('  ║  3. Tunggu 1-2 jam sebelum kirim lagi   ║');
                console.log('  ╚══════════════════════════════════════════╝');
                console.log('');
                sending = false;
                writeStatus({ connected: false, error: 'logged_out', stopped: true, reason: 'session_banned' });
                return; // JANGAN auto-reconnect, stop!
            }

            console.log(`  [*] Reconnecting (reason: ${reason})...`);
            writeStatus({ connected: false, reconnecting: true });
            return startSock(args, mode);
        }

        if (connection === 'open') {
            paired = true;
            console.log('\n  [✓] WhatsApp terhubung!');
            process.stdout.write('\x07'); // Terminal bell
            writeStatus({ connected: true, paired: true });

            if (mode === 'pair') {
                console.log('  [*] Pairing selesai! Bot siap.');
                console.log('  [*] Tekan Ctrl+C atau jalankan:');
                console.log('  node astral_wa.js send <csv> <pesan> <delay_ms>');
            }

            if (mode === 'daemon') {
                await runDaemon(sock);
            }

            if (mode === 'send' && args[1]) {
                const csvPath = args[1];
                const msg = args[2] || 'Halo {name}, kami ingin menawarkan...';
                const dly = parseInt(args[3]) || 5000;

                if (!fs.existsSync(csvPath)) {
                    console.log('  [!] CSV tidak ditemukan:', csvPath);
                    process.exit(1);
                }
                const queue = await csv().fromFile(csvPath);
                if (!queue.length) { console.log('  [!] CSV kosong.'); process.exit(1); }

                console.log(`\n  [*] Kirim ke ${queue.length} target, delay ${dly}ms\n`);
                await sendMessages(sock, queue, msg, dly);
                console.log('\n  [*] Selesai. Tekan Ctrl+C untuk keluar.\n');
            }
        }
    });

    return sock;
}

async function main() {
    ensureDirs();
    const args = process.argv.slice(2);
    const mode = args[0] || 'daemon';
    await startSock(args, mode);

    process.on('SIGINT', () => { writeStatus({ connected: false, shutdown: true }); process.exit(0); });
    process.on('uncaughtException', (e) => {
        if (e.message === 'Invalid buffer') {
            console.log('  [!] Ignoring known Baileys bug (Invalid buffer during pairing)');
            return;
        }
        console.error('  [!] Err:', e.message);
    });
}

main().catch(e => { console.error('Fatal:', e.message); process.exit(1); });
