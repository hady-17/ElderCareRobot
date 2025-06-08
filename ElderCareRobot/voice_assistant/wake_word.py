import pvporcupine
import sounddevice as sd
import struct

def listen_for_wake_word():
    porcupine = pvporcupine.create(
        access_key="43jn9x1aVe0u/i8E2RGG9XaJGSkAq5ANvj7f8IB4LH24HV/O7oaO4w==",  # Replace with your actual key
        keywords=["computer"]
    )

    def audio_callback(indata, frames, time, status):
        pcm = struct.unpack_from("h" * frames, indata)
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("[INFO] Wake word detected!")
            raise KeyboardInterrupt

    with sd.RawInputStream(samplerate=porcupine.sample_rate,
                           blocksize=porcupine.frame_length,
                           dtype='int16',
                           channels=1,
                           callback=audio_callback):
        print("[INFO] Listening for wake word...")
        try:
            while True:
                pass
        except KeyboardInterrupt:
            pass
        finally:
            porcupine.delete()
            print("[INFO] Wake word detection stopped.")
