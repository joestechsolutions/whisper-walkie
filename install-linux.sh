#!/bin/bash
# Whisper Walkie — Linux Desktop Installer
# Creates a .desktop shortcut so the app appears in your application launcher.
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

# Ensure the binary is executable
chmod +x "$APP_BIN"

# Create .desktop entry
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
echo "  Binary: $APP_BIN"
echo "  Shortcut: $DESKTOP_FILE"
echo ""
echo "You can now launch Whisper Walkie from your application menu."
echo "Or run it directly: $APP_BIN"
