#!/bin/bash
# ╔════════════════════════════════════════════════════╗
# ║  ASTRAL Build Script - Buat package untuk dijual  ║
# ╚════════════════════════════════════════════════════╝

set -e

VERSION="2.0"
BUILD_DIR="astral_build"
DIST_DIR="astral_dist"

echo ""
echo "  ASTRAL Builder v${VERSION}"
echo "  ========================="
echo ""

# Clean
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Copy files
echo "[1/5] Copying files..."
cp astral_wa.js "$BUILD_DIR/"
cp install.sh "$BUILD_DIR/"
cp README_PEMBELI.md "$BUILD_DIR/README.md"
cp package.json "$BUILD_DIR/" 2>/dev/null || echo '{"name":"astral","version":"2.0","dependencies":{"@whiskeysockets/baileys":"^6.7.16","pino":"^9.6.0"}}' > "$BUILD_DIR/package.json"

# Obfuscate Python script
echo "[2/5] Obfuscating scrape.py..."
python3 encode.py scrape.py "$BUILD_DIR/scrape.py"
rm -f "$BUILD_DIR/scrape.pyc"

# Remove license file (trial starts fresh)
rm -f "$BUILD_DIR/license.json"

# Create zip
echo "[3/5] Creating zip package..."
cd "$BUILD_DIR"
zip -r "../$DIST_DIR/ASTRAL_v${VERSION}.zip" . -x "*.pyc" "*__pycache__*" "*.git*"
cd ..

# Create tar.gz
echo "[4/5] Creating tar.gz package..."
tar czf "$DIST_DIR/ASTRAL_v${VERSION}.tar.gz" -C "$BUILD_DIR" .

# Summary
echo "[5/5] Build complete!"
echo ""
echo "  Package ready:"
echo "  ├── $DIST_DIR/ASTRAL_v${VERSION}.zip"
echo "  └── $DIST_DIR/ASTRAL_v${VERSION}.tar.gz"
echo ""
echo "  Files included:"
ls -la "$BUILD_DIR/"
echo ""
echo "  Next steps:"
echo "  1. Kirim zip ke pembeli"
echo "  2. Pembeli jalankan: bash install.sh"
echo "  3. Pembeli jalankan: python3 scrape.py"
echo ""
