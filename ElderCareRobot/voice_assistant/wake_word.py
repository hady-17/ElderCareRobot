import pvporcupine
import sounddevice as sd
import struct

def listen_for_wake_word():
    porcupine = pvporcupine.create(
        access_key="43jn9x1aVe0u/i8E2RGG9XaJGSkAq5ANvj7f8IB4LH24HV/O7oaO4w==",  # Replace with your actual key
        keywords=["computer"],
        sensitivities=[0.75]  # Adjust as needed
    )

    def audio_callback(indata, frames, time, status):
        if status:
            print(f"[ERROR] {status}")
        pcm = struct.unpack_from("h" * frames, indata)
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("[INFO] Wake word detected!")
            raise KeyboardInterrupt

    try:
        with sd.RawInputStream(
            device=1,  # Adjust based on your mic index
            samplerate=porcupine.sample_rate,
            blocksize=porcupine.frame_length,
            dtype='int16',
            channels=1,
            callback=audio_callback
        ):
            print("[INFO] Listening for wake word...")
            while True:
                pass

    except Exception as e:
        print(f"[ERROR] {e}")

    finally:
        porcupine.delete()
        print("[INFO] Wake word detection stopped.")
