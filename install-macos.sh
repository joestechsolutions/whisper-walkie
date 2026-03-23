#!/bin/bash
# Whisper Walkie — macOS Installer
# Moves the app to /Applications and creates a launch alias.
# Run this from inside the extracted WhisperWalkie folder.

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_BIN="$APP_DIR/WhisperWalkie"
INSTALL_DIR="/Applications/WhisperWalkie"

if [ ! -f "$APP_BIN" ]; then
    echo "Error: WhisperWalkie binary not found at $APP_BIN"
    echo "Run this script from inside the extracted WhisperWalkie folder."
    exit 1
fi

echo "Installing Whisper Walkie..."

# Move to /Applications if not already there
if [ "$APP_DIR" != "$INSTALL_DIR" ]; then
    if [ -d "$INSTALL_DIR" ]; then
        echo "Removing previous installation..."
        rm -rf "$INSTALL_DIR"
    fi
    cp -R "$APP_DIR" "$INSTALL_DIR"
    echo "Copied to $INSTALL_DIR"
fi

# Ensure binary is executable
chmod +x "$INSTALL_DIR/WhisperWalkie"

# Remove quarantine attribute so Gatekeeper doesn't block it
xattr -dr com.apple.quarantine "$INSTALL_DIR" 2>/dev/null || true

# Create a minimal .app wrapper so it appears in Launchpad and Spotlight
APP_BUNDLE="$INSTALL_DIR/Whisper Walkie.app"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

# Copy icon if available
if [ -f "$INSTALL_DIR/_internal/icon-512.png" ]; then
    cp "$INSTALL_DIR/_internal/icon-512.png" "$APP_BUNDLE/Contents/Resources/icon.png"
fi

# Create launcher script
cat > "$APP_BUNDLE/Contents/MacOS/WhisperWalkie" << 'LAUNCHER'
#!/bin/bash
DIR="$(dirname "$(dirname "$(dirname "$0")")")"
exec "$DIR/WhisperWalkie"
LAUNCHER
chmod +x "$APP_BUNDLE/Contents/MacOS/WhisperWalkie"

# Create Info.plist
cat > "$APP_BUNDLE/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Whisper Walkie</string>
    <key>CFBundleDisplayName</key>
    <string>Whisper Walkie</string>
    <key>CFBundleIdentifier</key>
    <string>com.joestechsolutions.whisperwalkie</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>WhisperWalkie</string>
    <key>CFBundleIconFile</key>
    <string>icon.png</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
</dict>
</plist>
PLIST

echo ""
echo "Whisper Walkie installed successfully!"
echo "  Location: $INSTALL_DIR"
echo "  App: $APP_BUNDLE"
echo ""
echo "You can now:"
echo "  - Find 'Whisper Walkie' in Launchpad or Spotlight"
echo "  - Or run directly: $INSTALL_DIR/WhisperWalkie"
echo ""
echo "Note: On first launch, grant Accessibility permissions in"
echo "  System Settings → Privacy & Security → Accessibility"
