#!/bin/bash
# Whisper Walkie — Linux Installer
# Creates a desktop shortcut and installs optional dependencies.
# Run this from inside the extracted WhisperWalkie folder.

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_BIN="$APP_DIR/WhisperWalkie"
ICON="$APP_DIR/_internal/icon-512.png"
DESKTOP_FILE="$HOME/.local/share/applications/whisperwalkie.desktop"

if [ ! -f "$APP_BIN" ]; then
    echo "Error: WhisperWalkie binary not found at $APP_BIN"
    echo "Run this script from inside the extracted WhisperWalkie folder."
    exit 1
fi

echo "Installing Whisper Walkie..."
echo ""

# ── Install optional system dependency ───────────────────────────────
# xdotool enables window title detection (optional but recommended)
if ! command -v xdotool &>/dev/null; then
    echo "Installing xdotool (optional, for window title detection)..."
    if command -v apt &>/dev/null; then
        sudo apt install -y xdotool
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y xdotool
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm xdotool
    else
        echo "  Could not auto-install xdotool. Install manually if needed."
    fi
    echo ""
fi

# ── Make binary executable ───────────────────────────────────────────
chmod +x "$APP_BIN"

# ── Create desktop shortcut ─────────────────────────────────────────
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Whisper Walkie
Comment=Local push-to-talk voice transcription
Exec=$APP_BIN
Icon=$ICON
Type=Application
Categories=Utility;Audio;
Terminal=false
EOF

echo "Whisper Walkie installed successfully!"
echo ""
echo "  Binary:   $APP_BIN"
echo "  Shortcut: $DESKTOP_FILE"
echo ""
echo "You can now:"
echo "  - Find 'Whisper Walkie' in your application menu"
echo "  - Or run directly: $APP_BIN"
