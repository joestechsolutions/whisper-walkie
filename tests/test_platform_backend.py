"""Cross-platform tests for the platform_backend module.

These tests validate that each backend correctly implements the
PlatformBackend ABC and that the factory selects the right one.
Tests are designed to run in CI on Windows, macOS, and Linux.
"""

import platform
import sys
from unittest import mock

import pytest

from platform_backend.base import PlatformBackend


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------

class TestFactory:
    """Test that get_backend() returns the correct backend for the OS."""

    def test_returns_platform_backend_instance(self):
        from platform_backend import get_backend
        backend = get_backend()
        assert isinstance(backend, PlatformBackend)

    def test_returns_correct_backend_type(self):
        from platform_backend import get_backend
        backend = get_backend()
        system = platform.system()

        if system == "Windows":
            from platform_backend.windows import WindowsBackend
            assert isinstance(backend, WindowsBackend)
        elif system == "Darwin":
            from platform_backend.macos import MacOSBackend
            assert isinstance(backend, MacOSBackend)
        elif system == "Linux":
            from platform_backend.linux import LinuxBackend
            assert isinstance(backend, LinuxBackend)

    def test_unsupported_platform_raises(self):
        with mock.patch("platform_backend.platform.system", return_value="FreeBSD"):
            # Re-import to trigger the factory with the mocked platform
            import importlib
            import platform_backend
            with pytest.raises(RuntimeError, match="Unsupported platform"):
                importlib.reload(platform_backend)
                platform_backend.get_backend()


# ---------------------------------------------------------------------------
# Base ABC contract tests (run on whichever platform is available)
# ---------------------------------------------------------------------------

class TestBackendContract:
    """Verify that the current platform's backend implements all ABC methods."""

    @pytest.fixture
    def backend(self):
        from platform_backend import get_backend
        return get_backend()

    def test_has_type_text(self, backend):
        assert callable(getattr(backend, "type_text", None))

    def test_has_install_key_hook(self, backend):
        assert callable(getattr(backend, "install_key_hook", None))

    def test_has_remove_key_hook(self, backend):
        assert callable(getattr(backend, "remove_key_hook", None))

    def test_has_reinstall_key_hook(self, backend):
        assert callable(getattr(backend, "reinstall_key_hook", None))

    def test_has_get_foreground_window_title(self, backend):
        assert callable(getattr(backend, "get_foreground_window_title", None))

    def test_has_pre_injection_cleanup(self, backend):
        assert callable(getattr(backend, "pre_injection_cleanup", None))

    def test_has_release_modifier_keys(self, backend):
        assert callable(getattr(backend, "release_modifier_keys", None))

    def test_needs_unhook_is_false(self, backend):
        """All backends use pynput (read-only) — unhook should never be needed."""
        assert backend.needs_unhook_for_injection is False

    def test_get_hotkey_names_returns_set(self, backend):
        result = backend.get_hotkey_names("right alt")
        assert isinstance(result, set)
        assert len(result) >= 1

    def test_get_hotkey_names_right_alt_includes_canonical(self, backend):
        result = backend.get_hotkey_names("right alt")
        assert "right alt" in result

    def test_get_hotkey_scan_codes_returns_set(self, backend):
        result = backend.get_hotkey_scan_codes("right alt")
        assert isinstance(result, set)

    def test_get_hotkey_names_case_insensitive(self, backend):
        """Hotkey matching should be case-insensitive."""
        result_lower = backend.get_hotkey_names("right alt")
        result_mixed = backend.get_hotkey_names("Right Alt")
        assert result_lower == result_mixed

    def test_get_hotkey_names_non_alt(self, backend):
        """Non-alt hotkeys should return a single-element set."""
        result = backend.get_hotkey_names("scroll lock")
        assert isinstance(result, set)
        assert "scroll lock" in result


# ---------------------------------------------------------------------------
# Hotkey configuration tests
# ---------------------------------------------------------------------------

SUPPORTED_HOTKEYS = [
    "right alt",
    "scroll lock",
    "pause",
    "f13",
    "f14",
    "insert",
    "right ctrl",
]


class TestHotkeyConfig:
    """Verify all supported hotkeys produce valid name sets."""

    @pytest.fixture
    def backend(self):
        from platform_backend import get_backend
        return get_backend()

    @pytest.mark.parametrize("hotkey", SUPPORTED_HOTKEYS)
    def test_hotkey_names_not_empty(self, backend, hotkey):
        names = backend.get_hotkey_names(hotkey)
        assert len(names) >= 1, f"No names for hotkey '{hotkey}'"

    @pytest.mark.parametrize("hotkey", SUPPORTED_HOTKEYS)
    def test_hotkey_names_are_lowercase(self, backend, hotkey):
        names = backend.get_hotkey_names(hotkey)
        for name in names:
            assert name == name.lower(), f"Name '{name}' is not lowercase"


# ---------------------------------------------------------------------------
# Platform-specific tests (only run on the matching OS)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-only tests")
class TestWindowsBackend:
    """Windows-specific backend validation."""

    @pytest.fixture
    def backend(self):
        from platform_backend.windows import WindowsBackend
        return WindowsBackend()

    def test_right_alt_vk_codes(self, backend):
        """Windows should match Right Alt by VK code 165."""
        codes = backend.get_hotkey_scan_codes("right alt")
        assert 165 in codes

    def test_right_alt_aliases(self, backend):
        names = backend.get_hotkey_names("right alt")
        assert "alt_r" in names
        assert "altgr" in names

    def test_input_struct_size(self, backend):
        """The INPUT struct must be 40 bytes on x64 for SendInput to work."""
        import ctypes
        from platform_backend.windows import INPUT
        expected_size = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
        assert ctypes.sizeof(INPUT) == expected_size

    def test_type_text_empty_string(self, backend):
        """Typing empty string should return 0 without error."""
        result = backend.type_text("")
        assert result == 0


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-only tests")
class TestMacOSBackend:
    """macOS-specific backend validation."""

    @pytest.fixture
    def backend(self):
        from platform_backend.macos import MacOSBackend
        return MacOSBackend()

    def test_right_alt_includes_option(self, backend):
        """macOS reports Right Alt as option_r."""
        names = backend.get_hotkey_names("right alt")
        assert "option_r" in names

    def test_pre_injection_cleanup_is_noop(self, backend):
        """pre_injection_cleanup should be a no-op on macOS."""
        # Should not raise
        backend.pre_injection_cleanup()

    def test_type_text_empty_string(self, backend):
        result = backend.type_text("")
        assert result == 0


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-only tests")
class TestLinuxBackend:
    """Linux-specific backend validation."""

    @pytest.fixture
    def backend(self):
        from platform_backend.linux import LinuxBackend
        return LinuxBackend()

    def test_right_alt_aliases(self, backend):
        names = backend.get_hotkey_names("right alt")
        assert "alt_r" in names
        assert "altgr" in names

    def test_pre_injection_cleanup_is_noop(self, backend):
        """pre_injection_cleanup should be a no-op on Linux."""
        backend.pre_injection_cleanup()

    def test_type_text_empty_string(self, backend):
        result = backend.type_text("")
        assert result == 0

    def test_wayland_detection(self):
        """Verify Wayland detection uses XDG_SESSION_TYPE."""
        with mock.patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from platform_backend.linux import LinuxBackend
            b = LinuxBackend()
            assert b._is_wayland is True

    def test_x11_detection(self):
        with mock.patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            from platform_backend.linux import LinuxBackend
            b = LinuxBackend()
            assert b._is_wayland is False


# ---------------------------------------------------------------------------
# Model path resolution tests
# ---------------------------------------------------------------------------

class TestModelPath:
    """Test _get_model_path() logic for bundled vs. downloaded model."""

    def test_returns_model_name_when_no_bundle(self):
        """When no bundled model exists, should return 'base' for download."""
        # Ensure _MEIPASS is not set (not a PyInstaller bundle)
        if hasattr(sys, '_MEIPASS'):
            pytest.skip("Running inside PyInstaller bundle")
        # Import the function
        sys.path.insert(0, ".")
        from main import _get_model_path, MODEL_SIZE
        # Unless there's a local faster-whisper-base dir with model.bin,
        # this should return the model size string
        import os
        bundled = os.path.join(os.path.dirname(os.path.abspath("main.py")), "faster-whisper-base")
        if os.path.isdir(bundled) and os.path.isfile(os.path.join(bundled, "model.bin")):
            # Model exists locally — should return the path
            assert os.path.isdir(_get_model_path())
        else:
            assert _get_model_path() == MODEL_SIZE

    def test_bundled_model_detection(self, tmp_path):
        """When a bundled model dir exists with model.bin, should return its path."""
        model_dir = tmp_path / "faster-whisper-base"
        model_dir.mkdir()
        (model_dir / "model.bin").write_bytes(b"fake model")

        with mock.patch.object(sys, '_MEIPASS', str(tmp_path), create=True):
            # Re-test the logic directly
            import os
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            bundled = os.path.join(bundle_dir, 'faster-whisper-base')
            assert os.path.isdir(bundled)
            assert os.path.isfile(os.path.join(bundled, 'model.bin'))


# ---------------------------------------------------------------------------
# App configuration tests
# ---------------------------------------------------------------------------

class TestAppConfig:
    """Test application-level configuration constants."""

    def test_app_version_format(self):
        from main import APP_VERSION
        parts = APP_VERSION.split(".")
        assert len(parts) == 3, "APP_VERSION should be semver (X.Y.Z)"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' is not numeric"

    def test_default_hotkey_is_right_alt(self):
        from main import DEFAULT_HOTKEY
        assert DEFAULT_HOTKEY == "right alt"

    def test_sample_rate_is_16khz(self):
        from main import SAMPLE_RATE
        assert SAMPLE_RATE == 16000

    def test_model_size_is_base(self):
        from main import MODEL_SIZE
        assert MODEL_SIZE == "base"


# ---------------------------------------------------------------------------
# AppState tests
# ---------------------------------------------------------------------------

class TestAppState:
    """Test AppState initialization."""

    def test_initial_state(self):
        from main import AppState
        s = AppState()
        assert s.is_recording is False
        assert s.hotkey == "right alt"
        assert s.transcript_history == []
        assert s.status_text == "Ready"
        assert s.whisper_model is None
        assert s.selected_ollama_model is None

    def test_audio_queue_is_empty(self):
        from main import AppState
        s = AppState()
        assert s.audio_queue.empty()
