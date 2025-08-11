# tts.py
import os
import pyttsx3
import threading

speak_lock = threading.Lock()

def speak(text):
    try:
        with speak_lock:
            print(f"[USER] {text}")
            # Generate speech file
            os.system(f'pico2wave -w /tmp/tts.wav "{text}" && aplay /tmp/tts.wav')
    except Exception as e:
        print(f"[ERROR] TTS failed: {e}")
