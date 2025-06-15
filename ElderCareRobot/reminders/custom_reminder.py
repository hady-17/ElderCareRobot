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
            speak(f"It’s time to {reminder_task}.")
            if r.get("type") == "daily":
                updated.append(r)
            else:
                print(f"[INFO] Marking one-time reminder as done: {reminder_task}")
                r["done"] = True
                updated.append(r)
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

def list_reminders_for(name):
    reminders = load_reminders()
    user_reminders = [r for r in reminders if r["name"].lower() == name.lower() and not r.get("done")]

    if not user_reminders:
        speak("You have no upcoming reminders.")
        return

    speak(f"You have {len(user_reminders)} reminder{'s' if len(user_reminders) > 1 else ''}:")
    for idx, r in enumerate(user_reminders, start=1):
        speak(f"{idx}. {r['task']} at {r['time']} ({r['type']})")

    speak("Would you like to modify or delete one? Say the number of the reminder.")

    response = recognize_speech()
    if not response:
        speak("No response received.")
        return

    match = re.search(r"(\d+)", response)
    if not match:
        speak("I couldn't understand the number. Please try again next time.")
        return

    index = int(match.group(1)) - 1
    if 0 <= index < len(user_reminders):
        selected = user_reminders[index]
        speak(f"Do you want to modify or delete reminder {index + 1}?")
        action = recognize_speech()

        if action and "delete" in action.lower():
            all_reminders = load_reminders()
            all_reminders = [r for r in all_reminders if r != selected]
            save_reminders(all_reminders)
            speak(f"Reminder number {index + 1} has been deleted.")

        elif action and "modify" in action.lower():
            speak("What should be the new task?")
            new_task = recognize_speech()

            speak("What time should I remind you?")
            new_time = recognize_speech()
            parsed_time = parse(new_time)
            if not parsed_time:
                speak("I couldn't understand the time. Canceling modification.")
                return

            speak("Should this be daily or once?")
            new_type_response = recognize_speech()
            new_type = "daily" if new_type_response and "daily" in new_type_response.lower() else "once"

            selected['task'] = new_task if new_task else selected['task']
            selected['time'] = parsed_time.strftime("%I:%M %p")
            selected['type'] = new_type
            selected['done'] = False

            all_reminders = load_reminders()
            for i, r in enumerate(all_reminders):
                if r == user_reminders[index]:
                    all_reminders[i] = selected
                    break

            save_reminders(all_reminders)
            speak(f"Reminder number {index + 1} has been updated.")
        else:
            speak("Okay, no changes made.")
    else:
        speak("Invalid reminder number.")
