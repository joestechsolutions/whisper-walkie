"""macOS platform backend for Whisper Walkie.

Uses pynput for keyboard monitoring and text injection via CGEvents.
Requires Accessibility permissions in System Preferences > Privacy & Security > Accessibility.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any, Callable

import pynput.keyboard

from .base import PlatformBackend

log = logging.getLogger("walkie")

# ---------------------------------------------------------------------------
# Key name translation table
# ---------------------------------------------------------------------------
# Maps pynput special Key members to the normalised string names used by the
# rest of the application.  Entries not listed here fall back to the
# pynput-generated name (e.g. "Key.space" -> stripped to just the attribute).
# Build the key map dynamically — some Key members (num_lock, insert, pause,
# print_screen, scroll_lock) do not exist on macOS and would cause an
# AttributeError at import time if referenced directly.
_KEY_ENTRIES: list[tuple[str, str]] = [
    ("alt",          "alt"),
    ("alt_l",        "left alt"),
    ("alt_r",        "right alt"),
    ("ctrl",         "ctrl"),
    ("ctrl_l",       "left ctrl"),
    ("ctrl_r",       "right ctrl"),
    ("shift",        "shift"),
    ("shift_l",      "left shift"),
    ("shift_r",      "right shift"),
    ("cmd",          "cmd"),
    ("cmd_l",        "left cmd"),
    ("cmd_r",        "right cmd"),
    ("space",        "space"),
    ("enter",        "enter"),
    ("backspace",    "backspace"),
    ("delete",       "delete"),
    ("tab",          "tab"),
    ("esc",          "esc"),
    ("up",           "up"),
    ("down",         "down"),
    ("left",         "left"),
    ("right",        "right"),
    ("home",         "home"),
    ("end",          "end"),
    ("page_up",      "page up"),
    ("page_down",    "page down"),
    ("caps_lock",    "caps lock"),
    ("num_lock",     "num lock"),
    ("scroll_lock",  "scroll lock"),
    ("pause",        "pause"),
    ("insert",       "insert"),
    ("print_screen", "print screen"),
    ("f1",  "f1"),  ("f2",  "f2"),  ("f3",  "f3"),  ("f4",  "f4"),
    ("f5",  "f5"),  ("f6",  "f6"),  ("f7",  "f7"),  ("f8",  "f8"),
    ("f9",  "f9"),  ("f10", "f10"), ("f11", "f11"), ("f12", "f12"),
    ("f13", "f13"), ("f14", "f14"), ("f15", "f15"), ("f16", "f16"),
    ("f17", "f17"), ("f18", "f18"), ("f19", "f19"), ("f20", "f20"),
]

_SPECIAL_KEY_MAP: dict[pynput.keyboard.Key, str] = {}
for _attr, _name in _KEY_ENTRIES:
    _key = getattr(pynput.keyboard.Key, _attr, None)
    if _key is not None:
        _SPECIAL_KEY_MAP[_key] = _name


def _translate_key(key: pynput.keyboard.Key | pynput.keyboard.KeyCode) -> tuple[str, int]:
    """Return (key_name, scan_code) for a pynput key object.

    key_name is the normalised lowercase string understood by the rest of the
    application.  scan_code is the virtual-key code on macOS (vk), or 0 when
    not available.
    """
    if isinstance(key, pynput.keyboard.Key):
        # Special / named key
        name = _SPECIAL_KEY_MAP.get(key)
        if name is None:
            # Fall back: strip the "Key." prefix from the repr
            name = key.name if hasattr(key, "name") else str(key)
        scan_code = 0
        try:
            vk_val = key.value
            if vk_val is not None and hasattr(vk_val, "vk"):
                scan_code = vk_val.vk or 0
        except Exception:
            pass
        return name.lower(), scan_code

    # KeyCode — a character or raw virtual-key event
    scan_code = 0
    try:
        if hasattr(key, "vk") and key.vk is not None:
            scan_code = key.vk
    except Exception:
        pass

    if key.char is not None:
        return key.char.lower(), scan_code

    # No printable character; use the vk as a string representation
    return f"vk:{scan_code}", scan_code


# ---------------------------------------------------------------------------
# MacOSBackend
# ---------------------------------------------------------------------------


class MacOSBackend(PlatformBackend):
    """Platform backend for macOS using pynput.

    Keyboard events are captured through a Quartz event tap (read-only mode)
    managed by pynput's Listener.  Text injection uses pynput's Controller
    which sends CGEvents directly to the active application.

    Accessibility permissions are required.  If the app has not been granted
    access, pynput will fail to start the Listener; a helpful error is logged
    directing the user to System Preferences > Privacy & Security > Accessibility.
    """

    def __init__(self) -> None:
        self._listener: pynput.keyboard.Listener | None = None
        self._controller = pynput.keyboard.Controller()
        self._last_callback: Callable | None = None

    # ------------------------------------------------------------------
    # type_text
    # ------------------------------------------------------------------

    def type_text(self, text: str) -> int:
        """Inject *text* into the focused window using CGEvents via pynput.

        Returns the number of characters successfully injected (i.e. len(text)
        on success, 0 on failure).
        """
        if not text:
            return 0
        try:
            self._controller.type(text)
            log.info("type_text: injected %d characters via pynput Controller", len(text))
            return len(text)
        except Exception as exc:
            log.error("type_text: failed to inject text: %s", exc)
            return 0

    # ------------------------------------------------------------------
    # install_key_hook
    # ------------------------------------------------------------------

    def install_key_hook(self, callback: Callable) -> Any:
        """Start a pynput Listener and return it as the hook handle.

        *callback* is called with ``(event_type, key_name, scan_code)`` where
        ``event_type`` is ``'down'`` or ``'up'``.

        If the Listener cannot be started (most commonly because Accessibility
        access has not been granted) an error is logged and None is returned.
        """
        self._last_callback = callback

        def on_press(key: pynput.keyboard.Key | pynput.keyboard.KeyCode) -> None:
            try:
                name, scan_code = _translate_key(key)
                callback("down", name, scan_code)
            except Exception as exc:
                log.debug("install_key_hook on_press error: %s", exc)

        def on_release(key: pynput.keyboard.Key | pynput.keyboard.KeyCode) -> None:
            try:
                name, scan_code = _translate_key(key)
                callback("up", name, scan_code)
            except Exception as exc:
                log.debug("install_key_hook on_release error: %s", exc)

        try:
            listener = pynput.keyboard.Listener(
                on_press=on_press,
                on_release=on_release,
            )
            listener.start()
            self._listener = listener
            log.info("install_key_hook: pynput Listener started (thread=%s)", listener.name)
            return listener
        except Exception as exc:
            log.error(
                "install_key_hook: failed to start Listener: %s\n"
                "  --> Make sure the app is granted Accessibility access in\n"
                "      System Preferences > Privacy & Security > Accessibility.",
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # remove_key_hook
    # ------------------------------------------------------------------

    def remove_key_hook(self, handle: Any = None) -> None:
        """Stop the pynput Listener identified by *handle* (or the current one).

        If *handle* is None the internally-tracked listener is stopped.
        """
        target: pynput.keyboard.Listener | None = handle if handle is not None else self._listener
        if target is None:
            log.debug("remove_key_hook: no active listener to remove")
            return
        try:
            target.stop()
            log.info("remove_key_hook: Listener stopped")
        except Exception as exc:
            log.warning("remove_key_hook: error stopping Listener: %s", exc)
        finally:
            if target is self._listener:
                self._listener = None

    # ------------------------------------------------------------------
    # reinstall_key_hook
    # ------------------------------------------------------------------

    def reinstall_key_hook(self, callback: Callable) -> Any:
        """Create and start a fresh Listener with the same *callback*.

        Any previously running listener is stopped first.
        """
        self.remove_key_hook()
        return self.install_key_hook(callback)

    # ------------------------------------------------------------------
    # get_foreground_window_title
    # ------------------------------------------------------------------

    def get_foreground_window_title(self) -> str:
        """Return the name of the frontmost application via AppleScript.

        Returns an empty string when the title cannot be determined.
        """
        script = (
            'tell application "System Events" to get name of '
            "first process whose frontmost is true"
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2,
            )
            title = result.stdout.strip()
            log.debug("get_foreground_window_title: %r", title)
            return title
        except Exception as exc:
            log.debug("get_foreground_window_title: osascript error: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # pre_injection_cleanup
    # ------------------------------------------------------------------

    def pre_injection_cleanup(self) -> None:
        """No-op on macOS.

        macOS does not activate the menu bar on Option/Alt release the way
        Windows does with the Alt key, so no pre-injection cleanup is needed.
        """
        log.debug("pre_injection_cleanup: no-op on macOS")

    # ------------------------------------------------------------------
    # needs_unhook_for_injection
    # ------------------------------------------------------------------

    @property
    def needs_unhook_for_injection(self) -> bool:
        """False on macOS.

        pynput's Listener uses a Quartz event tap in *listen-only* (read-only)
        mode and does **not** intercept or block synthetic keystrokes produced
        by the Controller.  Unhooking before injection is therefore unnecessary.
        """
        return False

    # ------------------------------------------------------------------
    # release_modifier_keys
    # ------------------------------------------------------------------

    def release_modifier_keys(self) -> None:
        """Send key-up events for common modifier keys via pynput.

        Releasing a key that is not currently pressed may raise an exception
        on some macOS versions; each release is individually wrapped in a
        try/except so a failure on one key does not block the others.
        """
        modifiers = [
            pynput.keyboard.Key.alt,
            pynput.keyboard.Key.alt_l,
            pynput.keyboard.Key.alt_r,
            pynput.keyboard.Key.ctrl,
            pynput.keyboard.Key.ctrl_l,
            pynput.keyboard.Key.ctrl_r,
            pynput.keyboard.Key.shift,
            pynput.keyboard.Key.shift_l,
            pynput.keyboard.Key.shift_r,
        ]
        for mod in modifiers:
            try:
                self._controller.release(mod)
            except Exception:
                # Silently ignore — the key was not held down
                pass
        log.debug("release_modifier_keys: modifier release sweep complete")

    # ------------------------------------------------------------------
    # get_hotkey_names
    # ------------------------------------------------------------------

    def get_hotkey_names(self, hotkey: str) -> set[str]:
        """Return the set of all names that should match *hotkey* on macOS.

        On macOS, Right Alt is reported by pynput as both ``alt_r`` and
        ``option_r``.  This method expands the canonical name accordingly so
        that event matching works regardless of which name pynput emits.
        """
        lower = hotkey.lower()
        if lower == "right alt":
            return {"right alt", "option_r", "alt_r"}
        if lower == "left alt":
            return {"left alt", "option_l", "alt_l"}
        return {lower}

    # ------------------------------------------------------------------
    # get_hotkey_scan_codes
    # ------------------------------------------------------------------

    def get_hotkey_scan_codes(self, hotkey: str) -> set[int]:
        """Return an empty set — pynput on macOS matches by key name, not scan code."""
        return set()
