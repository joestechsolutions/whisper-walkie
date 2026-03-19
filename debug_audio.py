import sounddevice as sd
import numpy as np
import wavio
import sys

SAMPLE_RATE = 16000
DURATION = 5  # record for 5 seconds

print("\n--- Available Microphones ---")
devices = sd.query_devices()
input_devices = []

for i, device in enumerate(devices):
    if device['max_input_channels'] > 0:
        print(f"[{i}] {device['name']}")
        input_devices.append(i)

try:
    device_idx = int(input("\nEnter the number of the microphone to test: ") or input_devices[0])
except ValueError:
    device_idx = input_devices[0]

print(f"\nRecording {DURATION} seconds of audio from '{devices[device_idx]['name']}'...")
print("Speak into the microphone now!")

try:
    recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, device=device_idx, dtype='float32')
    sd.wait()  # Wait until recording is finished
    print("Recording finished.")
    
    # Save as WAV file
    filename = "test_audio.wav"
    wavio.write(filename, recording, SAMPLE_RATE, sampwidth=2)
    print(f"Saved audio to {filename}. Please play it to verify your microphone is capturing sound.")
    
except Exception as e:
    print(f"Error recording audio: {e}")
