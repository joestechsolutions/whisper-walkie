# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Whisper Walkie** — A cross-platform push-to-talk speech-to-text desktop app. Hold a hotkey (default: Right Alt), speak, release, and the transcribed text is typed directly into whatever window has focus. No clipboard involved. Supports Windows, macOS, and Linux.

## Tech Stack

- **Python** (`main.py` for app logic/GUI, `platform_backend/` for OS-specific code)
- **Flet** (v0.81.0+) for the GUI (Flutter-based, cross-platform)
- **faster-whisper** for local speech-to-text (CTranslate2, CUDA on Windows/Linux, CPU on macOS)
- **sounddevice** for audio capture
- **Platform backend layer** for keyboard hooks and text injection:
  - **Windows**: `keyboard` library + Win32 SendInput via ctypes
  - **macOS**: `pynput` + Quartz CGEvents (requires Accessibility permissions)
  - **Linux**: `pynput` + XRecord (X11), xdotool/wtype fallbacks for Wayland
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
├── windows.py       # Win32 SendInput + keyboard library hooks
├── macos.py         # pynput + CGEvents + osascript
└── linux.py         # pynput + XRecord + xdotool/wtype fallbacks
```

**Key interface methods:**
- `type_text(text)` — inject text into the focused window
- `install_key_hook(callback)` / `remove_key_hook()` / `reinstall_key_hook()` — global hotkey monitoring
- `pre_injection_cleanup()` — dismiss Alt menus (Windows), no-op elsewhere
- `needs_unhook_for_injection` — True on Windows only (keyboard lib intercepts synthetic keys)
- `get_hotkey_names()` / `get_hotkey_scan_codes()` — platform-aware hotkey matching

### Main App (`main.py`)

1. **AppState** — Global singleton holding recording state, audio queue, device/hotkey/model selection, GUI callback, keyboard hook refs.

2. **Audio pipeline** — `load_whisper()` tries CUDA (Windows/Linux) then falls back to CPU. `audio_callback()` feeds a queue during recording. `process_audio()` runs transcription in a background thread, then uses the backend to type the result.

3. **Design system** — `DS` class with color tokens, spacing, radii (indigo/cyan dark theme).

4. **GUI** — Flet-based: StatusCard (ready/recording/processing/result states with live timer), transcription history panel, settings panel (hotkey/model/microphone dropdowns), header with pin-to-top, footer.

5. **Background listener** — `run_transcription()` loads Whisper, installs keyboard hook via backend, opens a `sounddevice.InputStream`, loops forever.

## Critical Implementation Details

- **Keyboard hook lifecycle (Windows)**: The `keyboard` library's low-level hook intercepts ALL keystrokes including synthetic ones. The hook must be temporarily removed before injecting text (`backend.needs_unhook_for_injection` is True on Windows). On macOS/Linux, pynput's listener is read-only and doesn't intercept, so no unhook needed.

- **Right Alt / AltGr**: Reported inconsistently across platforms. Each backend's `get_hotkey_names()` returns all known aliases. Windows also matches by scan code (56, 541, 57400).

- **Focus management (Windows only)**: `backend.pre_injection_cleanup()` sends Escape + mouse click to dismiss Alt-triggered menus. No-op on macOS/Linux.

- **macOS permissions**: Requires Accessibility access (System Preferences > Privacy & Security > Accessibility). The macOS backend logs a helpful error if permission is denied.

- **Linux display servers**: X11 works fully via pynput XRecord. Wayland has limited support — falls back to `wtype` for text injection and cannot get window titles. The backend detects `XDG_SESSION_TYPE` and warns.

- **Logging**: File-based logging to `walkie.log` (overwritten each run). App logger is DEBUG, third-party loggers are WARNING.

- **PyInstaller build**: `WhisperWalkie.spec` is Windows-specific. macOS/Linux packaging not yet configured.
