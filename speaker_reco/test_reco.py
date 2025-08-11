# test_voice_match.py

import os
import numpy as np
from scipy.spatial.distance import cosine
from resemblyzer import VoiceEncoder, preprocess_wav

# Configuration
ENCODING_PATH = "voice_encodings"
TEST_WAV = "test_voice.wav"  # Make sure this file exists

def run_speaker_test():
    if not os.path.exists(TEST_WAV):
        print(f"[ERROR] Test WAV not found: {TEST_WAV}")
        return

    if not os.path.exists(ENCODING_PATH) or not os.listdir(ENCODING_PATH):
        print(f"[ERROR] No embeddings found in: {ENCODING_PATH}")
        return

    encoder = VoiceEncoder()
    try:
        test_wav = preprocess_wav(TEST_WAV)
        test_embedding = encoder.embed_utterance(test_wav)
    except Exception as e:
        print(f"[ERROR] Failed to preprocess or encode test audio: {e}")
        return

    best_match = "Unknown"
    min_dist = float("inf")

    print("[TEST] Comparing against known voice embeddings...")
    for file in os.listdir(ENCODING_PATH):
        if file.endswith(".npy"):
            try:
                name = os.path.splitext(file)[0]
                known_embedding = np.load(os.path.join(ENCODING_PATH, file))
                dist = cosine(test_embedding, known_embedding)
                print(f"[COMPARE] {name}: distance = {dist:.3f}")
                if dist < min_dist:
                    best_match = name
                    min_dist = dist
            except Exception as e:
                print(f"[ERROR] Failed to compare with {file}: {e}")

    print(f"\n[RESULT] Closest match: {best_match} (distance = {min_dist:.3f})")
    if min_dist > 0.6:
        print("[WARNING] Voice is above match threshold. Might not be a confident match.")

if __name__ == "__main__":
    run_speaker_test()
