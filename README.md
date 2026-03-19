# Whisper Walkie

**Local, private speech-to-text that types directly into any window.**

Hold a hotkey, speak, release — your words appear wherever your cursor is. No cloud APIs, no clipboard hacks, no subscriptions. Everything runs locally on your machine using OpenAI's Whisper model.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![AI Built](https://img.shields.io/badge/Built%20with-Generative%20AI-blueviolet)

---

## How It Works

1. **Hold** the push-to-talk key (default: Right Alt)
2. **Speak** into your microphone
3. **Release** the key
4. Text is **typed directly** into whatever app has focus — browser, chat, IDE, anything

No clipboard involved. Whisper Walkie injects Unicode keystrokes via the Windows SendInput API, so it works everywhere a keyboard works.

## Features

- **100% Local** — Whisper model runs on your machine. Audio never leaves your computer.
- **GPU Accelerated** — Automatically uses CUDA if available, falls back to CPU.
- **Works Everywhere** — Types into any window: browsers, Slack, Discord, VS Code, Word, games.
- **Push-to-Talk** — Hold to record, release to transcribe. Simple as a walkie-talkie.
- **Configurable Hotkey** — Right Alt, Scroll Lock, Pause, F13, F14, Insert, or Right Ctrl.
- **Transcription History** — Last 10 transcriptions saved with timestamps and copy buttons.
- **Pin to Top** — Optional always-on-top mode so the app stays visible.
- **Ollama Integration** — Detects local Ollama models for future AI post-processing.

## Screenshots

*Coming soon*

## Quick Start

### Prerequisites

- **Windows 10/11**
- **Python 3.10+**
- **A microphone**
- **NVIDIA GPU** (optional, for faster transcription)

### Option 1: Run from Source

```bash
# Clone the repo
git clone https://github.com/joestechsolutions/whisper-walkie.git
cd whisper-walkie

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run (with console for debugging)
python main.py

# Or run without console window
pythonw main.py
```

### Option 2: Download the Exe

Check [Releases](https://github.com/joestechsolutions/whisper-walkie/releases) for a standalone `.exe` — no Python required.

### Option 3: Build Your Own Exe

```bash
pip install pyinstaller
pyinstaller WhisperWalkie.spec
# Output: dist/WhisperWalkie.exe
```

## Configuration

All settings are available in the app's UI:

| Setting | Options | Default |
|---------|---------|---------|
| **Push-to-Talk Key** | Right Alt, Scroll Lock, Pause, F13, F14, Insert, Right Ctrl | Right Alt |
| **Microphone** | Any detected input device | Auto-detected |
| **AI Model** | Any local Ollama model | First available |

## Tech Stack

| Component | Technology |
|-----------|------------|
| GUI | [Flet](https://flet.dev) (Flutter for Python) |
| Speech-to-Text | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) |
| Audio Capture | [sounddevice](https://python-sounddevice.readthedocs.io/) (PortAudio) |
| Hotkey System | [keyboard](https://github.com/boppreh/keyboard) (low-level hooks) |
| Text Injection | Windows SendInput API via ctypes |
| Local AI | [Ollama](https://ollama.ai) (optional) |

## How It's Built

This project was built using **Generative AI as a development tool** — specifically [Claude](https://claude.ai) by Anthropic. It demonstrates that AI-assisted development is a legitimate and powerful approach to building real, functional software.

The entire application — from the Windows API integration to the Flet GUI design system — was developed through human-AI collaboration. The developer (a human with domain expertise) directed the architecture and requirements, while AI handled implementation details, debugging edge cases, and iterating on the UI design.

**This is the future of software engineering.** AI doesn't replace developers — it amplifies them.

## Known Limitations

- **Windows only** — Uses Windows-specific APIs (SendInput, low-level keyboard hooks). Mac/Linux support is possible but not yet implemented.
- **Right Alt quirk** — Windows reports Right Alt as "AltGr" in some keyboard layouts, which can trigger menu bars. The app handles this with an Escape keystroke + click workaround.
- **First transcription is slower** — The Whisper model loads on first use. Subsequent transcriptions are fast.

## Project Structure

```
whisper-walkie/
├── main.py              # Everything — app logic, GUI, audio, hotkeys
├── requirements.txt     # Python dependencies
├── WhisperWalkie.spec   # PyInstaller build config
├── icon.ico             # App icon
├── start-walkie.bat     # Launch exe
├── start-walkie-debug.bat    # Launch from source (console)
├── start-walkie-source.bat   # Launch from source (no console)
└── CLAUDE.md            # AI development context
```

## Contributing

Contributions welcome! This is an open-source project by [Joe's Tech Solutions LLC](https://www.joestechsolutions.com).

1. Fork it
2. Create your feature branch (`git checkout -b feature/cool-thing`)
3. Commit your changes (`git commit -m 'Add cool thing'`)
4. Push to the branch (`git push origin feature/cool-thing`)
5. Open a Pull Request

## License

[MIT](LICENSE) — Use it, modify it, ship it.

## Author

**Joe Blas** — [Joe's Tech Solutions LLC](https://www.joestechsolutions.com)
- Email: joe@joestechsolutions.com
- LinkedIn: [joseph-blas](https://www.linkedin.com/in/joseph-blas/)
- GitHub: [joestechsolutions](https://github.com/joestechsolutions)
