#!/bin/bash
# Whisper Walkie — Wayland Setup Helper
# This script is run via pkexec (graphical sudo) to install system
# dependencies needed for Wayland support.  It is NOT meant to be
# run manually — the app invokes it automatically on first launch.
#
# Usage (called by the app):  pkexec /path/to/setup-wayland.sh <username>

set -e

USERNAME="${1:?Usage: setup-wayland.sh <username>}"
CACHE_DIR="/home/$USERNAME/.whisper-walkie"

# ── Install wtype (text injection on Wayland) ─────────────────────
if ! command -v wtype &>/dev/null; then
    if command -v apt-get &>/dev/null; then
        apt-get install -y -qq wtype 2>/dev/null
    elif command -v dnf &>/dev/null; then
        dnf install -y -q wtype 2>/dev/null
    elif command -v pacman &>/dev/null; then
        pacman -S --noconfirm --quiet wtype 2>/dev/null
    fi
fi

# ── Add user to input group (hotkey detection on Wayland) ─────────
if ! getent group input &>/dev/null; then
    echo "WARNING: 'input' group does not exist on this system" >&2
else
    if ! id -nG "$USERNAME" 2>/dev/null | grep -qw input; then
        usermod -aG input "$USERNAME"
        echo "ADDED_INPUT_GROUP"
    fi
fi

# ── Cache dumpkeys output (pynput uinput backend needs this) ──────
# dumpkeys requires /dev/console access (root only).  We cache its
# output so pynput can load the keyboard layout without root.
if command -v dumpkeys &>/dev/null; then
    mkdir -p "$CACHE_DIR"
    dumpkeys --full-table --keys-only > "$CACHE_DIR/dumpkeys.cache" 2>/dev/null || true
    chown "$USERNAME:" "$CACHE_DIR/dumpkeys.cache" 2>/dev/null || true
fi

exit 0
