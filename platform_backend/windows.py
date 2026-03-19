"""Windows platform backend for Whisper Walkie.

Implements PlatformBackend using the Win32 API (via ctypes) for keystroke
injection and the `keyboard` library for global key hooks.

Key design decisions that match the original main.py behaviour:

- The INPUT union includes all three input types (KEYBDINPUT, MOUSEINPUT,
  HARDWAREINPUT) so ctypes.sizeof(INPUT) == 40 bytes on x64.  Without
  MOUSEINPUT the struct is too small and SendInput silently returns 0.

- Unicode characters are injected one at a time with KEYEVENTF_UNICODE so
  no clipboard is needed and no Ctrl+V modifier interaction occurs.

- Stuck modifier keys (right/left/generic Alt, Ctrl, Shift) are released
  with key-up events before every text injection to prevent AltGr artefacts.

- The `keyboard` library intercepts synthetic SendInput keystrokes when its
  low-level hook is active, so the hook must be removed before injection
  and re-installed afterwards (needs_unhook_for_injection = True).
"""

import ctypes
import ctypes.wintypes
import logging
import time
from typing import Any, Callable

import keyboard

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

# Right Alt / AltGr scan codes that the keyboard library may report
_RIGHT_ALT_NAMES: frozenset = frozenset({'right alt', 'alt gr', 'altgr'})
_RIGHT_ALT_SCANS: frozenset = frozenset({56, 541, 57400})

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


# ---------------------------------------------------------------------------
# WindowsBackend
# ---------------------------------------------------------------------------


class WindowsBackend(PlatformBackend):
    """Windows-specific platform backend using ctypes + the keyboard library."""

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

        # Keep a reference to the last wrapper passed to keyboard.hook() so
        # reinstall_key_hook() can reuse it without the caller having to
        # supply it again.
        self._current_callback_wrapper: Callable | None = None

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

    def install_key_hook(self, callback: Callable) -> Any:
        """Install a global low-level keyboard hook via the keyboard library.

        *callback* is called as ``callback(event_type, key_name, scan_code)``
        where *event_type* is ``'down'`` or ``'up'``, *key_name* is the
        lower-cased key name string (may be empty), and *scan_code* is the
        hardware scan code integer (or ``None`` if unavailable).

        Returns the hook handle (the wrapper function) so the caller can
        store it for later reinstallation.
        """

        def callback_wrapper(event: keyboard.KeyboardEvent) -> None:
            event_type: str = event.event_type  # 'down' or 'up'
            key_name: str = (event.name or "").lower()
            scan_code: int | None = getattr(event, "scan_code", None)
            try:
                callback(event_type, key_name, scan_code)
            except Exception as exc:
                log.error("Key hook callback raised an exception: %s", exc)

        self._current_callback_wrapper = callback_wrapper
        handle = keyboard.hook(callback_wrapper, suppress=False)
        log.info("keyboard.hook() installed")
        return handle

    def remove_key_hook(self, handle: Any = None) -> None:
        """Remove all active keyboard hooks installed by the keyboard library.

        The *handle* parameter is accepted for API compatibility but is not
        used — ``keyboard.unhook_all()`` is the safest approach because it
        clears all hooks registered within this process, including any that
        were re-installed internally.
        """
        try:
            keyboard.unhook_all()
            log.info("keyboard.unhook_all() complete")
        except Exception as exc:
            log.warning("Failed to unhook keyboard: %s", exc)

    def reinstall_key_hook(self, callback: Callable) -> Any:
        """Re-install the keyboard hook after it was removed for injection.

        Uses the same wrapper created in the most recent call to
        ``install_key_hook`` so the normalised callback signature is
        preserved.  If no wrapper exists yet (first call), delegates to
        ``install_key_hook`` to build one.
        """
        if self._current_callback_wrapper is None:
            log.debug(
                "reinstall_key_hook: no existing wrapper, calling install_key_hook"
            )
            return self.install_key_hook(callback)

        handle = keyboard.hook(self._current_callback_wrapper, suppress=False)
        log.info("keyboard.hook() re-installed")
        return handle

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
        """True — the keyboard library's hook intercepts synthetic keystrokes.

        When the hook is active, SendInput keystrokes are captured by the
        low-level hook callback before they reach the target window, so the
        text never actually arrives.  The hook must be removed before calling
        type_text() and reinstalled afterwards.
        """
        return True

    def get_hotkey_names(self, hotkey: str) -> set:
        """Return the full set of name strings that identify *hotkey*.

        Right Alt is reported inconsistently by the keyboard library across
        different keyboard layouts and Windows versions — it may appear as
        ``'right alt'``, ``'alt gr'``, or ``'altgr'``.  When *hotkey* is any
        of those three variants all three are included in the returned set so
        the caller can match any of them.

        For all other keys the set contains only the lower-cased hotkey name.
        """
        hotkey_lower = hotkey.lower()
        if hotkey_lower in _RIGHT_ALT_NAMES:
            return set(_RIGHT_ALT_NAMES)
        return {hotkey_lower}

    def get_hotkey_scan_codes(self, hotkey: str) -> set:
        """Return the full set of scan codes that identify *hotkey*.

        Scan codes are looked up via ``keyboard.key_to_scan_codes()``.  For
        Right Alt variants the three known AltGr scan codes (56, 541, 57400)
        are also included because different keyboards and virtualisation layers
        may report different values.

        Returns an empty set if the hotkey name is not recognised.
        """
        hotkey_lower = hotkey.lower()
        scan_codes: set = set()

        try:
            scan_codes.update(keyboard.key_to_scan_codes(hotkey))
        except ValueError:
            log.debug(
                "get_hotkey_scan_codes: keyboard library does not recognise %r",
                hotkey,
            )

        if hotkey_lower in _RIGHT_ALT_NAMES:
            scan_codes.update(_RIGHT_ALT_SCANS)

        return scan_codes
