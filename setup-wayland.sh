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

# ── Install ydotool + wtype + xdotool (text injection on Wayland) ─
# ydotool is the primary method — its character-by-character typing via
# /dev/uinput works on GNOME/Mutter and wlroots compositors.
# wtype is a fallback for wlroots (Sway, Hyprland).
# xdotool is a fallback for XWayland windows.
for pkg in ydotool wl-clipboard wtype xdotool; do
    cmd="${pkg%%-*}"  # wl-clipboard -> wl, wtype -> wtype, xdotool -> xdotool
    [ "$pkg" = "wl-clipboard" ] && cmd="wl-copy"
    if ! command -v "$cmd" &>/dev/null; then
        if command -v apt-get &>/dev/null; then
            apt-get install -y -qq "$pkg" 2>/dev/null
        elif command -v dnf &>/dev/null; then
            dnf install -y -q "$pkg" 2>/dev/null
        elif command -v pacman &>/dev/null; then
            pacman -S --noconfirm --quiet "$pkg" 2>/dev/null
        fi
    fi
done

# ── Add user to input group (hotkey detection on Wayland) ─────────
if ! getent group input &>/dev/null; then
    echo "WARNING: 'input' group does not exist on this system" >&2
else
    if ! id -nG "$USERNAME" 2>/dev/null | grep -qw input; then
        usermod -aG input "$USERNAME"
        echo "ADDED_INPUT_GROUP"
    fi
fi

# ── Allow input group to write /dev/uinput (text injection) ───────
# By default /dev/uinput is root-only.  pynput's uinput Controller
# needs write access to create a virtual keyboard for text injection.
# This is the only method that works reliably on GNOME Wayland (wtype
# requires zwp_virtual_keyboard_v1 which Mutter does not implement,
# and xdotool only reaches XWayland clients).
UINPUT_RULE="/etc/udev/rules.d/99-whisper-walkie-uinput.rules"
if [ ! -f "$UINPUT_RULE" ]; then
    echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' > "$UINPUT_RULE"
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger /dev/uinput 2>/dev/null || true
    echo "ADDED_UINPUT_RULE"
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
