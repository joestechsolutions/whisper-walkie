# Whisper Walkie

<img width="1280" height="640" alt="social-preview" src="https://github.com/user-attachments/assets/fc5eaa28-de99-430a-a38d-83d131719eee" />

### Your voice, your machine. Nothing leaves.

**Free voice typing that works in any app on your computer.** Hold a key, speak, release — your words appear wherever your cursor is. No cloud, no subscriptions, no account needed.

[![Download Free](https://img.shields.io/github/v/release/joestechsolutions/whisper-walkie?label=Download%20Free&style=for-the-badge&color=6366f1)](https://github.com/joestechsolutions/whisper-walkie/releases/latest)

![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue)
![License](https://img.shields.io/badge/License-MIT%20(Free%20Forever)-green)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-brightgreen)
![CI](https://github.com/joestechsolutions/whisper-walkie/actions/workflows/ci.yml/badge.svg)

---

## Download

Choose your platform and download — no Python or technical setup required:

| Platform | Download | Size | Notes |
|----------|----------|------|-------|
| **Windows** | [**.exe installer**](https://github.com/joestechsolutions/whisper-walkie/releases/latest) | ~200 MB | Double-click to install. AI model included. |
| **macOS** | [**.zip**](https://github.com/joestechsolutions/whisper-walkie/releases/latest) | ~200 MB | Drag to Applications. Grant Accessibility permission on first run. |
| **Linux** | [**.tar.gz**](https://github.com/joestechsolutions/whisper-walkie/releases/latest) | ~200 MB | Extract and run. Works best on X11. |

> **Everything is bundled** — the AI speech model is included in the download. No internet needed after you download.

---

## Quick Start (2 minutes)

### 1. Install

**Windows:** Run the installer. If Windows SmartScreen appears, click **"More info"** → **"Run anyway"** (the app is [open source](https://github.com/joestechsolutions/whisper-walkie) and safe).

**macOS:** Extract the `.zip` and run the installer:
```bash
unzip WhisperWalkie-macos.zip
cd WhisperWalkie
./install-macos.sh
```
This installs to `/Applications`, clears the Gatekeeper warning, and creates a Launchpad/Spotlight entry. Then grant Accessibility permissions in **System Settings → Privacy & Security → Accessibility.**

**Linux:** Extract and launch:
```bash
tar xzf WhisperWalkie-linux.tar.gz
cd WhisperWalkie
./WhisperWalkie
```

**Create a desktop shortcut** (so it appears in your app launcher):
```bash
./install-linux.sh
```

For best results, install xdotool:
```bash
sudo apt install xdotool   # Debian/Ubuntu
```

### 2. Choose your microphone

Open the app and go to **Settings**. Select your microphone from the dropdown.

### 3. Start talking

1. **Hold** the push-to-talk key (default: **Right Alt**)
2. **Speak** naturally into your microphone
3. **Release** the key
4. Text appears wherever your cursor is — browser, Slack, VS Code, Word, anywhere

That's it. No account, no sign-up, no configuration files.

---

## Demo

https://github.com/user-attachments/assets/682d5a2b-b35b-41cd-ac61-77a16de6ad6c

> Hold Right Alt, speak, release — text appears instantly in any window.

---

## Why Whisper Walkie?

| Other Voice Tools | Whisper Walkie |
|-------------------|----------------|
| Send your audio to cloud servers | **100% local** — audio never leaves your machine |
| $10-20/month subscriptions | **Free and open source** — forever |
| Only work in specific apps | **Works in ANY window** — types via keyboard injection |
| Require accounts and sign-ups | **No account needed** — download, run, done |
| Always listening | **Push-to-talk** — only records when YOU hold the key |

## Features

- **100% Local & Private** — AI model runs on your machine. Audio never touches a network.
- **Works Everywhere** — Types into any window: browsers, chat apps, IDEs, games.
- **GPU Accelerated** — Uses NVIDIA CUDA if available (Windows/Linux), falls back to CPU.
- **Cross-Platform** — Windows, macOS, and Linux.
- **Push-to-Talk** — Hold to record, release to transcribe. Simple as a walkie-talkie.
- **Configurable Hotkey** — Right Alt, Scroll Lock, Pause, F13, F14, Insert, or Right Ctrl.
- **Transcription History** — Last 10 transcriptions with timestamps and copy buttons.
- **Works Offline** — AI model is bundled. No internet needed after download.
- **99 Languages** — Whisper auto-detects the spoken language. Accuracy varies by language — English is strongest.

---

## FAQ

<details>
<summary><b>Is it really free?</b></summary>
<br>
Yes, completely free and open source under the MIT license. No trials, no premium tier, no subscriptions. Forever.
</details>

<details>
<summary><b>Is my audio sent to any server?</b></summary>
<br>
Never. The AI model runs entirely on your machine. Your audio is processed locally and never touches a network. No accounts, no telemetry, no cloud.
</details>

<details>
<summary><b>Windows shows a SmartScreen warning — is it safe?</b></summary>
<br>
Yes. SmartScreen warns about apps from new publishers. Since Whisper Walkie is open source, you can <a href="https://github.com/joestechsolutions/whisper-walkie">read every line of code</a>. Click "More info" → "Run anyway" to proceed.
</details>

<details>
<summary><b>Do I need a powerful computer?</b></summary>
<br>
No. The Whisper "base" model runs on any modern CPU. If you have an NVIDIA GPU, transcription will be faster with CUDA acceleration.
</details>

<details>
<summary><b>Does it work offline?</b></summary>
<br>
Yes. The AI model is bundled with the download. No internet connection needed after you download.
</details>

<details>
<summary><b>Can I change the push-to-talk key?</b></summary>
<br>
Yes. Open Settings in the app and choose from: Right Alt, Scroll Lock, Pause, F13, F14, Insert, or Right Ctrl.
</details>

<details>
<summary><b>How do I grant macOS Accessibility permissions?</b></summary>
<br>
Go to System Settings → Privacy & Security → Accessibility. Click the + button and add the Whisper Walkie app.
</details>

---

## Settings

All settings are available in the app — no config files to edit:

| Setting | Options | Default |
|---------|---------|---------|
| **Push-to-Talk Key** | Right Alt, Scroll Lock, Pause, F13, F14, Insert, Right Ctrl | Right Alt |
| **Microphone** | Any detected input device | Auto-detected |
| **AI Model** | Any local Ollama model (optional) | First available |

---

## For Developers

<details>
<summary><b>Run from source</b></summary>

### Prerequisites
- Python 3.10+
- A microphone

### Setup

```bash
git clone https://github.com/joestechsolutions/whisper-walkie.git
cd whisper-walkie
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python main.py
```

### Platform notes

**macOS:** Requires Accessibility permissions. CPU only (no CUDA).

**Linux (X11):** Works out of the box. Install `xdotool` for window title detection.

**Linux (Wayland):** Limited support. Install `wtype` for text injection.

</details>

<details>
<summary><b>Build standalone executable</b></summary>

```bash
# Download the Whisper model first
python -c "from faster_whisper.utils import download_model; download_model('base', output_dir='./faster-whisper-base')"

# Build with PyInstaller
pip install pyinstaller
pyinstaller WhisperWalkie.spec

# Output: dist/WhisperWalkie/ folder
```

</details>

<details>
<summary><b>Tech stack</b></summary>

| Component | Technology |
|-----------|------------|
| GUI | [Flet](https://flet.dev) (Flutter for Python) |
| Speech-to-Text | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CTranslate2) |
| Audio Capture | [sounddevice](https://python-sounddevice.readthedocs.io/) |
| Keyboard Hooks | [pynput](https://pynput.readthedocs.io/) |
| Text Injection | Win32 SendInput (Windows), CGEvents (macOS), Xlib/xdotool (Linux) |
| CI/CD | GitHub Actions (3 OS × 2 Python versions) |

</details>

<details>
<summary><b>Platform support matrix</b></summary>

| Feature | Windows | macOS | Linux (X11) | Linux (Wayland) |
|---------|---------|-------|-------------|-----------------|
| Push-to-talk | Full | Full | Full | Limited |
| Text injection | SendInput | CGEvents | pynput/xdotool | wtype |
| CUDA acceleration | Yes | No | Yes | Yes |
| Window title | Yes | Yes | Yes (xdotool) | No |

</details>

<details>
<summary><b>Project structure</b></summary>

```
whisper-walkie/
├── main.py                    # App logic, GUI, audio, transcription
├── platform_backend/          # Cross-platform abstraction layer
│   ├── __init__.py            # Factory: get_backend()
│   ├── base.py                # PlatformBackend ABC
│   ├── windows.py             # Win32 SendInput + pynput hooks
│   ├── macos.py               # pynput + CGEvents + osascript
│   └── linux.py               # pynput + xdotool/wtype
├── .github/workflows/         # CI + auto-build on version tags
├── requirements.txt           # Pinned Python dependencies
├── WhisperWalkie.spec         # PyInstaller build config
└── tests/                     # Cross-platform test suite
```

</details>

---

## Contributing

Contributions welcome! This is an open-source project by [Joe's Tech Solutions LLC](https://www.joestechsolutions.com).

1. Fork it
2. Create your feature branch (`git checkout -b feature/cool-thing`)
3. Commit your changes
4. Open a Pull Request

CI automatically tests your changes on Windows, macOS, and Linux.

## Why I Built This

I was using tools like [Willow](https://heywillow.io) and [OpenWhispr](https://openwhispr.com/) for voice transcription. They worked — but every word I spoke was going to the cloud, where other companies could use it to train their models. That didn't sit right with me.

I was already running [Ollama](https://ollama.com) and [Open WebUI](https://openwebui.com) for local LLMs. I wanted the same thing for voice: **fast, private, and completely offline.** So I built it.

### Why it's free

I built Whisper Walkie for people like me who care about privacy. I'm giving it away because I want to contribute something real to the open source community — working software for Windows, macOS, and Linux that anyone can use, inspect, and build on.

### How it's built

Whisper Walkie was built entirely using the **agentic AI workflow** with [Claude Code](https://claude.com/claude-code) from Anthropic — proving that one developer with the right tools can ship production-quality, cross-platform software that stands up against anything built by a traditional engineering team. [Read more →](https://joestechsolutions.com/whisper-walkie)

## License

[MIT](LICENSE) — Use it, modify it, ship it. Free forever.

## Author

**Joe Blas** — [Joe's Tech Solutions LLC](https://www.joestechsolutions.com)
- Website: [joestechsolutions.com/whisper-walkie](https://joestechsolutions.com/whisper-walkie)
- GitHub: [joestechsolutions](https://github.com/joestechsolutions)
- LinkedIn: [joseph-blas](https://www.linkedin.com/in/joseph-blas/)
