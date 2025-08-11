# speech_recoginition.py  (typo kept to match your imports elsewhere)
import queue, sys, json, time, math, os
import sounddevice as sd
import vosk
import numpy as np
import webrtcvad
from difflib import get_close_matches

# =========================
# Config
# =========================
MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", "voice_assistant/vosk-model-small-en-us-0.15")

SAMPLE_RATE = 16000       # Vosk model rate
FRAME_MS    = 20          # 10, 20, or 30 (required by WebRTC VAD). 20ms = good latency.
BLOCKSIZE   = SAMPLE_RATE * FRAME_MS // 1000  # samples per frame (e.g., 320 for 20 ms)
DTYPE       = 'int16'

VAD_AGGRESSIVENESS = int(os.environ.get("VAD_LEVEL", "2"))  # 0..3 (3 = most aggressive)
QUEUE_TIMEOUT_S    = 0.05   # how often we wake up to check the queue (lower -> lower latency)
END_SILENCE_MS     = 250    # grace period of silence to consider utterance done
MIN_SPEECH_MS      = 150    # require a minimum speech duration to avoid returning noise

PRINT_PARTIALS     = False  # set True to print partials live (debug/UI)

# Optional: set a specific input device index via env var
INPUT_DEVICE_INDEX = os.environ.get("INPUT_DEVICE_INDEX")
if INPUT_DEVICE_INDEX is not None:
    try:
        INPUT_DEVICE_INDEX = int(INPUT_DEVICE_INDEX)
    except ValueError:
        INPUT_DEVICE_INDEX = None

# =========================
# Lightweight One-Pole High-Pass (no SciPy)
# =========================
class OnePoleHP:
    """
    Simple 1st-order HP filter:
    y[n] = a * (y[n-1] + x[n] - x[n-1])
    a derived from cutoff & sample rate. Works in float then converts back to int16.
    """
    def __init__(self, cutoff_hz=100.0, sr=SAMPLE_RATE):
        rc = 1.0 / (2 * math.pi * max(1.0, cutoff_hz))
        self.alpha = rc / (rc + 1.0 / sr)
        self.prev_x = 0.0
        self.prev_y = 0.0

    def process(self, x_int16: np.ndarray) -> np.ndarray:
        x = x_int16.astype(np.float32)
        y = np.empty_like(x)
        a = self.alpha
        px = self.prev_x
        py = self.prev_y
        for i in range(x.shape[0]):
            xi = x[i]
            yi = a * (py + xi - px)
            y[i] = yi
            px = xi
            py = yi
        self.prev_x = px
        self.prev_y = py
        y = np.clip(y, -32768, 32767).astype(np.int16)
        return y

# =========================
# Core stream + recognition
# =========================
def _open_model():
    try:
        return vosk.Model(MODEL_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to load Vosk model at '{MODEL_PATH}': {e}")
        return None

def _make_stream(callback):
    kwargs = dict(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCKSIZE,
        dtype=DTYPE,
        channels=1,
        callback=callback,
        latency='low'
    )
    if INPUT_DEVICE_INDEX is not None:
        kwargs["device"] = INPUT_DEVICE_INDEX
    try:
        return sd.RawInputStream(**kwargs)
    except Exception as e:
        print("[ERROR] Could not open input stream. Listing devices:")
        try:
            print(sd.query_devices())
        except Exception as e2:
            print(f"[ERROR] query_devices failed: {e2}")
        print("[HINT] Pick the input index with 'max_input_channels' > 0 and set env var INPUT_DEVICE_INDEX.")
        print(f"[DETAILS] {e}")
        return None

def _now_ms():
    return int(time.time() * 1000)

def _make_recognizer(model, choices):
    """
    If 'choices' provided, create a grammar-biased recognizer.
    Otherwise, freeform recognizer.
    """
    if choices:
        grammar = json.dumps(choices, ensure_ascii=False)
        rec = vosk.KaldiRecognizer(model, SAMPLE_RATE, grammar)
        try:
            rec.SetWords(True)
            rec.SetMaxAlternatives(5)
        except Exception:
            pass
    else:
        rec = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    return rec

def _map_to_choice(text_or_json, choices):
    """
    Map recognized output to the closest allowed command.
    Accepts either a string (final text) or a Vosk result dict.
    """
    if not choices:
        # freeform
        if isinstance(text_or_json, dict):
            return (text_or_json.get("text") or "").strip() or None
        return (text_or_json or "").strip() or None

    # Normalize inputs
    if isinstance(text_or_json, dict):
        text = (text_or_json.get("text") or "").strip()
        alts = [a.get("text","").strip() for a in text_or_json.get("alternatives", []) if a.get("text")]
        candidates = [t for t in [text] + alts if t]
    else:
        candidates = [(text_or_json or "").strip()]

    # 1) exact/contains
    for t in candidates:
        for c in choices:
            if c in t or t in c:
                return c

    # 2) fuzzy (closest)
    for t in candidates:
        m = get_close_matches(t, choices, n=1, cutoff=0.6)
        if m:
            return m[0]
    return None

def _stream_and_recognize(timeout=10, confirm_mode=False, use_vad=True, choices=None):
    """
    Returns:
      - recognize_speech: str | None
      - listen_for_confirmation: bool
    """
    model = _open_model()
    if model is None:
        return None if not confirm_mode else False

    q = queue.Queue()
    hp = OnePoleHP(cutoff_hz=100.0, sr=SAMPLE_RATE)
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS) if use_vad else None

    def callback(indata, frames, t, status):
        if status:
            print(f"[AUDIO STATUS] {status}", file=sys.stderr)
        q.put(bytes(indata))

    stream = _make_stream(callback)
    if stream is None:
        return None if not confirm_mode else False

    with stream:
        print("[INFO] Waiting for confirmation..." if confirm_mode else "[INFO] Listening...")
        rec = _make_recognizer(model, choices)

        buf = b""
        frame_bytes = 2 * BLOCKSIZE  # int16 -> 2 bytes
        start_time = time.time()
        last_voice_time_ms = _now_ms()
        speech_start_ms = None
        had_speech = False

        while True:
            # read from queue frequently to keep latency low
            try:
                data = q.get(timeout=QUEUE_TIMEOUT_S)
            except queue.Empty:
                data = b""

            if data:
                buf += data

            # Process in VAD-sized frames
            while len(buf) >= frame_bytes:
                frame = buf[:frame_bytes]
                buf = buf[frame_bytes:]

                samples = np.frombuffer(frame, dtype=np.int16)
                samples = hp.process(samples)
                frame = samples.tobytes()

                is_speech = True
                if vad:
                    try:
                        is_speech = vad.is_speech(frame, SAMPLE_RATE)
                    except Exception as e:
                        print(f"[WARN] VAD error ({e}). Disabling VAD.")
                        vad = None
                        is_speech = True

                now_ms = _now_ms()
                if is_speech:
                    if not had_speech:
                        speech_start_ms = now_ms
                    had_speech = True
                    last_voice_time_ms = now_ms

                    # Feed to recognizer
                    if rec.AcceptWaveform(frame):
                        # If Vosk already thinks this is a full utterance, finalize immediately
                        result = json.loads(rec.Result())
                        if confirm_mode:
                            lt = (result.get("text") or "").lower()
                            print(f"[USER] {lt}")
                            if any(k in lt for k in ("got that","yes","confirm","okay","ok","done","stop","cancel")):
                                return True
                        else:
                            mapped = _map_to_choice(result, choices)
                            if mapped:
                                raw = result.get("text","")
                                print(f"[USER] {mapped}" + (f"  (raw: {raw})" if choices else ""))
                                return mapped
                    else:
                        if PRINT_PARTIALS:
                            partial = json.loads(rec.PartialResult()).get("partial", "")
                            if partial:
                                print(f"[PARTIAL] {partial}")

                else:
                    # just transitioned to silence after speech?
                    if had_speech:
                        # Only finalize if we spoke long enough
                        spoke_long_enough = (speech_start_ms is not None and
                                             (now_ms - speech_start_ms) >= MIN_SPEECH_MS)
                        # Apply a short grace period of silence so we don't cut off too fast
                        if (now_ms - last_voice_time_ms) >= END_SILENCE_MS and spoke_long_enough:
                            final = json.loads(rec.FinalResult())
                            if confirm_mode:
                                lt = (final.get("text") or "").lower()
                                print(f"[USER] {lt}")
                                if any(k in lt for k in ("got that","yes","confirm","okay","ok","done","stop","cancel")):
                                    return True
                            else:
                                mapped = _map_to_choice(final, choices)
                                if mapped:
                                    raw = final.get("text","")
                                    print(f"[USER] {mapped}" + (f"  (raw: {raw})" if choices else ""))
                                    return mapped
                            # reset for next utterance
                            had_speech = False
                            speech_start_ms = None

            # Global timeout (counts silence only)
            if timeout != 0:
                silence_elapsed = (_now_ms() - last_voice_time_ms) / 1000.0
                if silence_elapsed > timeout:
                    print("[INFO] Timeout exceeded, no response.")
                    return None if not confirm_mode else False

# =========================
# Public API
# =========================
def recognize_speech(timeout=10, choices=None):
    """
    If choices is None: returns freeform recognized text (str) or None.
    If choices provided: returns the best matching choice (str) or None.
    """
    return _stream_and_recognize(timeout=timeout, confirm_mode=False, choices=choices)

def listen_for_confirmation(timeout=10):
    """Returns True on affirmative confirmation, False on timeout/negative/no speech."""
    return _stream_and_recognize(timeout=timeout, confirm_mode=True)

# =========================
# CLI test
# =========================
if __name__ == "__main__":
    # Quick smoke test: say something from the choices
    print("Say something… (e.g., 'close' / 'wake me up')")
    out = recognize_speech(
        timeout=8,
        choices=["close","end","exit","wake me up","remind me","remove sleep alarm",
                 "add sleep alarm","medication","emergency","what are my reminders",
                 "list my reminders","sleep alarm","my sleep"]
    )
    print("RESULT:", out)
