# enroll_voice.py
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import os

encoder = VoiceEncoder()
voice_folder = "voice_samples/hady"          # Folder containing WAV files
output_folder = "voice_encodings"       # Where embeddings are saved

os.makedirs(output_folder, exist_ok=True)

for file in os.listdir(voice_folder):
    if file.endswith(".wav"):
        name = os.path.splitext(file)[0]
        wav_path = os.path.join(voice_folder, file)
        wav = preprocess_wav(wav_path)
        embedding = encoder.embed_utterance(wav)
        np.save(os.path.join(output_folder, f"{name}.npy"), embedding)
        print(f"[SAVED] Voice encoding for: {name}")
