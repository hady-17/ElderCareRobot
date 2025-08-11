# recorder.py

import sounddevice as sd
from scipy.io.wavfile import write
import os

def record_voice(filename="hady.wav", duration=20, sample_rate=16000):
    os.makedirs(os.path.dirname(filename), exist_ok=True) if "/" in filename else None
    print("🎤 Recording started... Speak now.")
    try:
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        write(filename, sample_rate, recording)
        print(f"✅ Voice recorded and saved to: {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to record: {e}")

if __name__ == "__main__":
    record_voice()
