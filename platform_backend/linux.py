"""Linux platform backend for Whisper Walkie.

Uses pynput for keyboard hooking and text injection (X11 via Xlib / XRecord).
Falls back to xdotool or wtype for text injection when pynput fails.
Does NOT use the `keyboard` library, which requires root on Linux.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from typing import Any, Callable, Optional

from pynput import keyboard as pynput_keyboard
from pynput.keyboard import Key, KeyCode, Listener

from .base import PlatformBackend

log = logging.getLogger("walkie")

# ---------------------------------------------------------------------------
# Key name mapping for special pynput Key enum members that differ from the
# normalised names used by the rest of the application.
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


def _translate_pynput_key(key: Key | KeyCode) -> tuple[str, int]:
    """Return (key_name, scan_code) from a raw pynput key object.

    For special Key members the name comes from *_KEY_NAME_MAP* with a
    fallback to the member's name attribute (e.g. ``Key.space`` -> ``'space'``).
    For KeyCode the printable character is preferred; when absent the
    string representation is used.  scan_code is sourced from ``.vk`` where
    available, otherwise 0.
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

    # Fall back to pynput's own string representation, e.g. '<65437>'
    return str(key), vk


class LinuxBackend(PlatformBackend):
    """Platform backend for Linux (X11 and limited Wayland support).

    Keyboard hooking is implemented with ``pynput``'s Listener, which uses
    XRecord on X11 — a purely observational mechanism that does not intercept
    or block synthetic keyboard events.  On Wayland, pynput may fall back to
    reading ``/dev/input/`` which requires elevated permissions; a warning is
    emitted if that is detected.

    Text injection primary path is ``pynput.keyboard.Controller().type()``.
    The xdotool / wtype fallbacks are used when the primary path raises an
    exception.
    """

    def __init__(self) -> None:
        session_type: str = os.environ.get("XDG_SESSION_TYPE", "").lower()
        self._is_wayland: bool = session_type == "wayland"

        if self._is_wayland:
            pynput_backend = os.environ.get(
                "PYNPUT_BACKEND_KEYBOARD",
                os.environ.get("PYNPUT_BACKEND", "xorg"),
            )
            if pynput_backend == "uinput":
                # Verify the user has /dev/input/ access
                import grp
                try:
                    input_gid = grp.getgrnam("input").gr_gid
                    user_groups = os.getgroups()
                    if input_gid not in user_groups:
                        log.warning(
                            "LinuxBackend: Wayland session with uinput backend, but user "
                            "is not in the 'input' group.  Hotkey detection will likely fail.  "
                            "Run: sudo usermod -aG input $USER  (then log out and back in)."
                        )
                except KeyError:
                    log.warning(
                        "LinuxBackend: 'input' group not found on this system."
                    )
                log.info(
                    "LinuxBackend: Wayland session detected, using uinput backend "
                    "for keyboard hooking.  Active-window title is not available."
                )
            else:
                log.warning(
                    "LinuxBackend: Wayland session detected but using '%s' backend.  "
                    "Global keyboard hooks will NOT work.  Set PYNPUT_BACKEND=uinput "
                    "and ensure the 'evdev' package is available.",
                    pynput_backend,
                )

        # Probe for optional CLI helpers at startup so we log only once.
        self._xdotool: Optional[str] = shutil.which("xdotool")
        if self._xdotool is None:
            log.warning(
                "LinuxBackend: xdotool not found.  "
                "Text injection and window-title lookup will fall back to "
                "pynput only.  Install xdotool for best compatibility."
            )

        self._wtype: Optional[str] = shutil.which("wtype") if self._is_wayland else None
        if self._is_wayland and self._wtype is None:
            log.warning(
                "LinuxBackend: wtype not found.  "
                "On Wayland, text injection may fail if pynput is also "
                "unavailable.  Install wtype as a fallback."
            )

        # The currently active pynput Listener (or None).
        self._listener: Optional[Listener] = None

    # ------------------------------------------------------------------
    # PlatformBackend interface
    # ------------------------------------------------------------------

    def type_text(self, text: str) -> int:
        """Inject *text* into the focused window.

        On Wayland the order is wtype → xdotool → pynput because xdotool
        silently fails on native Wayland windows (returns exit 0 but only
        reaches XWayland clients) and pynput needs /dev/uinput write access.
        On X11 the order is pynput → xdotool.

        Returns the number of characters successfully injected (``len(text)``
        on success, ``0`` on complete failure).
        """
        if not text:
            return 0

        if self._is_wayland:
            return self._type_text_wayland(text)
        return self._type_text_x11(text)

    def _type_text_wayland(self, text: str) -> int:
        """Wayland injection: wtype → xdotool → pynput."""

        # --- Primary on Wayland: wtype ---
        if self._wtype is not None:
            try:
                result = subprocess.run(
                    [self._wtype, "--", text],
                    timeout=2,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    log.debug(
                        "LinuxBackend.type_text: injected %d chars via wtype", len(text)
                    )
                    return len(text)
                log.warning(
                    "LinuxBackend.type_text: wtype exited %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
            except Exception as exc:
                log.warning("LinuxBackend.type_text: wtype failed (%s)", exc)

        # --- Fallback 1: xdotool (works for XWayland windows) ---
        if self._xdotool is not None:
            try:
                result = subprocess.run(
                    [self._xdotool, "type", "--clearmodifiers", "--", text],
                    timeout=2,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    log.debug(
                        "LinuxBackend.type_text: injected %d chars via xdotool", len(text)
                    )
                    return len(text)
                log.warning(
                    "LinuxBackend.type_text: xdotool exited %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
            except Exception as exc:
                log.warning("LinuxBackend.type_text: xdotool failed (%s)", exc)

        # --- Fallback 2: pynput (needs /dev/uinput write access) ---
        try:
            controller = pynput_keyboard.Controller()
            controller.type(text)
            log.debug("LinuxBackend.type_text: injected %d chars via pynput", len(text))
            return len(text)
        except Exception as exc:
            log.warning("LinuxBackend.type_text: pynput failed (%s)", exc)

        log.error("LinuxBackend.type_text: all injection methods failed for text of length %d", len(text))
        return 0

    def _type_text_x11(self, text: str) -> int:
        """X11 injection: pynput → xdotool."""

        # --- Primary on X11: pynput ---
        try:
            controller = pynput_keyboard.Controller()
            controller.type(text)
            log.debug("LinuxBackend.type_text: injected %d chars via pynput", len(text))
            return len(text)
        except Exception as exc:
            log.warning("LinuxBackend.type_text: pynput failed (%s), trying fallback", exc)

        # --- Fallback: xdotool ---
        if self._xdotool is not None:
            try:
                result = subprocess.run(
                    [self._xdotool, "type", "--clearmodifiers", "--", text],
                    timeout=2,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    log.debug(
                        "LinuxBackend.type_text: injected %d chars via xdotool", len(text)
                    )
                    return len(text)
                log.warning(
                    "LinuxBackend.type_text: xdotool exited %d: %s",
                    result.returncode,
                    result.stderr.strip(),
                )
            except Exception as exc:
                log.warning("LinuxBackend.type_text: xdotool failed (%s)", exc)

        log.error("LinuxBackend.type_text: all injection methods failed for text of length %d", len(text))
        return 0

    def install_key_hook(self, callback: Callable) -> Listener:
        """Install a global keyboard hook using a ``pynput`` Listener.

        The *callback* is called as ``callback(event_type, key_name,
        scan_code)`` where *event_type* is ``'down'`` or ``'up'``.

        On X11, pynput uses XRecord which is a non-intercepting, observer-only
        mechanism — no root privileges are required.  On Wayland, pynput may
        need access to ``/dev/input/`` (typically requires the user to be in
        the ``input`` group or to run as root); a warning is emitted if
        pynput raises a ``PermissionError``.

        Returns the started ``Listener`` instance.
        """

        def _on_press(key: Key | KeyCode) -> None:
            try:
                name, scan_code = _translate_pynput_key(key)
                callback("down", name, scan_code)
            except Exception as exc:
                log.debug("LinuxBackend: error in on_press handler: %s", exc)

        def _on_release(key: Key | KeyCode) -> None:
            try:
                name, scan_code = _translate_pynput_key(key)
                callback("up", name, scan_code)
            except Exception as exc:
                log.debug("LinuxBackend: error in on_release handler: %s", exc)

        try:
            listener = Listener(on_press=_on_press, on_release=_on_release)
            listener.start()
            self._listener = listener
            log.debug("LinuxBackend: pynput Listener started")
            return listener
        except PermissionError as exc:
            log.warning(
                "LinuxBackend: PermissionError starting pynput Listener (%s).  "
                "On Wayland, /dev/input/ access may be required.  "
                "Add your user to the 'input' group or run with elevated privileges.",
                exc,
            )
            raise
        except Exception as exc:
            log.error("LinuxBackend: failed to start pynput Listener: %s", exc)
            raise

    def remove_key_hook(self, handle: Any = None) -> None:
        """Stop the pynput Listener identified by *handle* (or the stored one).

        If *handle* is ``None``, the most recently installed listener is
        stopped.  Stopping an already-stopped listener is a no-op.
        """
        target: Optional[Listener] = handle if handle is not None else self._listener

        if target is None:
            log.debug("LinuxBackend.remove_key_hook: no active listener to remove")
            return

        try:
            target.stop()
            log.debug("LinuxBackend: pynput Listener stopped")
        except Exception as exc:
            log.warning("LinuxBackend.remove_key_hook: error stopping listener: %s", exc)
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
        """Return the title of the currently focused window.

        Uses ``xdotool getactivewindow getwindowname``.  Returns an empty
        string on Wayland (not supported), when xdotool is absent, or when
        the subprocess call fails.
        """
        if self._is_wayland:
            log.debug(
                "LinuxBackend.get_foreground_window_title: not available on Wayland"
            )
            return ""

        if self._xdotool is None:
            return ""

        try:
            result = subprocess.run(
                [self._xdotool, "getactivewindow", "getwindowname"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            log.debug(
                "LinuxBackend.get_foreground_window_title: xdotool exited %d: %s",
                result.returncode,
                result.stderr.strip(),
            )
        except FileNotFoundError:
            log.debug("LinuxBackend.get_foreground_window_title: xdotool not found")
        except Exception as exc:
            log.debug("LinuxBackend.get_foreground_window_title: %s", exc)

        return ""

    def pre_injection_cleanup(self) -> None:
        """No-op on Linux.

        Unlike Windows, Alt key release does not typically trigger menu bars
        in GTK/Qt applications under GNOME or KDE, so no pre-injection
        dismissal is needed.
        """

    @property
    def needs_unhook_for_injection(self) -> bool:
        """Return ``False``.

        pynput's Listener on X11 relies on XRecord, which is a passive,
        read-only extension.  It does NOT intercept synthetic keyboard events
        generated by ``pynput.keyboard.Controller`` or ``xdotool``, so there
        is no need to uninstall the hook before injecting text.
        """
        return False

    def release_modifier_keys(self) -> None:
        """Release common modifier keys via ``pynput``'s Controller.

        Silently ignores any key that is already released or otherwise
        raises an exception.
        """
        controller = pynput_keyboard.Controller()
        for key in _MODIFIER_KEYS:
            try:
                controller.release(key)
            except Exception:
                # Key was already released or not supported on this layout.
                pass
        log.debug("LinuxBackend.release_modifier_keys: modifier release attempted")

    def get_hotkey_names(self, hotkey: str) -> set[str]:
        """Return the set of names that can identify *hotkey* on Linux.

        Right Alt (AltGr) has several common aliases across keyboard layouts
        and tools, so all are returned for that key.  All other hotkeys are
        returned as a single lower-cased name.

        Examples::

            backend.get_hotkey_names('right alt')
            # -> {'right alt', 'alt_r', 'alt gr', 'altgr'}

            backend.get_hotkey_names('ctrl')
            # -> {'ctrl'}
        """
        normalised = hotkey.lower()
        if normalised == "right alt":
            return {"right alt", "alt_r", "alt gr", "altgr", "iso_level3_shift"}
        return {normalised}

    def get_hotkey_scan_codes(self, hotkey: str) -> set[int]:
        """Return an empty set.

        pynput identifies keys by name on Linux; scan-code-based matching is
        not required for this backend.
        """
        return set()
