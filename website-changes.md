# Whisper Walkie — Website Changes for Wayland Support

These changes should be applied to the JTS website repo (`joblas/joestechsolutions-nextjs`).

## 1. Remove "Wayland experimental" label

**File:** `src/app/whisper-walkie/DownloadButton.tsx`
**Line:** 146

Change:
```tsx
note: "X11 fully supported; Wayland experimental",
```
To:
```tsx
note: "Works on X11 and Wayland",
```

## 2. Update Linux quickstart instructions

Wherever the Linux installation section mentions Wayland as experimental or suggests manual terminal setup for Wayland, update to reflect that Wayland is now fully supported automatically.

The app now handles Wayland setup automatically on first launch — no manual steps needed. The only thing the user does is:

1. Extract the `.tar.gz`
2. Double-click `WhisperWalkie`
3. Enter system password when prompted (same as installing any app)
4. Start talking

## 3. Remove any "Wayland experimental" warnings from FAQ

If the FAQ section mentions Wayland limitations or experimental status, update to say Wayland is fully supported.

## Summary

Wayland support is no longer experimental. The app auto-detects Wayland, installs required dependencies (`wtype` for text injection, `input` group for hotkey detection) via a standard system authentication prompt, and restarts itself. Zero terminal interaction required.
