import os
import platform
import logging

log = logging.getLogger("walkie")


def _configure_pynput_backend() -> None:
    """Select the correct pynput backend before it is imported.

    On Wayland, pynput's default ``xorg`` backend uses XRecord which is
    completely non-functional — the listener thread starts but silently
    receives zero key events.  The ``uinput`` backend reads ``/dev/input/``
    via ``evdev`` and works correctly on Wayland (requires the user to be
    in the ``input`` group).

    This MUST be called before any ``import pynput`` statement.
    """
    if platform.system() != "Linux":
        return
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session_type == "wayland":
        os.environ.setdefault("PYNPUT_BACKEND", "uinput")
        os.environ.setdefault("PYNPUT_BACKEND_KEYBOARD", "uinput")
        os.environ.setdefault("PYNPUT_BACKEND_MOUSE", "uinput")


def get_backend():
    """Factory: returns the appropriate PlatformBackend for the current OS."""
    system = platform.system()

    if system == "Windows":
        from .windows import WindowsBackend
        return WindowsBackend()
    elif system == "Darwin":
        from .macos import MacOSBackend
        return MacOSBackend()
    elif system == "Linux":
        _configure_pynput_backend()
        from .linux import LinuxBackend
        return LinuxBackend()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
