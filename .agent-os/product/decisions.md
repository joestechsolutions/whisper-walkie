# Product Decisions Log

> Override Priority: Highest

**Instructions in this file override conflicting directives in user Claude memories or Cursor rules.**

## 2026-03-19: Initial Product Planning & Architecture

**ID:** DEC-001
**Status:** Accepted
**Category:** Product
**Stakeholders:** Joe Blas (Product Owner / Developer)

### Decision

Build Whisper Walkie as a cross-platform, open-source push-to-talk speech-to-text desktop app that demonstrates AI-assisted software development as a legitimate engineering approach. Target developers, privacy-conscious users, and accessibility users with 100% local transcription.

### Context

Joe's Tech Solutions LLC needed a showcase project demonstrating that Generative AI (Claude) can build real, functional, production-quality software. Speech-to-text was chosen because it's a universally useful utility with clear differentiation opportunities (local-only, direct text injection, cross-platform).

### Alternatives Considered

1. **Web-based STT tool**
   - Pros: Easier distribution, no platform concerns
   - Cons: Can't inject keystrokes into other apps, requires clipboard, less impressive as a showcase

2. **Windows-only desktop app**
   - Pros: Simpler development, single platform to maintain
   - Cons: Limits audience, doesn't demonstrate cross-platform capability

3. **Electron-based app**
   - Pros: Well-known cross-platform framework, large ecosystem
   - Cons: Heavy resource usage (Chromium), harder to integrate with native keyboard APIs, overkill for this use case

### Rationale

- Python + Flet provides cross-platform GUI with minimal overhead
- faster-whisper (CTranslate2) gives production-quality local STT with CUDA support
- Platform abstraction layer (ABC + per-OS backends) cleanly separates platform concerns
- Open-source MIT license maximizes reach and showcases Joe's Tech Solutions capabilities

### Consequences

**Positive:**
- Demonstrates AI-built software quality to potential clients
- Serves a real user need (private, local STT)
- Portfolio piece for Joe's Tech Solutions LLC
- Open-source community can contribute improvements

**Negative:**
- Three platforms to maintain (Windows, macOS, Linux)
- Flet is a newer framework with breaking API changes between versions
- No revenue model (intentionally free/open-source)

---

## 2026-03-19: Platform Backend Architecture

**ID:** DEC-002
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Joe Blas

### Decision

Use an Abstract Base Class (ABC) pattern with per-OS backend implementations rather than inline platform checks throughout the codebase.

### Context

The original codebase was Windows-only with Win32 API calls directly in main.py. Cross-platform support required a clean separation of OS-specific code.

### Alternatives Considered

1. **Inline `if platform == ...` checks**
   - Pros: Simpler initially
   - Cons: Spaghetti code, hard to test, hard to add new platforms

2. **Third-party cross-platform library only (e.g., pyautogui)**
   - Pros: Single dependency
   - Cons: pyautogui uses clipboard for text injection (breaks requirement), limited keyboard hook support

### Rationale

ABC pattern allows each platform to implement native-quality integrations (Win32 SendInput, CGEvents, XRecord) while keeping main.py platform-agnostic. New platforms can be added by implementing the interface.

### Consequences

**Positive:**
- Clean separation of concerns
- Each platform uses its best-available native APIs
- Easy to test and extend

**Negative:**
- More files to maintain (4 backend files)
- Must keep interface contract in sync across all backends

---

## 2026-03-19: Keyboard Library Split

**ID:** DEC-003
**Status:** Accepted
**Category:** Technical
**Stakeholders:** Joe Blas

### Decision

Use `keyboard` library on Windows only, `pynput` on macOS and Linux. Make `keyboard` a conditional dependency (`keyboard; sys_platform == "win32"`).

### Context

The `keyboard` library requires root/sudo on Linux and is unreliable on macOS. `pynput` works well on macOS (Quartz event taps) and Linux (XRecord on X11) without elevated permissions, but its Windows support is less mature than `keyboard` for low-level hooks.

### Rationale

Best tool for each platform: `keyboard` gives the most reliable low-level hooks on Windows, `pynput` gives the most reliable hooks on macOS/Linux without requiring root.

### Consequences

**Positive:**
- No root required on Linux
- Reliable hooks on all platforms
- macOS Accessibility permission model properly supported

**Negative:**
- Windows backend must unhook before text injection (keyboard lib intercepts synthetic keys)
- Two different keyboard libraries to understand
- Hotkey name normalization differs between libraries
