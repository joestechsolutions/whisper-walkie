# Product Mission

## Pitch

Whisper Walkie is a cross-platform push-to-talk speech-to-text desktop app that helps anyone who types — developers, writers, professionals, accessibility users — convert speech to text instantly by providing 100% local, private transcription that types directly into any window. No cloud APIs, no clipboard hacks, no subscriptions.

## Users

### Primary Customers

- **Developers & Power Users**: People who spend all day typing and want a faster input method that works in any app — IDEs, terminals, browsers, chat apps.
- **Privacy-Conscious Users**: Anyone who needs speech-to-text but refuses to send audio to cloud services.
- **Accessibility Users**: People with RSI, motor disabilities, or other conditions that make sustained typing difficult.
- **Content Creators & Writers**: Bloggers, journalists, note-takers who want to capture thoughts quickly.

### User Personas

**The Developer** (25-45)
- **Role:** Software Engineer
- **Context:** Writes code, documentation, and Slack messages all day
- **Pain Points:** Cloud STT sends audio to third parties, clipboard-based tools break workflow, existing tools don't work cross-platform
- **Goals:** Fast local transcription that types directly into any window without interrupting flow

**The Accessibility User** (any age)
- **Role:** Any computer user with motor limitations
- **Context:** Needs voice input as a primary or supplementary text entry method
- **Pain Points:** Commercial solutions are expensive, require subscriptions, or don't work everywhere
- **Goals:** Reliable, free, private voice-to-text that works in every application

## The Problem

### Cloud-Dependent Speech-to-Text

Most speech-to-text tools send your audio to cloud servers for processing. This creates privacy concerns, requires internet connectivity, and often requires paid subscriptions. Users who work with sensitive information or in offline environments are left without options.

**Our Solution:** Run OpenAI's Whisper model entirely on the user's machine — audio never leaves the computer.

### Clipboard-Based Workarounds

Many local STT tools transcribe to a clipboard, requiring the user to manually paste. This breaks workflow and doesn't work in all contexts (games, certain terminal emulators, restricted input fields).

**Our Solution:** Inject text directly via platform-native keystroke APIs (Win32 SendInput, CGEvents, Xlib/xdotool), so it works everywhere a keyboard works.

### Platform Lock-In

Most quality STT desktop tools are Windows-only or macOS-only. Cross-platform users and Linux developers are underserved.

**Our Solution:** A single codebase with a platform abstraction layer that provides native-quality keyboard hooks and text injection on Windows, macOS, and Linux.

## Differentiators

### 100% Local & Private

Unlike Dragon NaturallySpeaking, Google Speech-to-Text, or Otter.ai, Whisper Walkie processes all audio locally using OpenAI's Whisper model. Zero network calls for transcription. Your voice data stays on your machine.

### Universal Text Injection

Unlike clipboard-based tools (e.g., Whisper.cpp frontends, nerd-dictation), Whisper Walkie types directly into the focused window via platform-native APIs. It works in browsers, IDEs, chat apps, games — anywhere a keyboard works.

### Truly Cross-Platform

Unlike most STT desktop tools that target one OS, Whisper Walkie runs on Windows, macOS, and Linux (X11 and Wayland) with platform-native keyboard hooks and text injection on each.

## Key Features

### Core Features

- **Push-to-Talk**: Hold a hotkey, speak, release — transcription types into the focused window. Simple as a walkie-talkie.
- **100% Local Processing**: Whisper model runs on-device. Audio never leaves the computer.
- **GPU Acceleration**: Automatically uses CUDA on Windows/Linux for faster transcription, gracefully falls back to CPU.
- **Direct Text Injection**: Types into any window via platform-native keystroke APIs — no clipboard involved.
- **Cross-Platform**: Works on Windows, macOS, and Linux with native backends for each.

### Usability Features

- **Configurable Hotkey**: Choose from Right Alt, Scroll Lock, Pause, F13, F14, Insert, or Right Ctrl.
- **Transcription History**: Last 10 transcriptions saved with timestamps and one-click copy.
- **Pin to Top**: Optional always-on-top mode so the app stays visible while you work.
- **Microphone Selection**: Choose any detected input device from the UI.

### Integration Features

- **Ollama Integration**: Detects local Ollama models for future AI-powered post-processing.
- **Standalone Exe**: Pre-built Windows executable available — no Python required for end users.
