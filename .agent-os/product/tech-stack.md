# Technical Stack

## Application Framework
- **Python 3.10+** — Core language
- **Flet 0.81.0** — Flutter-based cross-platform GUI framework

## Speech-to-Text Engine
- **faster-whisper** (CTranslate2) — Local Whisper inference
- **CUDA** — GPU acceleration on Windows/Linux (auto-detected, CPU fallback)

## Audio
- **sounddevice** (PortAudio bindings) — Microphone capture
- **scipy** — Audio processing (WAV encoding)
- **numpy** — Audio buffer management

## Keyboard & Text Injection
- **keyboard** (Windows only) — Global hotkey hooks via low-level Win32 API
- **pynput** (macOS, Linux) — Global keyboard hooks and text injection
- **ctypes / Win32 SendInput** (Windows) — Native Unicode keystroke injection
- **Quartz CGEvents** (macOS) — Native text injection via pynput
- **Xlib / XRecord** (Linux X11) — Keyboard hooks via pynput
- **xdotool** (Linux X11 fallback) — Text injection and window title
- **wtype** (Linux Wayland fallback) — Text injection

## AI Integration
- **Ollama** (optional) — Local LLM detection for future AI post-processing
- **requests** — HTTP client for Ollama API

## Utilities
- **pyperclip** — Clipboard access for copy buttons

## Build & Distribution
- **PyInstaller** — Windows standalone exe packaging (`WhisperWalkie.spec`)
- **venv** — Python virtual environment

## Hosting & Repository
- **GitHub**: https://github.com/joestechsolutions/whisper-walkie
- **Distribution**: GitHub Releases (Windows exe), source install (all platforms)
- **License**: MIT
