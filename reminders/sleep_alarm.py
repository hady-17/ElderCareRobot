import json
from datetime import datetime
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import recognize_speech
from dateparser import parse
from word2number import w2n
import time
from notifications import send_telegram_notification
#from face_Recoginition.videoPersonDetection import search_for_person_only
from LapTestCode import search_for_person_only
SLEEP_ALARM_FILE = "sleep_alarm.json"
import re

# Add near the top (after imports)
NUMBER_WORDS = {
    "zero","oh","o","one","two","three","four","five","six","seven","eight","nine","ten",
    "eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen",
    "twenty","thirty","forty","fifty"
}
HOMOPHONE_FIXES = {
    "for": "four",
    "to": "two",
    "too": "two",
    "won": "one",
    "tree": "three",
    "free": "three",     # optional (common accent)
    "sex": "six",
    "ate": "eight",
    "oh": "zero",
    "o": "zero",
    "shifting": "fifteen",  # e.g., "shifting pm" -> "fifteen pm"
    
}

def _normalize_time_words(s: str) -> str:
    """Light homophone fixes only when used in a time phrase."""
    s = s.lower().strip()
    s = s.replace("a m", "am").replace("p m", "pm")
    tokens = re.split(r"\s+", s)
    has_time_marker = any(t in ("am","pm") for t in tokens) or "in the morning" in s or "in the evening" in s

    def looks_like_number_word(tok):
        return tok.isdigit() or tok in NUMBER_WORDS or re.fullmatch(r"\d{1,2}(:\d{1,2})?", tok) is not None

    out = []
    for i, t in enumerate(tokens):
        nxt = tokens[i+1] if i+1 < len(tokens) else ""
        # Only fix homophones if we detect a time context or a numeric word follows
        if t in HOMOPHONE_FIXES and (has_time_marker or looks_like_number_word(nxt)):
            out.append(HOMOPHONE_FIXES[t])
        else:
            out.append(t)
    s = " ".join(out)
    # Normalize hyphens (e.g., "thirty-five")
    s = s.replace("-", " ")
    return s

# Replace your existing convert_to_12hr_format with this version
def convert_to_12hr_format(time_str):
    """Convert spoken or written time into 12-hour format (handles up to 6-word phrases)."""
    if not time_str:
        return None

    # NEW: normalize homophones and spacing first
    time_str = _normalize_time_words(time_str)
    time_str = time_str.replace("at", " ").strip()

    from dateparser import parse
    from word2number import w2n

    parsed = parse(time_str)
    if parsed:
        return parsed.strftime("%I:%M %p").upper()

    try:
        # Handle wordy forms ourselves
        words = (time_str
                 .replace("in the morning", "am")
                 .replace("in the evening", "pm")
                 .split())

        # e.g., "four pm"
        if len(words) == 2 and words[1] in ("am","pm"):
            hour = w2n.word_to_num(words[0])
            return f"{hour}:00 {words[1].upper()}"

        # e.g., "four thirty pm"
        if len(words) == 3 and words[2] in ("am","pm"):
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(words[1])
            if minute >= 60:
                return None
            return f"{hour}:{minute:02d} {words[2].upper()}"

        # e.g., "four thirty five pm"
        if len(words) == 4 and words[3] in ("am","pm"):
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(f"{words[1]} {words[2]}")
            if minute >= 60:
                return None
            return f"{hour}:{minute:02d} {words[3].upper()}"

        # e.g., "four thirty in the morning"
        if len(words) == 6 and words[-3:] == ["in","the","morning"]:
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(f"{words[1]} {words[2]}")
            if minute >= 60:
                return None
            return f"{hour}:{minute:02d} AM"

        # e.g., "four thirty in the evening"
        if len(words) == 6 and words[-3:] == ["in","the","evening"]:
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(f"{words[1]} {words[2]}")
            if minute >= 60:
                return None
            return f"{hour}:{minute:02d} PM"

        # single hour like "four"
        if len(words) == 1:
            hour = w2n.word_to_num(words[0])
            # leave AM/PM undecided; your caller can ask a follow-up if needed
            return f"{hour}:00"
    except Exception as e:
        print(f"[ERROR] Failed to convert spoken time: {e}")
        return None

    return None


def load_sleep_alarms():
    try:
        with open(SLEEP_ALARM_FILE, "r") as f:
            data = json.load(f)
            return data.get("sleep_alarms", [])
    except (FileNotFoundError, json.JSONDecodeError):
        print("[WARN] Sleep alarm file missing or corrupted.")
        return []

def save_sleep_alarms(alarms):
    with open(SLEEP_ALARM_FILE, "w") as f:
        json.dump({"sleep_alarms": alarms}, f, indent=4)

def add_sleep_alarm(name, task, time_str, alarm_type="once"):
    time_str = convert_to_12hr_format(time_str)
    if time_str is None:
        speak("I couldn't understand the time. Please try again.")
        return

    alarms = load_sleep_alarms()
    alarms.append({
        "name": name,
        "task": task,
        "time": time_str,
        "type": alarm_type,
        "done": False
    })
    save_sleep_alarms(alarms)
    speak(f"Alarm set for {name} to {task} at {time_str} ({alarm_type}).")

def remove_sleep_alarm(name, task):
    alarms = load_sleep_alarms()
    alarms = [a for a in alarms if not (a["name"].lower() == name.lower() and a["task"].lower() == task.lower())]
    save_sleep_alarms(alarms)
    speak(f"Alarm for {task} has been removed.")


def check_due_sleep_alarm(name):
    alarms = load_sleep_alarms()
    now = datetime.now().strftime("%I:%M %p").upper()
    print(f"[DEBUG] Checking sleep alarms for {name} at {now}")

    for alarm in alarms:
        if alarm["name"].lower() == name.lower() and alarm["time"].upper() == now and not alarm["done"]:
            # NEW: scan area first (no face ID) because elder may be asleep
            present = search_for_person_only(timeout_sec=60)  # NEW
            if not present:
                send_telegram_notification(
                    f"⚠️ Sleep alarm '{alarm['task']}' for {alarm['name']} at {now}: no person detected nearby. Will retry."
                )  # Telegram utility:contentReference[oaicite:5]{index=5}
                time.sleep(10)
                continue

            # Existing announce + repeat-until-ack flow
            print(f"[DEBUG] Found due alarm: {alarm}")
            speak(f"Sorry for interrupting you. It's time to {alarm['task']}. Please say 'done', 'got it', or 'stop'.")
            acknowledged = False
            while not acknowledged:
                response = recognize_speech(timeout=6)  # Vosk STT:contentReference[oaicite:6]{index=6}
                if response:
                    response = response.lower()
                    if any(word in response for word in ["done", "got it", "stop"]):
                        speak(f"Sleep alarm for {alarm['task']} acknowledged.")
                        alarm["done"] = True
                        save_sleep_alarms(alarms)
                        acknowledged = True
                        send_telegram_notification(
                            f"Sleep alarm for {alarm['task']} acknowledged by {name} at {now}."
                        )  # Telegram notify:contentReference[oaicite:7]{index=7}
                    else:
                        speak(f"Still waiting for acknowledgment. Repeating sleep alarm for {alarm['task']}.")
                        time.sleep(10)
                else:
                    speak(f"Timeout reached. Repeating sleep alarm for {alarm['task']}.")
                    send_telegram_notification(
                        f"Sleep alarm for {alarm['task']} not acknowledged by {name} at {now}."
                    )  # Telegram notify:contentReference[oaicite:8]{index=8}
                    time.sleep(10)


def handle_add_sleep_alarm_conversation(name):
    speak("What time should I set the alarm for?")
    #how to handle the case when the user says "at 7 am" or "at 7:30 pm"


    time_str = recognize_speech()
    if not time_str:
        speak("I didn’t hear the time. Please try again.")
        return  
    time_str = convert_to_12hr_format(time_str)
    if time_str is None:
        speak("I couldn't understand the time. Please try again.")
        return  

    speak("Should this alarm repeat daily or just once?")
    repeat_response = recognize_speech()
    alarm_type = "daily" if repeat_response and "daily" in repeat_response.lower() else "once"

    task = "wake up"  # Default task for sleep alarms
    if task:
        add_sleep_alarm(name, task, time_str, alarm_type)
    else:
        speak("I didn’t catch that. Please try again.")

def handle_remove_sleep_alarm_conversation(name):
    speak("What is the task of the alarm you want to remove?")
    task = recognize_speech()
    if task:
        remove_sleep_alarm(name, task)
    else:
        speak("I didn’t catch that. Please try again.")
