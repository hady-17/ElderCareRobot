import json
import re
from datetime import datetime, timedelta
from dateparser import parse
from word2number import w2n
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import recognize_speech
import time

REMINDER_FILE = "custom_reminders.json"

def convert_written_time(phrase):
    phrase = phrase.lower().strip()
    phrase = phrase.replace("in the morning", "am").replace("in the evening", "pm").replace("at ", "")
    words = phrase.split()
    try:
        if len(words) == 2 and words[1] in ("am", "pm"):
            hour = w2n.word_to_num(words[0])
            return f"{hour}:00 {words[1]}"
        elif len(words) == 3 and words[2] in ("am", "pm"):
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(words[1])
            return f"{hour}:{minute:02d} {words[2]}"
        elif len(words) == 2:
            hour = w2n.word_to_num(words[0])
            minute = w2n.word_to_num(words[1])
            return f"{hour}:{minute:02d}"
        elif len(words) == 1:
            hour = w2n.word_to_num(words[0])
            return f"{hour}:00"
    except:
        return None
    return None

def extract_task_and_time(prompt):
    prompt = prompt.lower()
    is_daily = "daily" in prompt

    match = re.search(r"at ([a-zA-Z0-9 :]+)", prompt)
    task = re.sub(r"(remind me to |remember me to )", "", prompt, flags=re.IGNORECASE)
    task = task.replace("daily", "").strip()

    if match:
        time_phrase = match.group(1).strip()
        task = task.replace(f"at {time_phrase}", "").strip()

        parsed = parse(time_phrase)
        if not parsed:
            converted = convert_written_time(time_phrase)
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
                        break
                    else:
                        print(f"[REPEAT] Heard: {response} — not valid acknowledgment.")
                else:
                    print("[REPEAT] No response.")
                time.sleep(10)
                attempts += 1

            if acknowledged:
                if r.get("type") == "daily":
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

    parsed = parse(time_phrase)
    if not parsed:
        converted = convert_written_time(time_phrase)
        if converted:
            parsed = parse(converted)

    if parsed:
        time_str = parsed.strftime("%I:%M %p")

        speak("Should this be a daily reminder or just once?")
        type_response = recognize_speech()
        if type_response and "daily" in type_response.lower():
            reminder_type = "daily"
        else:
            reminder_type = "once"

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
