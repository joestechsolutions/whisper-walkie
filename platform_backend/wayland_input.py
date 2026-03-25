"""Wayland text injection via ydotool.

ydotool's character-by-character typing via /dev/uinput works on GNOME
Wayland (Mutter) even though wtype, xdotool, pynput, and AT-SPI do not.
This is the primary injection method for Wayland compositors.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Optional

log = logging.getLogger("walkie")


class WaylandInput:
    """Injects text on Wayland via ydotool character-by-character typing."""

    def __init__(self) -> None:
        self._ydotool: Optional[str] = shutil.which("ydotool")
        self._wtype: Optional[str] = shutil.which("wtype")
        self._available = False

    def setup(self) -> None:
        if self._ydotool is not None:
            self._available = True
            log.info("WaylandInput: ydotool found — text injection ready")
        elif self._wtype is not None:
            self._available = True
            log.info("WaylandInput: wtype found (wlroots compositors)")
        else:
            log.warning(
                "WaylandInput: neither ydotool nor wtype found — "
                "install ydotool for Wayland text injection"
            )

    @property
    def available(self) -> bool:
        return self._available

    def type_text(self, text: str) -> bool:
        """Type text into the focused window character by character.

        Uses ydotool type with a small inter-key delay for reliability.
        Falls back to wtype for wlroots compositors (Sway, Hyprland).
        """
        if not self._available:
            return False

        # Primary: ydotool (works on GNOME Wayland + wlroots)
        if self._ydotool is not None:
            try:
                result = subprocess.run(
                    [self._ydotool, "type", "--key-delay", "3", "--", text],
                    timeout=max(5, len(text) * 0.01),
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    log.debug("WaylandInput: typed %d chars via ydotool", len(text))
                    return True
                log.warning(
                    "WaylandInput: ydotool exited %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
            except Exception as exc:
                log.warning("WaylandInput: ydotool failed: %s", exc)

        # Fallback: wtype (wlroots compositors only)
        if self._wtype is not None:
            try:
                result = subprocess.run(
                    [self._wtype, "--", text],
                    timeout=5,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    log.debug("WaylandInput: typed %d chars via wtype", len(text))
                    return True
                log.warning(
                    "WaylandInput: wtype exited %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
            except Exception as exc:
                log.warning("WaylandInput: wtype failed: %s", exc)

        return False
