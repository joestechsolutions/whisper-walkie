"""Quick diagnostic: press keys and see what the keyboard library reports."""
import keyboard
import time

print("=" * 50)
print("HOTKEY DIAGNOSTIC")
print("=" * 50)
print("Press any key to see how the keyboard library sees it.")
print("Try pressing RIGHT ALT specifically.")
print("Press ESC to quit.\n")

def on_event(e):
    print(f"  event_type={e.event_type:<5}  name={e.name!r:<20}  scan_code={e.scan_code}")

keyboard.hook(on_event, suppress=False)

try:
    # Also check what scan codes it resolves for 'right alt'
    try:
        codes = keyboard.key_to_scan_codes('right alt')
        print(f"key_to_scan_codes('right alt') = {codes}")
    except Exception as ex:
        print(f"key_to_scan_codes('right alt') failed: {ex}")

    try:
        codes = keyboard.key_to_scan_codes('alt gr')
        print(f"key_to_scan_codes('alt gr') = {codes}")
    except Exception as ex:
        print(f"key_to_scan_codes('alt gr') failed: {ex}")

    print("\nWaiting for key presses...\n")
    keyboard.wait('esc')
except KeyboardInterrupt:
    pass
finally:
    keyboard.unhook_all()
    print("\nDone.")
