# custom_reminder.py

import re
import json
import time
from datetime import datetime
import schedule
import dateparser
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import listen_for_confirmation

REMINDER_FILE = "reminders.json"

def load_reminders():
    try:
        with open(REMINDER_FILE, "r") as f:
            data = json.load(f)
        return data.get("reminders", [])
    except FileNotFoundError:
        return []

def save_reminders(reminders):
    with open(REMINDER_FILE, "w") as f:
        json.dump({"reminders": reminders}, f, indent=4)

def parse_reminder_command(command):
    pattern = r"(?:remind me|remember me) to (.+?) at (\d{1,2}(:\d{2})?\s*(am|pm)?)"
    match = re.search(pattern, command, re.IGNORECASE)
    if match:
        task = match.group(1).strip()
        time_str = match.group(2).strip()
        dt = dateparser.parse(time_str)
        if dt:
            parsed_time = dt.strftime("%H:%M")
            return task, parsed_time
    return None, None

def parse_remove_command(command):
    pattern = r"(?:cancel|delete|remove) (?:my )?reminder to (.+)"
    match = re.search(pattern, command, re.IGNORECASE)
    if match:
        task = match.group(1).strip()
        return task
    return None

def add_reminder(name, task, time_str):
    reminders = load_reminders()
    reminders.append({"name": name, "task": task, "time": time_str})
    save_reminders(reminders)

def remove_reminder(name, task):
    reminders = load_reminders()
    new_reminders = [r for r in reminders if not (r["name"].lower() == name.lower() and r["task"].lower() == task.lower())]
    if len(new_reminders) != len(reminders):
        save_reminders(new_reminders)
        speak(f"I have removed the reminder to {task} for {name}.")
    else:
        speak(f"No reminder found to {task} for {name}.")

def handle_new_reminder(name, command):
    task, time_str = parse_reminder_command(command)
    if task and time_str:
        speak(f"I heard: remind {name} to {task} at {time_str}. Please confirm by saying 'got that'.")
        confirmed = listen_for_confirmation(timeout=10)
        if confirmed:
            add_reminder(name, task, time_str)
            speak(f"Reminder saved: {task} at {time_str} for {name}.")
        else:
            speak("I did not receive confirmation. The reminder was not saved.")
    else:
        speak("Sorry, I couldn’t understand the reminder. Please try again.")
