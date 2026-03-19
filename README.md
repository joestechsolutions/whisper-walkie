# Whisper Walkie

**Local, private speech-to-text that types directly into any window.**

Hold a hotkey, speak, release — your words appear wherever your cursor is. No cloud APIs, no clipboard hacks, no subscriptions. Everything runs locally on your machine using OpenAI's Whisper model.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![CI](https://github.com/joestechsolutions/whisper-walkie/actions/workflows/ci.yml/badge.svg)
![AI Built](https://img.shields.io/badge/Built%20with-Claude%20AI-blueviolet)

---

## How It Works

1. **Hold** the push-to-talk key (default: Right Alt)
2. **Speak** into your microphone
3. **Release** the key
4. Text is **typed directly** into whatever app has focus — browser, chat, IDE, anything

No clipboard involved. Text is injected via platform-native keystroke APIs, so it works everywhere a keyboard works.

## Features

- **100% Local** — Whisper model runs on your machine. Audio never leaves your computer.
- **Cross-Platform** — Works on Windows, macOS, and Linux.
- **GPU Accelerated** — Automatically uses CUDA if available (Windows/Linux), falls back to CPU.
- **Works Everywhere** — Types into any window: browsers, Slack, Discord, VS Code, Word, games.
- **Push-to-Talk** — Hold to record, release to transcribe. Simple as a walkie-talkie.
- **Configurable Hotkey** — Right Alt, Scroll Lock, Pause, F13, F14, Insert, or Right Ctrl.
- **Transcription History** — Last 10 transcriptions saved with timestamps and copy buttons.
- **Pin to Top** — Optional always-on-top mode so the app stays visible.
- **Ollama Integration** — Detects local Ollama models for future AI post-processing.
- **Self-Sustaining** — CI/CD pipeline tests every change on all 3 platforms. Dependabot keeps dependencies current. Tag a version and the exe builds itself.

## Demo

https://github.com/joestechsolutions/whisper-walkie/assets/demo.mp4

> Hold Right Alt, speak, release — text appears instantly in any window.

## Quick Start

### Prerequisites

- **Python 3.10+**
- **A microphone**
- **NVIDIA GPU** (optional, for faster transcription on Windows/Linux)

### Platform-Specific Notes

<details>
<summary><b>Windows</b></summary>

Works out of the box. CUDA acceleration supported if you have an NVIDIA GPU.

```bash
git clone https://github.com/joestechsolutions/whisper-walkie.git
cd whisper-walkie
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
</details>

<details>
<summary><b>macOS</b></summary>

Requires **Accessibility permissions** for global keyboard hooks.

On first run, macOS will prompt you to grant access in **System Settings > Privacy & Security > Accessibility**. You must add your terminal app (or Python) to the allowed list.

```bash
git clone https://github.com/joestechsolutions/whisper-walkie.git
cd whisper-walkie
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

> Note: CUDA is not available on macOS. Whisper runs on CPU (still fast with the `base` model).
</details>

<details>
<summary><b>Linux</b></summary>

Works on **X11** out of the box via pynput. **Wayland** has limited support.

For best results, install `xdotool`:
```bash
sudo apt install xdotool   # Debian/Ubuntu
sudo pacman -S xdotool     # Arch
sudo dnf install xdotool   # Fedora
```

For Wayland, also install `wtype`:
```bash
sudo apt install wtype      # if available
```

```bash
git clone https://github.com/joestechsolutions/whisper-walkie.git
cd whisper-walkie
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

> Note: pynput does **not** require root on X11.
</details>

### Download Pre-Built (Windows)

Check [Releases](https://github.com/joestechsolutions/whisper-walkie/releases) for a standalone `.exe` — no Python required. New releases are built automatically via GitHub Actions when a version is tagged.

### Build Your Own Exe (Windows)

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

| Component | Technology | Platform |
|-----------|------------|----------|
| GUI | [Flet](https://flet.dev) 0.81.0 (Flutter for Python) | All |
| Speech-to-Text | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) | All |
| Audio Capture | [sounddevice](https://python-sounddevice.readthedocs.io/) (PortAudio) | All |
| Keyboard Hooks | [pynput](https://pynput.readthedocs.io/) | All |
| Text Injection | Win32 SendInput via ctypes | Windows |
| Text Injection | pynput CGEvents | macOS |
| Text Injection | pynput Xlib / xdotool / wtype | Linux |
| Local AI | [Ollama](https://ollama.ai) (optional) | All |
| CI/CD | GitHub Actions | All |
| Dependency Updates | Dependabot (weekly) | All |

## How It's Built

This project was built using **Generative AI as a development tool** — specifically [Claude](https://claude.ai) by Anthropic. It demonstrates that AI-assisted development is a legitimate and powerful approach to building real, functional software.

The entire application — from the platform abstraction layer to the Flet GUI design system — was developed through human-AI collaboration. The developer (a human with domain expertise) directed the architecture and requirements, while AI handled implementation details, cross-platform compatibility, debugging edge cases, and iterating on the UI design.

### Self-Managing Architecture

This project is designed to sustain itself with minimal human intervention:

- **GitHub Actions CI** tests every push across Windows, macOS, and Linux (Python 3.10 + 3.12)
- **Dependabot** opens weekly PRs when dependencies have updates — CI validates them automatically
- **Auto-build releases** — tag a version (`git tag v1.x`) and a Windows exe is built and published to GitHub Releases
- **Unified dependencies** — one keyboard library ([pynput](https://pynput.readthedocs.io/)) across all platforms, reducing maintenance surface

**This is the future of software engineering.** AI doesn't replace developers — it amplifies them.

## Platform Support

| Feature | Windows | macOS | Linux (X11) | Linux (Wayland) |
|---------|---------|-------|-------------|-----------------|
| Push-to-talk hotkey | Full | Full | Full | Limited |
| Text injection | SendInput (Unicode) | CGEvents | pynput/xdotool | wtype |
| CUDA acceleration | Yes | No | Yes | Yes |
| Window title logging | Yes | Yes | Yes (xdotool) | No |
| Pre-built exe | Yes | No | No | No |

## Known Limitations

- **Right Alt quirk (Windows)** — Windows reports Right Alt as "AltGr" in some keyboard layouts, which can trigger menu bars. The app handles this with an Escape keystroke + click workaround.
- **First transcription is slower** — The Whisper model loads on first use. Subsequent transcriptions are fast.
- **Screen recording conflict** — Some screen recorders grab exclusive mic access, causing garbled transcription. Fix: disable "Allow applications to take exclusive control" in Windows Sound Settings for your microphone.
- **Wayland (Linux)** — Global keyboard hooks require `/dev/input/` access (add your user to the `input` group). Text injection needs `wtype` installed.
- **macOS permissions** — Must grant Accessibility access or keyboard hooks will silently fail.

## Project Structure

```
whisper-walkie/
├── main.py                    # App logic, GUI, audio, transcription
├── platform_backend/          # Cross-platform abstraction layer
│   ├── __init__.py            # Factory: get_backend()
│   ├── base.py                # PlatformBackend ABC
│   ├── windows.py             # Win32 SendInput + pynput hooks
│   ├── macos.py               # pynput + CGEvents + osascript
│   └── linux.py               # pynput + xdotool/wtype
├── .github/
│   ├── workflows/ci.yml       # CI: test on 3 platforms x 2 Python versions
│   ├── workflows/build-exe.yml # Auto-build exe on version tags
│   └── dependabot.yml         # Weekly dependency update PRs
├── .agent-os/product/         # AI agent context (mission, roadmap, decisions)
├── requirements.txt           # Python dependencies (pinned)
├── WhisperWalkie.spec         # PyInstaller build config (Windows)
├── icon.ico                   # App icon
├── start-walkie.bat           # Launch exe (Windows)
├── start-walkie-debug.bat     # Launch from source (Windows, console)
├── start-walkie-source.bat    # Launch from source (Windows, no console)
└── CLAUDE.md                  # AI development context
```

## Contributing

Contributions welcome! This is an open-source project by [Joe's Tech Solutions LLC](https://www.joestechsolutions.com).

1. Fork it
2. Create your feature branch (`git checkout -b feature/cool-thing`)
3. Commit your changes (`git commit -m 'Add cool thing'`)
4. Push to the branch (`git push origin feature/cool-thing`)
5. Open a Pull Request

CI will automatically test your changes on Windows, macOS, and Linux.

## License

[MIT](LICENSE) — Use it, modify it, ship it.

## Author

**Joe Blas** — [Joe's Tech Solutions LLC](https://www.joestechsolutions.com)
- Email: joe@joestechsolutions.com
- LinkedIn: [joseph-blas](https://www.linkedin.com/in/joseph-blas/)
- GitHub: [joestechsolutions](https://github.com/joestechsolutions)
