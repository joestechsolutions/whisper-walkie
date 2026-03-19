"""Windows platform backend for Whisper Walkie.

Implements PlatformBackend using the Win32 API (via ctypes) for keystroke
injection and ``pynput`` for global key hooks.

Key design decisions:

- The INPUT union includes all three input types (KEYBDINPUT, MOUSEINPUT,
  HARDWAREINPUT) so ctypes.sizeof(INPUT) == 40 bytes on x64.  Without
  MOUSEINPUT the struct is too small and SendInput silently returns 0.

- Unicode characters are injected one at a time with KEYEVENTF_UNICODE so
  no clipboard is needed and no Ctrl+V modifier interaction occurs.

- Stuck modifier keys (right/left/generic Alt, Ctrl, Shift) are released
  with key-up events before every text injection to prevent AltGr artefacts.

- pynput's Listener on Windows uses WH_KEYBOARD_LL but is read-only — it
  does NOT intercept or block synthetic SendInput keystrokes.  The callback
  receives an ``injected`` flag so we can ignore our own synthetic events.
  This means needs_unhook_for_injection = False (no hook juggling needed).
"""

import ctypes
import ctypes.wintypes
import logging
import time
from typing import Any, Callable, Optional

from pynput import keyboard as pynput_keyboard
from pynput.keyboard import Key, KeyCode, Listener

from .base import PlatformBackend

log = logging.getLogger("walkie")

# ---------------------------------------------------------------------------
# Win32 constants
# ---------------------------------------------------------------------------

INPUT_KEYBOARD: int = 1
INPUT_MOUSE: int = 0

KEYEVENTF_KEYUP: int = 0x0002
KEYEVENTF_UNICODE: int = 0x0004

MOUSEEVENTF_LEFTDOWN: int = 0x0002
MOUSEEVENTF_LEFTUP: int = 0x0004

VK_SHIFT: int = 0x10
VK_CONTROL: int = 0x11
VK_MENU: int = 0x12    # generic Alt
VK_ESCAPE: int = 0x1B
VK_LMENU: int = 0xA4   # Left Alt
VK_RMENU: int = 0xA5   # Right Alt

# Right Alt / AltGr — pynput reports as Key.alt_r (vk=165) but keyboard
# layouts and tools may report alternate names.
_RIGHT_ALT_NAMES: frozenset = frozenset({'right alt', 'alt_r', 'alt gr', 'altgr'})

# VK codes for Right Alt matching (VK_RMENU = 0xA5 = 165)
_RIGHT_ALT_VK_CODES: frozenset = frozenset({165})

# ---------------------------------------------------------------------------
# Key name mapping for pynput Key enum members
# ---------------------------------------------------------------------------
_KEY_NAME_MAP: dict[Key, str] = {
    Key.alt_r: "right alt",
    Key.alt_l: "left alt",
    Key.ctrl_r: "right ctrl",
    Key.ctrl_l: "left ctrl",
    Key.shift_r: "right shift",
    Key.shift_l: "left shift",
    Key.scroll_lock: "scroll lock",
    Key.pause: "pause",
    Key.insert: "insert",
    Key.f13: "f13",
    Key.f14: "f14",
}

# Modifier keys whose release we attempt before text injection.
_MODIFIER_KEYS: tuple[Key, ...] = (
    Key.alt,
    Key.alt_r,
    Key.ctrl,
    Key.ctrl_l,
    Key.ctrl_r,
    Key.shift,
    Key.shift_l,
    Key.shift_r,
)

# ---------------------------------------------------------------------------
# ctypes structures — defined at module level so they are available as soon
# as the module is imported (before WindowsBackend.__init__ runs).
#
# The INPUT union MUST include all three sub-structures so the compiler
# pads it to the correct size (40 bytes on x64).  See:
# https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-input
# ---------------------------------------------------------------------------


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          ctypes.c_long),
        ("dy",          ctypes.c_long),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         ctypes.wintypes.WORD),
        ("wScan",       ctypes.wintypes.WORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg",    ctypes.wintypes.DWORD),
        ("wParamL", ctypes.wintypes.WORD),
        ("wParamH", ctypes.wintypes.WORD),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("mi", MOUSEINPUT),
            ("hi", HARDWAREINPUT),
        ]

    _fields_ = [
        ("type",   ctypes.wintypes.DWORD),
        ("_input", _INPUT),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


# ---------------------------------------------------------------------------
# Module-level helpers for building INPUT records
# ---------------------------------------------------------------------------

def _extra_ptr() -> ctypes.POINTER(ctypes.c_ulong):
    """Return a stable pointer to a zeroed c_ulong for dwExtraInfo."""
    return ctypes.pointer(ctypes.c_ulong(0))


def _make_key_input(vk: int, flags: int = 0) -> INPUT:
    """Build an INPUT record for a virtual-key keystroke event."""
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp._input.ki.wVk = vk
    inp._input.ki.wScan = 0
    inp._input.ki.dwFlags = flags
    inp._input.ki.time = 0
    inp._input.ki.dwExtraInfo = _extra_ptr()
    return inp


def _make_unicode_input(char_code: int, flags: int = 0) -> INPUT:
    """Build an INPUT record for a Unicode character injection.

    wVk must be 0 when KEYEVENTF_UNICODE is set; the Unicode code point is
    placed in wScan.  This bypasses the keyboard layout entirely.
    """
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp._input.ki.wVk = 0
    inp._input.ki.wScan = char_code
    inp._input.ki.dwFlags = KEYEVENTF_UNICODE | flags
    inp._input.ki.time = 0
    inp._input.ki.dwExtraInfo = _extra_ptr()
    return inp


def _translate_pynput_key(key: Key | KeyCode) -> tuple[str, int]:
    """Return (key_name, vk_code) from a raw pynput key object.

    For special Key members the name comes from *_KEY_NAME_MAP* with a
    fallback to the member's name attribute.  For KeyCode the printable
    character is preferred; when absent the string representation is used.
    vk_code is sourced from ``.vk`` where available, otherwise 0.
    """
    if isinstance(key, Key):
        name = _KEY_NAME_MAP.get(key, key.name)
        vk: int = getattr(key.value, "vk", None) or 0
        return name, vk

    # KeyCode (regular character or a raw vk code with no character)
    char: Optional[str] = getattr(key, "char", None)
    vk = getattr(key, "vk", None) or 0

    if char is not None:
        return char, vk

    # Fall back to pynput's own string representation
    return str(key), vk


# ---------------------------------------------------------------------------
# WindowsBackend
# ---------------------------------------------------------------------------


class WindowsBackend(PlatformBackend):
    """Windows-specific platform backend using ctypes + pynput.

    Text injection uses Win32 SendInput for best Unicode support.
    Keyboard hooks use pynput's Listener (WH_KEYBOARD_LL) which is read-only
    and does not intercept synthetic keystrokes — no unhook/rehook needed.
    """

    def __init__(self) -> None:
        self._user32 = ctypes.windll.user32

        # Wire up the SendInput signature so ctypes can validate arguments and
        # return the UINT result correctly.
        self._user32.SendInput.argtypes = [
            ctypes.wintypes.UINT,
            ctypes.POINTER(INPUT),
            ctypes.c_int,
        ]
        self._user32.SendInput.restype = ctypes.wintypes.UINT

        # The currently active pynput Listener (or None).
        self._listener: Optional[Listener] = None

        log.debug(
            "WindowsBackend initialised — INPUT size = %d bytes",
            ctypes.sizeof(INPUT),
        )

    # ------------------------------------------------------------------
    # Internal SendInput helpers
    # ------------------------------------------------------------------

    def _send_inputs(self, inputs: list[INPUT]) -> int:
        """Send a list of INPUT records via SendInput.

        Returns the number of events successfully inserted into the input
        stream.  A return value less than len(inputs) indicates that some
        events were blocked (e.g. by UIPI).
        """
        count = len(inputs)
        arr = (INPUT * count)(*inputs)
        result = self._user32.SendInput(count, arr, ctypes.sizeof(INPUT))
        if result != count:
            log.warning(
                "SendInput: requested %d events, inserted %d "
                "(UIPI block or struct size mismatch?)",
                count,
                result,
            )
        return result

    # ------------------------------------------------------------------
    # PlatformBackend interface
    # ------------------------------------------------------------------

    def type_text(self, text: str) -> int:
        """Inject *text* into the focused window via Unicode SendInput events.

        Modifier keys are released first to eliminate AltGr / sticky-key
        artefacts.  Each character is sent as a separate key-down / key-up
        pair with a 5 ms pause between characters to give the target
        application time to process each event.

        Returns the cumulative count of SendInput events successfully queued.
        """
        self.release_modifier_keys()
        time.sleep(0.05)  # let Windows process the modifier releases

        total_sent = 0
        for char in text:
            code = ord(char)
            inputs = [
                _make_unicode_input(code),                       # key down
                _make_unicode_input(code, KEYEVENTF_KEYUP),      # key up
            ]
            total_sent += self._send_inputs(inputs)
            time.sleep(0.005)  # 5 ms between characters

        log.info(
            "type_text: sent %d SendInput events for %d characters",
            total_sent,
            len(text),
        )
        return total_sent

    def install_key_hook(self, callback: Callable) -> Listener:
        """Install a global keyboard hook using a ``pynput`` Listener.

        The *callback* is called as ``callback(event_type, key_name,
        scan_code)`` where *event_type* is ``'down'`` or ``'up'``.

        Synthetic (injected) keystrokes from SendInput are automatically
        ignored so text injection doesn't trigger the hotkey callback.

        Returns the started ``Listener`` instance.
        """

        def _on_press(key: Key | KeyCode, injected: bool = False) -> None:
            if injected:
                return  # ignore our own SendInput keystrokes
            try:
                name, vk_code = _translate_pynput_key(key)
                callback("down", name, vk_code)
            except Exception as exc:
                log.debug("WindowsBackend: error in on_press handler: %s", exc)

        def _on_release(key: Key | KeyCode, injected: bool = False) -> None:
            if injected:
                return  # ignore our own SendInput keystrokes
            try:
                name, vk_code = _translate_pynput_key(key)
                callback("up", name, vk_code)
            except Exception as exc:
                log.debug("WindowsBackend: error in on_release handler: %s", exc)

        listener = Listener(on_press=_on_press, on_release=_on_release)
        listener.start()
        self._listener = listener
        log.info("pynput Listener installed (Windows)")
        return listener

    def remove_key_hook(self, handle: Any = None) -> None:
        """Stop the pynput Listener identified by *handle* (or the stored one).

        If *handle* is ``None``, the most recently installed listener is
        stopped.  Stopping an already-stopped listener is a no-op.
        """
        target: Optional[Listener] = handle if handle is not None else self._listener

        if target is None:
            log.debug("WindowsBackend.remove_key_hook: no active listener to remove")
            return

        try:
            target.stop()
            log.debug("WindowsBackend: pynput Listener stopped")
        except Exception as exc:
            log.warning("WindowsBackend.remove_key_hook: error stopping listener: %s", exc)
        finally:
            if target is self._listener:
                self._listener = None

    def reinstall_key_hook(self, callback: Callable) -> Listener:
        """Stop any existing listener and install a new one.

        Returns the new ``Listener`` handle.
        """
        self.remove_key_hook()
        return self.install_key_hook(callback)

    def get_foreground_window_title(self) -> str:
        """Return the title bar text of the currently focused window.

        Returns an empty string if the foreground window cannot be determined
        or the title cannot be read.
        """
        try:
            hwnd = self._user32.GetForegroundWindow()
            if not hwnd:
                return ""
            buf = ctypes.create_unicode_buffer(256)
            self._user32.GetWindowTextW(hwnd, buf, 256)
            return buf.value
        except Exception as exc:
            log.warning("get_foreground_window_title failed: %s", exc)
            return ""

    def pre_injection_cleanup(self) -> None:
        """Dismiss any Alt-triggered menus and refocus the text area.

        Sequence:
        1. Send Escape key-down/up to close any menu bar that was activated
           by the Right Alt / AltGr key release.
        2. Read the current cursor position with GetCursorPos.
        3. Send a mouse left-click at that position so focus returns to the
           text widget underneath the cursor (in case Escape moved focus to
           the menu bar or title bar).

        Small sleep delays are inserted between steps to give Windows time
        to process each event before the next one arrives.
        """
        # Step 1 — dismiss Alt menu with Escape
        esc_inputs = [
            _make_key_input(VK_ESCAPE),
            _make_key_input(VK_ESCAPE, KEYEVENTF_KEYUP),
        ]
        self._send_inputs(esc_inputs)
        time.sleep(0.05)

        # Step 2 — get cursor position
        pt = POINT()
        self._user32.GetCursorPos(ctypes.byref(pt))
        log.debug("pre_injection_cleanup: cursor at (%d, %d)", pt.x, pt.y)

        # Step 3 — click at cursor position to refocus the text area
        click_down = INPUT()
        click_down.type = INPUT_MOUSE
        click_down._input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN

        click_up = INPUT()
        click_up.type = INPUT_MOUSE
        click_up._input.mi.dwFlags = MOUSEEVENTF_LEFTUP

        self._send_inputs([click_down, click_up])
        time.sleep(0.1)

    def release_modifier_keys(self) -> None:
        """Send key-up events for all common modifier keys.

        Targets Right Alt, Left Alt, generic Alt, Control, and Shift.
        This prevents AltGr / sticky modifier artefacts from corrupting
        injected Unicode characters.
        """
        modifier_releases = [
            _make_key_input(VK_RMENU,   KEYEVENTF_KEYUP),
            _make_key_input(VK_LMENU,   KEYEVENTF_KEYUP),
            _make_key_input(VK_MENU,    KEYEVENTF_KEYUP),
            _make_key_input(VK_CONTROL, KEYEVENTF_KEYUP),
            _make_key_input(VK_SHIFT,   KEYEVENTF_KEYUP),
        ]
        sent = self._send_inputs(modifier_releases)
        log.debug("release_modifier_keys: sent %d key-up events", sent)

    @property
    def needs_unhook_for_injection(self) -> bool:
        """False — pynput's Listener is read-only and does not block synthetic keys.

        Unlike the ``keyboard`` library, pynput on Windows uses a WH_KEYBOARD_LL
        hook that observes but does not intercept.  The ``injected`` flag in the
        callback lets us ignore our own SendInput events, so no hook juggling
        is needed.
        """
        return False

    def get_hotkey_names(self, hotkey: str) -> set:
        """Return the full set of name strings that identify *hotkey*.

        Right Alt is reported by pynput as 'right alt' (via our _KEY_NAME_MAP).
        We also include legacy aliases for compatibility.
        """
        hotkey_lower = hotkey.lower()
        if hotkey_lower in _RIGHT_ALT_NAMES:
            return set(_RIGHT_ALT_NAMES)
        return {hotkey_lower}

    def get_hotkey_scan_codes(self, hotkey: str) -> set:
        """Return VK codes that identify *hotkey*.

        pynput on Windows uses virtual key codes rather than hardware scan
        codes.  For Right Alt, returns {165} (VK_RMENU).
        For other keys, returns an empty set (name matching is sufficient).
        """
        hotkey_lower = hotkey.lower()
        if hotkey_lower in _RIGHT_ALT_NAMES:
            return set(_RIGHT_ALT_VK_CODES)
        return set()
