# Wayland Zero-Friction Setup — Design Spec

**Date:** 2026-03-23
**Status:** Approved
**Goal:** Make Whisper Walkie work seamlessly on Wayland with zero terminal interaction.

## Problem

On Wayland, two system-level dependencies are required:
1. **`wtype`** — for text injection (xdotool doesn't work on Wayland)
2. **`input` group membership** — for hotkey detection via `/dev/input/` (pynput uinput backend)

Today, the app silently fails if these are missing. The current PR (#3) shows a dialog with terminal commands — not acceptable for a premium product.

## Design

### User Experience

**On Wayland (first launch, deps missing):**
1. User double-clicks `WhisperWalkie`
2. System authentication dialog appears (standard pkexec prompt — same as installing software from Ubuntu Software)
3. User enters password
4. App restarts automatically (~1 second)
5. Onboarding begins. Everything works.

**On Wayland (subsequent launches):** App opens directly. No prompts.

**On X11 or macOS or Windows:** No change. App opens directly.

### Technical Flow

```
main.py startup
  → _check_and_fix_wayland() runs before GUI
  → Detects XDG_SESSION_TYPE == "wayland"
  → Checks: is wtype installed? Is user in input group?
  → If both OK or not Wayland: continue to GUI
  → If anything missing:
      1. Locate bundled setup-wayland.sh
      2. Run: pkexec /path/to/setup-wayland.sh <username>
      3. If input group was added:
           Re-exec via: sg input -c "/path/to/WhisperWalkie"
           (activates group immediately without logout)
         Else (only wtype was missing):
           Continue normally (wtype works immediately)
      4. Save wayland_setup_complete=true in config
```

### setup-wayland.sh (new, bundled)

Small shell script run via pkexec with root privileges:
- Detects package manager (apt, dnf, pacman)
- Installs `wtype` if not found
- Runs `usermod -aG input <username>` if user not in input group
- Exits

Must be bundled in the PyInstaller build and in the source tree.

### Fallbacks

| Scenario | Behavior |
|----------|----------|
| pkexec not available | Show minimal dialog: "Setup needed" with one copy-able command + "Run Setup" info |
| sg not available | Re-exec without sg; save needs_relogin in config; show "Log out and back in" dialog |
| Non-apt/dnf/pacman distro | Skip wtype install; log warning; text injection falls back to pynput Controller |
| User cancels pkexec | App continues without Wayland fixes; show simple dialog explaining hotkey won't work until setup completes; offer retry button |
| Already set up | Config check skips everything |

### Config Schema Addition

In `~/.whisper-walkie/config.json`:
```json
{
  "wayland_setup_complete": true
}
```

### Files Changed

| File | Change |
|------|--------|
| `main.py` | Replace `_check_wayland_setup()` and `_build_wayland_dialog()` with `_check_and_fix_wayland()` auto-fix flow |
| `setup-wayland.sh` (new) | Root-level helper script for pkexec |
| `WhisperWalkie.spec` | Bundle `setup-wayland.sh` in datas |
| `install-linux.sh` | No changes needed (already handles Wayland) |

### What Gets Removed

- `_check_wayland_setup()` function in main.py
- `_build_wayland_dialog()` function in main.py
- The Wayland dialog UI code (120+ lines of Flet dialog builder)
- `import shutil` added by PR #3 (if no longer needed)

### Testing

1. Run from source on Wayland without input group or wtype → should see pkexec prompt, then app restarts and works
2. Run from source on Wayland with everything set up → should skip straight to app
3. Run from source on X11 → no Wayland flow at all
4. Run release binary on Wayland → same as #1
5. Cancel pkexec dialog → app shows retry option, doesn't crash
6. Run on system without pkexec → shows fallback dialog
