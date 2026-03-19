import platform
import logging

log = logging.getLogger("walkie")


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
        from .linux import LinuxBackend
        return LinuxBackend()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
