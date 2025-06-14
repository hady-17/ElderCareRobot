import json
import re
from datetime import datetime, timedelta
from dateparser import parse
from word2number import w2n
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import recognize_speech

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
    match = re.search(r"at ([a-zA-Z0-9 :]+)", prompt)
    task = re.sub(r"remind me to |remember me to ", "", prompt, flags=re.IGNORECASE)

    if match:
        time_phrase = match.group(1).strip()
        task = task.replace(f"at {time_phrase}", "").strip()

        parsed = parse(time_phrase)
        if not parsed:
            converted = convert_written_time(time_phrase)
            if converted:
                parsed = parse(converted)

        if parsed:
            return task.strip(), parsed.strftime("%I:%M %p")

    return task.strip(), None

def load_reminders():
    try:
        with open(REMINDER_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_reminders(reminders):
    with open(REMINDER_FILE, "w") as f:
        json.dump(reminders, f, indent=4)

def save_reminder(name, task, time_str):
    reminders = load_reminders()
    reminders.append({
        "name": name,
        "task": task,
        "time": time_str,
        "type": "once"
    })
    save_reminders(reminders)
    speak(f"Reminder set for {name} to {task} at {time_str}.")

def check_due_reminders(name):
    """Check if any reminder is due for the recognized elder."""
    reminders = load_reminders()
    now = datetime.now()
    now_str = now.strftime("%I:%M %p")
    print(f"[DEBUG] Checking reminders at {now_str} for {name}")

    updated = []

    for r in reminders:
        reminder_time = r.get("time")
        reminder_name = r.get("name")
        reminder_task = r.get("task")

        try:
            rem_time_obj = datetime.strptime(reminder_time, "%I:%M %p")
        except ValueError:
            print(f"[WARN] Invalid time format in reminder: {reminder_time}")
            updated.append(r)
            continue

        # Use today's date with reminder's time
        rem_time_today = now.replace(hour=rem_time_obj.hour, minute=rem_time_obj.minute, second=0, microsecond=0)

        # Compare time difference
        time_diff = abs((now - rem_time_today).total_seconds())

        if (name == "all" or reminder_name.lower() == name.lower()) and time_diff <= 60:
            print(f"[MATCH] It's time for: {reminder_task} ({reminder_time})")
            speak(f"It’s time to {reminder_task}.")
            if r.get("type") != "daily":
                continue  # Don't re-add if it's once
            else:
                updated.append(r)  # Keep daily reminder
        else:
            updated.append(r)

    save_reminders(updated)

def handle_interactive_reminder(name, initial_prompt=None):
    if initial_prompt:
        task, time_str = extract_task_and_time(initial_prompt)
        if task and time_str:
            save_reminder(name, task, time_str)
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
        save_reminder(name, task, time_str)
    else:
        speak("Sorry, I couldn't understand the time. Please try again.")
