# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Whisper Walkie** — A Windows push-to-talk speech-to-text desktop app. Hold a hotkey (default: Right Alt), speak, release, and the transcribed text is typed directly into whatever window has focus via Windows SendInput (Unicode keystroke injection). No clipboard involved.

## Tech Stack

- **Python** single-file app (`main.py` — ~1470 lines, everything lives here)
- **Flet** (v0.81.0+) for the GUI (Flutter-based Python UI framework)
- **faster-whisper** for local speech-to-text (uses CTranslate2, supports CUDA)
- **sounddevice** for audio capture
- **keyboard** library for global hotkey hooks (low-level Windows hooks)
- **Windows SendInput API** via ctypes for typing text into target windows
- **Ollama** integration for optional AI model selection (local LLM)

## Commands

```bash
# Run from source (with console output for debugging)
venv\Scripts\python.exe main.py

# Run from source (no console window — production-like)
venv\Scripts\pythonw.exe main.py

# Install dependencies
venv\Scripts\pip.exe install -r requirements.txt

# Build standalone exe with PyInstaller
pyinstaller WhisperWalkie.spec
```

Batch launchers: `start-walkie.bat` (exe), `start-walkie-debug.bat` (source+console), `start-walkie-source.bat` (source, no console).

## Architecture

Everything is in `main.py`. The key sections, in order:

1. **Windows API layer** (lines ~34–168): ctypes structs for `INPUT`, `KEYBDINPUT`, `MOUSEINPUT`. `type_text_direct()` injects Unicode characters via `SendInput` — no clipboard, no Ctrl+V. Releases stuck modifier keys before typing.

2. **AppState** (line ~177): Global singleton holding recording state, audio queue, selected device/hotkey/model, GUI callback reference, and keyboard hook refs.

3. **Audio pipeline** (lines ~196–338): `load_whisper()` → tries CUDA then falls back to CPU. `audio_callback()` feeds a queue during recording. `start_recording()`/`stop_recording()` toggle state. `process_audio()` runs transcription in a background thread, then unhooks the keyboard listener (because the `keyboard` library intercepts synthetic keystrokes), sends Escape+click to dismiss Alt-triggered menus, types the text, and re-hooks.

4. **Design system** (line ~358): `DS` class with color tokens, spacing, radii — indigo/cyan dark theme.

5. **GUI components** (lines ~408–750): Reusable Flet widgets (`_divider`, `_section_label`, `_styled_dropdown`, `_transcription_entry`). `StatusCard` class manages the hero section with state transitions (ready/recording/processing/result) and a live recording timer.

6. **Main GUI** (`main_gui`, line ~850): Assembles header, status card, history panel, settings panel (hotkey/model/microphone dropdowns), and footer. Wires `update_ui()` callback for background threads to drive UI state.

7. **Background listener** (line ~1386): `run_transcription()` loads Whisper, installs `keyboard.hook()` with scan-code matching for Right Alt variants (alt gr, scan 541/57400), opens a `sounddevice.InputStream`, and loops forever.

## Critical Implementation Details

- **Keyboard hook lifecycle**: The `keyboard` library's low-level hook intercepts ALL keystrokes including synthetic ones from SendInput. The hook must be temporarily removed (`keyboard.unhook_all()`) before injecting text, then reinstalled afterward. This is the most fragile part of the app.

- **Right Alt / AltGr quirk**: Windows reports Right Alt inconsistently — as 'right alt', 'alt gr', or various scan codes (56, 541, 57400). The hotkey matcher checks both name and scan code sets.

- **Focus management after recording**: After the user releases the hotkey, the app sends Escape (to dismiss any Alt-triggered menus) and a mouse click at the current cursor position (to refocus the text area), then types. There's a 300ms delay to let the key-up propagate.

- **Logging**: File-based logging to `walkie.log` (overwritten each run). The app's own logger is DEBUG level while third-party loggers are set to WARNING.

- **PyInstaller build**: `WhisperWalkie.spec` collects all data/binaries from faster_whisper, flet, sounddevice, and scipy. Produces a single-file `.exe` with `console=False`.
