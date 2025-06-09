# speech_recoginition.py

import queue
import sounddevice as sd
import vosk
import sys
import json
import time

def recognize_speech():
    model_path = "voice_assistant/vosk-model-small-en-us-0.15"
    model = vosk.Model(model_path)

    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("[INFO] Listening...")
        rec = vosk.KaldiRecognizer(model, 16000)

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print(f"[USER] {text}")
                    return text.strip()

def listen_for_confirmation(timeout=10):
    model_path = "voice_assistant/vosk-model-small-en-us-0.15"
    model = vosk.Model(model_path)

    q = queue.Queue()
    start_time = time.time()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("[INFO] Waiting for confirmation...")
        rec = vosk.KaldiRecognizer(model, 16000)

        while True:
            if time.time() - start_time > timeout:
                print("[INFO] Confirmation timeout.")
                return False
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()
                print(f"[USER] {text}")
                if "got that" in text or "yes" in text or "confirm" in text:
                    return True
