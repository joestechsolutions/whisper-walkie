# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Whisper Walkie** — A cross-platform push-to-talk speech-to-text desktop app. Hold a hotkey (default: Right Alt), speak, release, and the transcribed text is typed directly into whatever window has focus. No clipboard involved. Supports Windows, macOS, and Linux.

## Tech Stack

- **Python** (`main.py` for app logic/GUI, `platform_backend/` for OS-specific code)
- **Flet** (v0.82.2, pinned) for the GUI (Flutter-based, cross-platform)
- **faster-whisper** for local speech-to-text (CTranslate2, CUDA on Windows/Linux, CPU on macOS)
- **sounddevice** for audio capture
- **pynput** for keyboard hooks on all platforms (unified — no platform-specific keyboard libraries)
- **Platform backend layer** for text injection:
  - **Windows**: Win32 SendInput via ctypes (pynput for hooks)
  - **macOS**: pynput + Quartz CGEvents (requires Accessibility permissions)
  - **Linux**: pynput + XRecord (X11), xdotool/wtype fallbacks for Wayland
- **Ollama** integration for optional AI model selection (local LLM)

## Commands

```bash
# Run from source (with console output for debugging)
python main.py                         # or: venv\Scripts\python.exe main.py (Windows)

# Run from source (no console window — production-like, Windows only)
pythonw main.py

# Install dependencies
pip install -r requirements.txt

# Build standalone exe with PyInstaller (Windows)
pyinstaller WhisperWalkie.spec
```

Batch launchers (Windows): `start-walkie.bat` (exe), `start-walkie-debug.bat` (source+console), `start-walkie-source.bat` (source, no console).

## Architecture

### Platform Backend (`platform_backend/`)

The OS-specific code is isolated behind an abstract interface:

```
platform_backend/
├── __init__.py      # Factory: get_backend() returns the right backend for the OS
├── base.py          # PlatformBackend ABC — defines the interface
├── windows.py       # Win32 SendInput + pynput hooks
├── macos.py         # pynput + CGEvents + osascript
└── linux.py         # pynput + XRecord + xdotool/wtype fallbacks
```

**Key interface methods:**
- `type_text(text)` — inject text into the focused window
- `install_key_hook(callback)` / `remove_key_hook()` / `reinstall_key_hook()` — global hotkey monitoring
- `pre_injection_cleanup()` — dismiss Alt menus (Windows), no-op elsewhere
- `needs_unhook_for_injection` — False on all platforms (pynput is read-only, ignores synthetic keys via `injected` flag)
- `get_hotkey_names()` / `get_hotkey_scan_codes()` — platform-aware hotkey matching

### Main App (`main.py`)

1. **AppState** — Global singleton holding recording state, audio queue, device/hotkey/model selection, GUI callback, keyboard hook refs.

2. **Audio pipeline** — `load_whisper()` tries CUDA (Windows/Linux) then falls back to CPU. `audio_callback()` feeds a queue during recording. `process_audio()` runs transcription in a background thread, then uses the backend to type the result.

3. **Design system** — `DS` class with color tokens, spacing, radii (indigo/cyan dark theme).

4. **GUI** — Flet-based: StatusCard (ready/recording/processing/result states with live timer), transcription history panel, settings panel (hotkey/model/microphone dropdowns), header with pin-to-top, footer.

5. **First-run onboarding** — 3-step modal dialog (Welcome → Setup mic/hotkey → Try it). Detected via `~/.whisper-walkie/config.json`. On completion, saves `onboarding_complete: true` and applies user's mic/hotkey selections to AppState. Config helpers: `_get_config_path()`, `_load_config()`, `_save_config()`, `_is_first_run()`.

6. **Background listener** — `run_transcription()` loads Whisper, installs keyboard hook via backend, opens a `sounddevice.InputStream`, loops forever.

## Critical Implementation Details

- **Keyboard hooks (all platforms)**: All three backends use pynput's Listener, which is read-only and does NOT intercept synthetic keystrokes. On Windows, pynput passes an `injected` flag to callbacks, which we use to ignore our own SendInput events. No unhook/rehook cycle is needed on any platform.

- **Right Alt / AltGr**: Reported inconsistently across platforms. Each backend's `get_hotkey_names()` returns all known aliases. Windows matches by VK code (165 = VK_RMENU).

- **Focus management (Windows only)**: `backend.pre_injection_cleanup()` sends Escape + mouse click to dismiss Alt-triggered menus. No-op on macOS/Linux.

- **macOS permissions**: Requires Accessibility access (System Preferences > Privacy & Security > Accessibility). The macOS backend logs a helpful error if permission is denied.

- **Linux display servers**: X11 works fully via pynput XRecord. Wayland has limited support — falls back to `wtype` for text injection and cannot get window titles. The backend detects `XDG_SESSION_TYPE` and warns.

- **Logging**: File-based logging to `walkie.log` (overwritten each run). App logger is DEBUG, third-party loggers are WARNING. Transcription content is NOT logged (only char count) for privacy. Window titles are not logged.

- **Input sanitization**: Transcription output is sanitized via `unicodedata.category()` to strip control characters before keyboard injection. Only `\n` and `\t` are preserved.

- **CI security**: All GitHub Actions are SHA-pinned in both `ci.yml` and `build-exe.yml`. Dependencies are pinned to exact versions. `pip-audit` runs on every CI push.

- **PyInstaller build**: `WhisperWalkie.spec` uses `--onedir` mode and builds on all 3 platforms via GitHub Actions. The Whisper base model is pre-downloaded into `./faster-whisper-base/` at build time and bundled into the output. At runtime, `_get_model_path()` in main.py checks for the bundled model via `sys._MEIPASS`, falling back to auto-download if not bundled.
