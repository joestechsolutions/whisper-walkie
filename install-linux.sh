#!/bin/bash
# Whisper Walkie — Linux Installer
# Installs system dependencies, creates a desktop shortcut, and makes
# the app ready to launch from your application menu.
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

# ── Install system dependencies ──────────────────────────────────────
MISSING_DEPS=""

# PortAudio is required for microphone access
if ! ldconfig -p 2>/dev/null | grep -q libportaudio; then
    MISSING_DEPS="$MISSING_DEPS libportaudio2"
fi

# xdotool is optional but recommended for window title detection
if ! command -v xdotool &>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS xdotool"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo "Installing system dependencies:$MISSING_DEPS"
    if command -v apt &>/dev/null; then
        sudo apt install -y $MISSING_DEPS
    elif command -v dnf &>/dev/null; then
        # Fedora/RHEL: package names differ
        FEDORA_DEPS=""
        echo "$MISSING_DEPS" | grep -q "libportaudio2" && FEDORA_DEPS="$FEDORA_DEPS portaudio"
        echo "$MISSING_DEPS" | grep -q "xdotool" && FEDORA_DEPS="$FEDORA_DEPS xdotool"
        sudo dnf install -y $FEDORA_DEPS
    elif command -v pacman &>/dev/null; then
        # Arch: package names differ
        ARCH_DEPS=""
        echo "$MISSING_DEPS" | grep -q "libportaudio2" && ARCH_DEPS="$ARCH_DEPS portaudio"
        echo "$MISSING_DEPS" | grep -q "xdotool" && ARCH_DEPS="$ARCH_DEPS xdotool"
        sudo pacman -S --noconfirm $ARCH_DEPS
    else
        echo "Could not detect package manager. Please install manually:"
        echo "  PortAudio (required): libportaudio2 / portaudio"
        echo "  xdotool (optional): xdotool"
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
