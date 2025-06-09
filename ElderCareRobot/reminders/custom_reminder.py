# custom_reminder.py

import json
import re
from datetime import datetime, timedelta
from voice_assistant.tts import speak

REMINDER_FILE = "reminders.json"  # Path to the JSON file storing reminders

def load_reminders():
    """Load reminders from a JSON file."""
    try:
        with open(REMINDER_FILE, "r") as file:
            reminders = json.load(file)
    except FileNotFoundError:
        reminders = []  # If the file does not exist, return an empty list
    return reminders

def save_reminders(reminders):
    """Save reminders to the JSON file."""
    with open(REMINDER_FILE, "w") as file:
        json.dump(reminders, file, indent=4)

def extract_task_from_command(command):
    """Extract task (e.g., 'eat' or 'take medicine') from the command."""
    task_match = re.search(r"remind me to (.*)", command)
    if task_match:
        return task_match.group(1).strip()
    return ""

def extract_time_from_command(command):
    """Extract time (e.g., '3:30 PM' or '3 PM') from the command."""
    time_match = re.search(r"at (\d{1,2}:\d{2} (AM|PM)|\d{1,2} (AM|PM))", command)
    if time_match:
        return time_match.group(1)
    return ""

def handle_new_reminder(name, task, time_str):
    """Handle adding a new reminder."""
    if not task or not time_str:
        speak("I could not understand the task or time. Please try again.")
        return

    reminder = {
        "task": task,
        "time": time_str,
        "name": name,
        "type": "once"  # Default reminder type is 'once'
    }

    reminders = load_reminders()
    reminders.append(reminder)
    save_reminders(reminders)

    speak(f"Reminder set for {name}: {task} at {time_str}. This will be a one-time reminder.")

def handle_remove_reminder(name, task):
    """Handle removing a reminder."""
    reminders = load_reminders()

    # Remove the reminder by matching name and task
    reminders = [r for r in reminders if not (r["name"].lower() == name.lower() and r["task"].lower() == task.lower())]
    save_reminders(reminders)

    speak(f"Reminder for {task} removed successfully.")

def handle_modify_reminder(name, old_task, new_task, new_time, new_type):
    """Handle modifying an existing reminder."""
    reminders = load_reminders()

    for r in reminders:
        if r["name"].lower() == name.lower() and r["task"].lower() == old_task.lower():
            r["task"] = new_task if new_task else r["task"]
            r["time"] = new_time if new_time else r["time"]
            r["type"] = new_type if new_type else r["type"]

    save_reminders(reminders)
    speak(f"Reminder for {old_task} updated successfully.")
    
def check_due_reminders(name):
    """Check if any reminder is due for the recognized elder."""
    reminders = load_reminders()
    now = datetime.now().strftime("%I:%M %p")  # Get current time in 12-hour format with AM/PM

    for r in reminders:
        if r["name"].lower() == name.lower() and r["time"] == now:
            speak(f"It’s time to {r['task']}.")
            if r["type"] == "daily":
                next_time = (datetime.now() + timedelta(days=1)).strftime("%I:%M %p")
                r["time"] = next_time  # Update time to next day
                save_reminders(reminders)
