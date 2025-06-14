from voice_assistant.speech_recoginition import recognize_speech

def detect_wake_word(keywords=["jarvis", "rover", "robot", "hey robot"]):
    """
    Listens for any of the defined keywords using Vosk speech recognition.
    Triggers when one of them is detected in spoken text.
    """
    print("[INFO] Listening for wake word (via Vosk)...")

    while True:
        phrase = recognize_speech()
        if phrase:
            print(f"[HEARD]: {phrase}")
            for keyword in keywords:
                if keyword in phrase.lower():
                    print(f"[WAKE WORD DETECTED]: {keyword}")
                    return
