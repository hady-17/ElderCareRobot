# voice_assistant/verify_user.py
from speaker_reco.voice_recognition import record_temp_voice, identify_speaker
from voice_assistant.tts import speak

def verify_user_by_voice(expected_name: str, attempts: int = 2):
    """
    Ask the nearby person to speak and verify by voice embedding.
    Returns (is_match: bool, recognized_name: str).
    """
    last = "Unknown"
    for _ in range(attempts):
        speak("Please say: 'It's me' after the beep.")
        wav_path = record_temp_voice()
        who = identify_speaker(wav_path)  # returns "Unknown" on failure
        last = who or "Unknown"
        if who and who.lower() == expected_name.lower():
            return True, who
        speak("I didn't get a confident match. Let's try again.")
    return False, last
