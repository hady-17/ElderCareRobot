import json
import re
from datetime import datetime, timedelta
from dateparser import parse
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import recognize_speech
from reminders.sleep_alarm import convert_to_12hr_format
import time
from notifications import send_telegram_notification

REMINDER_FILE = "custom_reminders.json"
# --- Homophone-aware time normalization (add below your imports) ---
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
    "free": "three",     # optional, accents
    "sex": "six",
    "ate": "eight",
    "oh": "zero",
    "o": "zero",
    "shifting": "fifteen",  # e.g., "shifting pm" -> "fifteen pm"
}

def _normalize_time_words(s: str) -> str:
    """
    Light homophone fixes only when used in a time phrase.
    e.g., "for thirty pm" -> "four thirty pm"
    """
    s = s.lower().strip()
    s = s.replace("a m", "am").replace("p m", "pm")
    tokens = re.split(r"\s+", s)

    def looks_like_number_word(tok):
        return tok.isdigit() or tok in NUMBER_WORDS or re.fullmatch(r"\d{1,2}(:\d{1,2})?", tok) is not None

    has_time_marker = any(t in ("am","pm") for t in tokens) or "in the morning" in s or "in the evening" in s

    out = []
    for i, t in enumerate(tokens):
        nxt = tokens[i+1] if i+1 < len(tokens) else ""
        # Only fix homophones if we detect time context or a numeric token next
        if t in HOMOPHONE_FIXES and (has_time_marker or looks_like_number_word(nxt)):
            out.append(HOMOPHONE_FIXES[t])
        else:
            out.append(t)

    s = " ".join(out)
    s = s.replace("-", " ")  # handle "thirty-five"
    return s

def extract_task_and_time(prompt):
    prompt = prompt.lower()
    is_daily = "daily" in prompt

    match = re.search(r"at ([a-zA-Z0-9 :]+)", prompt)
    task = re.sub(r"(remind me to |remember me to )", "", prompt, flags=re.IGNORECASE)
    task = task.replace("daily", "").strip()

    if match:
        time_phrase = match.group(1).strip()
        task = task.replace(f"at {time_phrase}", "").strip()

        # NEW: normalize homophones before parsing
        time_phrase_norm = _normalize_time_words(time_phrase)

        parsed = parse(time_phrase_norm)
        if not parsed:
            converted = convert_to_12hr_format(time_phrase_norm)  # already robust in sleep_alarm
            if converted:
                parsed = parse(converted)

        if parsed:
            return task.strip(), parsed.strftime("%I:%M %p"), "daily" if is_daily else "once"

    return task.strip(), None, "daily" if is_daily else "once"


def load_reminders():
    try:
        with open(REMINDER_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("[WARN] Reminder file missing or corrupted. Resetting.")
        return []

def save_reminders(reminders):
    with open(REMINDER_FILE, "w") as f:
        json.dump(reminders, f, indent=4)

def save_reminder(name, task, time_str, reminder_type="once"):
    reminders = load_reminders()
    reminders.append({
        "name": name,
        "task": task,
        "time": time_str,
        "type": reminder_type,
        "done": False
    })
    save_reminders(reminders)
    speak(f"Reminder set for {name} to {task} at {time_str} ({reminder_type}).")


def check_due_reminders(name):
    reminders = load_reminders()
    now = datetime.now()
    now_str = now.strftime("%I:%M %p")
    print(f"[DEBUG] Checking reminders at {now_str} for {name}")

    updated = []

    for r in reminders:
        if r.get("done"):
            updated.append(r)
            continue

        reminder_time = r.get("time")
        reminder_name = r.get("name")
        reminder_task = r.get("task")

        try:
            rem_time_obj = datetime.strptime(reminder_time, "%I:%M %p")
        except ValueError:
            print(f"[WARN] Invalid time format in reminder: {reminder_time}")
            updated.append(r)
            continue

        rem_time_today = now.replace(hour=rem_time_obj.hour, minute=rem_time_obj.minute, second=0, microsecond=0)
        time_diff = abs((now - rem_time_today).total_seconds())

        if (name == "all" or reminder_name.lower() == name.lower()) and time_diff <= 60:
            print(f"[MATCH] It’s time for: {reminder_task} ({reminder_time})")

            acknowledged = False
            max_attempts = 12  # try for up to 2 minutes
            attempts = 0

            while not acknowledged and attempts < max_attempts:
                speak(f"It’s time to {reminder_task}. Please say 'got it' or 'stop' to confirm.")
                print("[WAITING] Listening for acknowledgment...")
                response = recognize_speech()
                if response:
                    response = response.lower()
                    if any(word in response for word in ["got it", "cancel", "close", "stop"]):
                        acknowledged = True
                        print(f"[ACK] Acknowledged: {response}")
                        send_telegram_notification(f"The elder has acknowledged the reminder: {reminder_task}.")
                        break
                    else:
                        print(f"[REPEAT] Heard: {response} — not valid acknowledgment.")
                else:
                    print("[REPEAT] No response.")
                    send_telegram_notification(f"Waiting for acknowledgment for reminder: {reminder_task}.")
                time.sleep(10)
                attempts += 1

            if acknowledged:
                if r.get("type") == "daily":
                    send_telegram_notification(f"Reminder for {reminder_task} acknowledged. It will repeat daily.")
                    updated.append(r)
                else:
                    r["done"] = True
                    updated.append(r)
                    print(f"[INFO] Marked reminder as done: {r}")
        else:
            updated.append(r)

    save_reminders(updated)

def handle_interactive_reminder(name, initial_prompt=None):
    if initial_prompt:
        task, time_str, reminder_type = extract_task_and_time(initial_prompt)
        if task and time_str:
            save_reminder(name, task, time_str, reminder_type)
            return
        else:
            speak("I couldn't understand the full reminder. Let's go step by step.")

    speak("What do you want me to remind you about?")
    task = recognize_speech()
    if not task:
        speak("I didn't catch that. Please try again later.")
        return

    speak("At what time should I remind you?")
    time_phrase = recognize_speech()
    if not time_phrase:
        speak("I didn’t hear the time. Please try again later.")
        return

    # NEW: normalize first
    time_phrase_norm = _normalize_time_words(time_phrase)

    parsed = parse(time_phrase_norm)
    if not parsed:
        converted = convert_to_12hr_format(time_phrase_norm)
        print(f"[DEBUG] Raw time phrase: {converted}")
        if converted:
            parsed = parse(converted)

    if parsed:
        time_str = parsed.strftime("%I:%M %p")
        print(f"[DEBUG] Final reminder time: {time_str}")
        speak("Should this be a daily reminder or just once?")
        type_response = recognize_speech()
        reminder_type = "daily" if (type_response and "daily" in type_response.lower()) else "once"
        save_reminder(name, task, time_str, reminder_type)
    else:
        speak("Sorry, I couldn't understand the time. Please try again.")


def remove_old_done_reminders(days=2):
    cutoff_time = datetime.now() - timedelta(days=days)
    reminders = load_reminders()
    cleaned = []

    for r in reminders:
        if r.get("done") and r.get("type") == "once":
            try:
                rem_time = datetime.strptime(r["time"], "%I:%M %p")
                reminder_datetime = datetime.combine(cutoff_time.date(), rem_time.time())
                if reminder_datetime < cutoff_time:
                    print(f"[CLEANUP] Removed old one-time reminder: {r}")
                    continue
            except Exception as e:
                print(f"[ERROR] Failed to parse reminder time for cleanup: {r['time']} - {e}")
                continue
        cleaned.append(r)

    save_reminders(cleaned)
