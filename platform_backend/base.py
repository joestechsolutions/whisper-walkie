from abc import ABC, abstractmethod
from typing import Callable, Optional, Any


class PlatformBackend(ABC):
    """Abstract interface for platform-specific operations."""

    @abstractmethod
    def type_text(self, text: str) -> int:
        """Inject text into the focused window via synthetic keystrokes.
        Returns number of characters successfully injected."""
        ...

    @abstractmethod
    def install_key_hook(self, callback: Callable) -> Any:
        """Install a global keyboard hook.
        callback receives (event_type: str, key_name: str, scan_code: int)
        where event_type is 'down' or 'up'.
        Returns a handle that can be passed to remove_key_hook."""
        ...

    @abstractmethod
    def remove_key_hook(self, handle: Any = None) -> None:
        """Remove the keyboard hook. If handle is None, remove all hooks."""
        ...

    @abstractmethod
    def reinstall_key_hook(self, callback: Callable) -> Any:
        """Reinstall the keyboard hook after removal.
        Returns new handle."""
        ...

    @abstractmethod
    def get_foreground_window_title(self) -> str:
        """Get the title of the currently focused window.
        Returns empty string if unavailable."""
        ...

    @abstractmethod
    def pre_injection_cleanup(self) -> None:
        """Platform-specific cleanup before injecting text.
        On Windows: sends Escape + mouse click to dismiss Alt menus.
        On other platforms: no-op."""
        ...

    @property
    @abstractmethod
    def needs_unhook_for_injection(self) -> bool:
        """Whether the keyboard hook must be removed before injecting text.
        True on Windows (keyboard lib intercepts synthetic keys),
        False on macOS/Linux (pynput doesn't intercept)."""
        ...

    @abstractmethod
    def release_modifier_keys(self) -> None:
        """Release any stuck modifier keys (Alt, Ctrl, Shift).
        Called before text injection."""
        ...

    def get_hotkey_names(self, hotkey: str) -> set:
        """Get all possible names for a hotkey on this platform.
        Override per-platform for special handling (e.g., Right Alt / AltGr on Windows)."""
        return {hotkey.lower()}

    def get_hotkey_scan_codes(self, hotkey: str) -> set:
        """Get all possible scan codes for a hotkey on this platform.
        Override per-platform for special handling."""
        return set()
