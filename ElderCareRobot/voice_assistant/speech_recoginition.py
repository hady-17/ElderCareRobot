# speech_recognition.py

'''import queue
import sounddevice as sd
import vosk
import sys
import json

def recognize_speech():
    model_path = "voice_assistant/vosk-model-small-en-us-0.15"  # adjust as needed
    model = vosk.Model(model_path)

    q = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    # Use the default microphone
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("[INFO] Listening... (Ctrl+C to stop)")
        rec = vosk.KaldiRecognizer(model, 16000)

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                text = json.loads(result)["text"]
                if text:
                    print(f"[USER] {text}")
                    return text  # Return the recognized text
'''
# speech_recognition.py

import queue
import sounddevice as sd
import vosk
import sys
import json

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
                result = rec.Result()
                text = json.loads(result)["text"]
                if text:
                    print(f"[USER] {text}")
                    return text
