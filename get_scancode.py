import keyboard
print("Press Right Alt now...")
event = keyboard.read_event()
print(f"Key: {event.name}, Scan Code: {event.scan_code}")
