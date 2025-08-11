# voice_recognition.py

from resemblyzer import VoiceEncoder, preprocess_wav
from scipy.spatial.distance import cosine
import numpy as np
import os
import shutil
import sounddevice as sd
from scipy.io.wavfile import write

encoder = VoiceEncoder()
ENCODING_PATH = os.path.join(os.path.dirname(__file__), "voice_encodings")

TEMP_DIR = "temp"
TEMP_FILE = os.path.join(TEMP_DIR, "temp_voice.wav")

def record_temp_voice(duration=6, sample_rate=16000, filename=TEMP_FILE, min_volume_threshold=0.01):
    """
    Records the user's voice and saves it in the temp/ folder only if sound is detected.
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    print("🎤 Listening for speaker... Please speak now.")

    try:
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()

        # Normalize to float and check volume
        normalized = recording / 32768.0  # int16 to float [-1.0, 1.0]
        volume = np.max(np.abs(normalized))

        if volume < min_volume_threshold:
            print(f"[ERROR] Detected silence or very low volume (max = {volume:.5f}). Skipping.")
            return None

        write(filename, sample_rate, recording)
        print(f"✅ Voice recorded to: {filename} (volume = {volume:.5f})")
        return filename

    except Exception as e:
        print(f"[ERROR] Failed to record audio: {e}")
        return None

def identify_speaker(wav_path=TEMP_FILE, threshold=0.31):
    """
    Identifies the speaker from a .wav file by comparing it with saved embeddings.
    Returns the name of the best match or 'Unknown' if no match is good enough.
    """
    if not wav_path or not os.path.exists(wav_path):
        print(f"[ERROR] File not found or recording failed: {wav_path}")
        _cleanup_temp()
        return "Unknown"

    try:
        test_wav = preprocess_wav(wav_path)
        test_embedding = encoder.embed_utterance(test_wav)
    except Exception as e:
        print(f"[ERROR] Failed to process voice: {e}")
        _cleanup_temp()
        return "Unknown"

    if np.max(np.abs(test_wav)) < 0.01:
        print("[ERROR] Input volume too low. Skipping recognition.")
        _cleanup_temp()
        return "Unknown"

    best_match = "Unknown"
    min_dist = float("inf")
    all_distances = []

    if not os.path.exists(ENCODING_PATH):
        print(f"[ERROR] No embedding directory found at: {ENCODING_PATH}")
        _cleanup_temp()
        return "Unknown"

    npy_files = [f for f in os.listdir(ENCODING_PATH) if f.endswith(".npy")]
    if not npy_files:
        print(f"[ERROR] No speaker embeddings found in: {ENCODING_PATH}")
        _cleanup_temp()
        return "Unknown"

    print("[INFO] Comparing against known speaker embeddings...")
    for file in npy_files:
        try:
            name = os.path.splitext(file)[0]
            known_embedding = np.load(os.path.join(ENCODING_PATH, file))
            dist = cosine(test_embedding, known_embedding)
            all_distances.append((name, dist))
            print(f"[COMPARE] {name}: distance = {dist:.3f}")
            if dist < min_dist and dist < threshold:
                best_match = name
                min_dist = dist
        except Exception as e:
            print(f"[ERROR] Failed to compare with {file}: {e}")

    print("\n[DEBUG] All comparisons:")
    for name, dist in sorted(all_distances, key=lambda x: x[1]):
        print(f"  {name}: {dist:.3f}")

    if best_match == "Unknown" or min_dist >= threshold:
        print(f"[WARNING] No confident match. Returning Unknown.")
        _cleanup_temp()
        return "Unknown"

    print(f"[RESULT] Best match: {best_match} (distance = {min_dist:.3f})")
    _cleanup_temp()
    return best_match

def _cleanup_temp():
    """
    Deletes the temp_voice.wav file and the temp directory.
    """
    try:
        if os.path.exists(TEMP_FILE):
            os.remove(TEMP_FILE)
        if os.path.exists(TEMP_DIR) and not os.listdir(TEMP_DIR):
            os.rmdir(TEMP_DIR)
        elif os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        print("[CLEANUP] Temp folder removed.")
    except Exception as e:
        print(f"[WARN] Temp cleanup failed: {e}")
