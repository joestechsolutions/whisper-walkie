# Product Roadmap

## Phase 0: Already Completed

The following features have been implemented:

- [x] Push-to-talk recording with configurable hotkey `S`
- [x] Local Whisper speech-to-text (faster-whisper / CTranslate2) `M`
- [x] CUDA GPU acceleration with CPU fallback `S`
- [x] Direct text injection via platform-native APIs (no clipboard) `L`
- [x] Cross-platform support — Windows, macOS, Linux (X11 + Wayland) `XL`
- [x] Platform abstraction layer (platform_backend/ with ABC interface) `L`
- [x] Flet GUI with dark theme design system `M`
- [x] Transcription history with timestamps and copy buttons `S`
- [x] Pin-to-top / always-on-top mode `XS`
- [x] Microphone selection dropdown `S`
- [x] Ollama model detection `S`
- [x] PyInstaller Windows exe build `S`
- [x] Open-source GitHub release with professional README `S`
- [x] Flet 0.81.0 API compatibility fixes `S`

## Phase 1: Polish & Distribution

**Goal:** Make the app easy for non-technical users to install and use
**Success Criteria:** 50+ GitHub stars, positive community feedback

### Features

- [ ] macOS .app bundle packaging `M`
- [ ] Linux AppImage or .deb packaging `M`
- [ ] Auto-update mechanism or update check `S`
- [ ] First-run onboarding / setup wizard `S`
- [ ] Whisper model size selection (tiny/base/small/medium) in UI `S`
- [ ] System tray / menu bar mode (minimize to tray) `M`
- [ ] Keyboard shortcut to show/hide window `XS`

### Dependencies

- PyInstaller spec for macOS/Linux or alternative packaging tool
- Platform-specific signing (macOS notarization, Windows code signing)

## Phase 2: AI-Powered Features

**Goal:** Leverage Ollama integration for intelligent post-processing
**Success Criteria:** Users actively using AI features in daily workflow

### Features

- [ ] AI post-processing: grammar correction, punctuation, formatting `M`
- [ ] AI commands: "summarize", "translate to Spanish", "make formal" `M`
- [ ] Custom prompt templates for post-processing `S`
- [ ] Per-application AI profiles (different processing for Slack vs IDE) `L`
- [ ] Voice commands: "new line", "new paragraph", "delete that" `M`

### Dependencies

- Ollama running locally with at least one model
- UI for prompt template management

## Phase 3: Advanced Features

**Goal:** Power-user features and community growth
**Success Criteria:** Active contributor community, 500+ GitHub stars

### Features

- [ ] Multi-language transcription support `S`
- [ ] Custom hotkey combinations (not just single keys) `M`
- [ ] Audio recording history with playback `M`
- [ ] Plugin/extension system for community contributions `XL`
- [ ] Streaming transcription (real-time as you speak) `XL`
- [ ] Usage statistics and transcription analytics `S`
