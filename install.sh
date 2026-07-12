#!/bin/bash
# ╔════════════════════════════════════════════════════╗
# ║  ASTRAL - Scraper + Auto WA DM Installer          ║
# ║  Jalankan: bash install.sh                        ║
# ╚════════════════════════════════════════════════════╝

set -e

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'

HOME_DIR="$HOME"
SCRIPT_DIR="$HOME_DIR"
DATA_DIR="$HOME_DIR/astral_data"
AUDIO_DIR="$DATA_DIR"

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  ASTRAL Installer v2.0                            ║${NC}"
echo -e "${CYAN}║  Scraper + Auto WA DM + Auto Reply                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Update & install dependencies
echo -e "${YELLOW}[1/6] Installing system dependencies...${NC}"
pkg update -y > /dev/null 2>&1 || true
pkg install -y python nodejs > /dev/null 2>&1 || true
echo -e "${GREEN}  ✓ System packages updated${NC}"

# Step 2: Install Python packages
echo -e "${YELLOW}[2/6] Installing Python packages...${NC}"
pip install requests fpdf2 > /dev/null 2>&1 || true
echo -e "${GREEN}  ✓ Python packages installed${NC}"

# Step 3: Install Node.js packages
echo -e "${YELLOW}[3/6] Installing Node.js packages...${NC}"
cd "$SCRIPT_DIR"
if [ ! -f "package.json" ]; then
    npm init -y > /dev/null 2>&1
fi
npm install @whiskeysockets/baileys pino > /dev/null 2>&1 || true
echo -e "${GREEN}  ✓ Node.js packages installed${NC}"

# Step 4: Create data directories
echo -e "${YELLOW}[4/6] Creating data directories...${NC}"
mkdir -p "$DATA_DIR"
mkdir -p "$AUDIO_DIR"
echo -e "${GREEN}  ✓ Directories created${NC}"

# Step 5: Generate audio files
echo -e "${YELLOW}[5/6] Generating audio files...${NC}"
python3 -c "
import struct, wave, math, os

data_dir = '$AUDIO_DIR'

def make_wav(filename, freq, duration, fade=True):
    sample_rate = 22050
    frames = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        val = math.sin(2 * math.pi * freq * t)
        if fade:
            val *= max(0, 1 - t/duration)
        frames.append(struct.pack('<h', int(val * 16000)))
    path = os.path.join(data_dir, filename)
    with wave.open(path, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b''.join(frames))

make_wav('beep.wav', 880, 0.15)
make_wav('success.wav', 1200, 0.2)
make_wav('error.wav', 440, 0.3)
make_wav('tick.wav', 1200, 0.02)
make_wav('ding.wav', 1500, 0.1)
print('Audio files generated')
" > /dev/null 2>&1
echo -e "${GREEN}  ✓ Audio files generated${NC}"

# Step 6: Make scripts executable
echo -e "${YELLOW}[6/6] Setting up scripts...${NC}"
chmod +x "$SCRIPT_DIR/scrape.py" 2>/dev/null || true
chmod +x "$SCRIPT_DIR/astral_wa.js" 2>/dev/null || true
echo -e "${GREEN}  ✓ Scripts ready${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ INSTALASI SELESAI!                             ║${NC}"
echo -e "${GREEN}║                                                    ║${NC}"
echo -e "${GREEN}║  Cara jalankan:                                    ║${NC}"
echo -e "${GREEN}║  python3 scrape.py                                 ║${NC}"
echo -e "${GREEN}║                                                    ║${NC}"
echo -e "${GREEN}║  Langkah selanjutnya:                              ║${NC}"
echo -e "${GREEN}║  1. Jalankan script di atas                        ║${NC}"
echo -e "${GREEN}║  2. Masukkan API key SerpApi (gratis)              ║${NC}"
echo -e "${GREEN}║  3. Pair WhatsApp                                  ║${NC}"
echo -e "${GREEN}║  4. Pilih Scrape & Auto DM                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
