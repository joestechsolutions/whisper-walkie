# Social Media Launch Posts — Whisper Walkie

---

## Twitter/X — Launch Announcement

I built a free voice typing app that works in ANY window on your computer.

Hold a key. Speak. Release. Text appears.

- 100% local (your audio never leaves your machine)
- Works in any app (browser, Slack, VS Code, Word, anything)
- Free & open source (MIT)
- Windows, macOS, Linux

https://github.com/joestechsolutions/whisper-walkie

---

## Twitter/X — Thread (post as replies)

**1/5** Every voice typing tool I tried was broken in the same way:
- Cloud-based (your voice goes to servers you don't control)
- Only works in one app (Chrome extension that doesn't help in Slack)
- $10-20/month subscriptions

So I built Whisper Walkie.

**2/5** How it works:
1. Hold Right Alt (or any key you pick)
2. Speak into your mic
3. Release
4. Text appears wherever your cursor is

No clipboard. No paste. It types directly via your OS keyboard API. Works in literally any window.

**3/5** Privacy is not a feature — it's the architecture.

Whisper Walkie runs OpenAI's Whisper model locally on YOUR machine. Audio never touches a network. No accounts. No telemetry. No cloud.

GPU accelerated with NVIDIA CUDA. CPU mode works great too.

**4/5** The whole thing was built with AI-assisted development (@AnthropicAI Claude).

Cross-platform backends, GUI, CI/CD pipeline, NSIS installer, landing page — all built through human + AI collaboration.

This is what the future of software engineering looks like.

**5/5** Free & open source (MIT license). Download for Windows, macOS, or Linux:

https://github.com/joestechsolutions/whisper-walkie/releases/latest

Landing page: https://joestechsolutions.com/whisper-walkie

Star the repo if this is useful!

---

## LinkedIn Post

I just shipped Whisper Walkie — a free, open-source voice typing tool that works in any app on your computer.

The problem: Every voice typing solution I tested either sends your audio to cloud servers, only works in specific apps, or costs $10-20/month.

The solution: A push-to-talk app that runs OpenAI's Whisper model 100% locally. Hold a key, speak, release — text appears wherever your cursor is. Browser, Slack, VS Code, Word, Discord. Anywhere.

Key facts:
- 100% local — audio never leaves your machine
- Works in ANY window via native keyboard injection
- GPU accelerated (NVIDIA CUDA) with CPU fallback
- Free forever (MIT license, open source)
- Windows, macOS, and Linux

Built with AI-assisted development using Claude by Anthropic. The entire app — cross-platform backends, GUI, CI/CD, installer — was developed through human + AI collaboration.

This is what I mean when I say AI amplifies developers, not replaces them.

Download: https://github.com/joestechsolutions/whisper-walkie/releases/latest
Full details: https://joestechsolutions.com/whisper-walkie

#OpenSource #AI #Productivity #VoiceTyping #PrivacyFirst #SpeechToText

---

## Reddit — r/opensource

**Title:** I built a free, local-only voice typing app that works in any window (Whisper Walkie)

**Body:**
Hey r/opensource! I built Whisper Walkie because I was frustrated with cloud-based voice typing tools that either cost money, only work in one app, or send my audio to servers I don't control.

**What it does:**
- Push-to-talk voice typing (hold a key, speak, release)
- Text is typed directly into whatever window has focus
- Works in ANY app — not just browsers

**Why it's different:**
- 100% local using faster-whisper (OpenAI's Whisper via CTranslate2)
- No cloud. No accounts. No telemetry. Audio never leaves your machine.
- GPU accelerated (CUDA on Windows/Linux), CPU works great on all platforms
- The Whisper model is bundled — works offline, no internet needed after download

**Available for:** Windows (installer + portable), macOS, Linux

**Tech stack:** Python, Flet (GUI), faster-whisper, pynput, platform-native keyboard APIs

**License:** MIT

GitHub: https://github.com/joestechsolutions/whisper-walkie

Would love feedback, especially from macOS and Linux users!

---

## Reddit — r/SideProject

**Title:** Shipped my first open-source product: voice typing that's 100% local and works in any app

**Body:**
After watching every voice typing tool charge $10-20/month to send my audio to the cloud, I decided to build my own.

Whisper Walkie is a push-to-talk voice typing app. Hold a key, speak, release — text appears wherever your cursor is. It runs OpenAI's Whisper model entirely on your machine. No cloud, no subscriptions, works offline.

The entire thing was built with AI-assisted development (Claude by Anthropic). It's my first real open-source release and I'm pretty proud of how it turned out.

Free. MIT licensed. Windows/macOS/Linux.

https://github.com/joestechsolutions/whisper-walkie

---

## Hacker News

**Title:** Show HN: Whisper Walkie - Free, local-only push-to-talk voice typing for any app

**Body:**
I built Whisper Walkie because cloud voice typing tools frustrated me: they're expensive, app-specific, and send your audio to servers you don't control.

Whisper Walkie runs OpenAI's Whisper model locally via faster-whisper (CTranslate2). Hold a hotkey, speak, release — text is typed directly into whatever window has focus via platform-native keyboard APIs (Win32 SendInput, CGEvents, Xlib).

Key design decisions:
- Push-to-talk only (no always-listening)
- Keyboard injection, not clipboard (works everywhere without Ctrl+V conflicts)
- pynput for hooks on all platforms (no root on Linux, no keyboard library)
- Model bundled in release (works offline)
- GPU acceleration optional (CUDA on Windows/Linux)

Tech: Python, Flet GUI, faster-whisper, pynput, PyInstaller for builds, NSIS installer for Windows.

MIT licensed. Built with Claude (AI-assisted development).

https://github.com/joestechsolutions/whisper-walkie
