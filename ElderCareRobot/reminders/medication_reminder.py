# medication_reminder.py

import re
import json
import time
import os
from datetime import datetime
import dateparser
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import recognize_speech, listen_for_confirmation

# Get the absolute path to this script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEDICATION_FILE = os.path.join(SCRIPT_DIR, "medication_schedules.json")
MEDICATION_LIST_FILE = os.path.join(SCRIPT_DIR, "brand_meds_lebanon.json")

def load_medication_schedules():
    try:
        with open(MEDICATION_FILE, "r") as f:
            return json.load(f).get("schedules", [])
    except FileNotFoundError:
        return []

def save_medication_schedules(schedules):
    with open(MEDICATION_FILE, "w") as f:
        json.dump({"schedules": schedules}, f, indent=4)

def load_med_list():
    try:
        with open(MEDICATION_LIST_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "medications" in data:
                return data["medications"]
            return data
    except Exception as e:
        print(f"[ERROR] Could not load medication list: {e}")
        return []

MEDICATION_LIST = load_med_list()

def add_medication_schedule(name, time_str, medication_name):
    schedules = load_medication_schedules()
    schedules.append({"name": name, "time": time_str, "medication": medication_name})
    save_medication_schedules(schedules)
    speak(f"Medication reminder saved: {medication_name} at {time_str} for {name}.")

def remove_medication_schedule(name, medication_name):
    schedules = load_medication_schedules()
    new = [s for s in schedules if not (
        s["name"].lower() == name.lower() and 
        s["medication"].lower() == medication_name.lower()
    )]
    if len(new) != len(schedules):
        save_medication_schedules(new)
        speak(f"Removed the medication reminder for {medication_name}.")
    else:
        speak(f"No medication reminder for {medication_name} found.")

def check_medication_schedule(name):
    now = datetime.now().strftime("%H:%M")
    for s in load_medication_schedules():
        if s["name"].lower() == name.lower():
            med_t = s["time"]
            total_diff = abs(
                (int(now[:2]) * 60 + int(now[3:])) -
                (int(med_t[:2]) * 60 + int(med_t[3:]))
            )
            if total_diff <= 5:
                speak(f"It’s time to take your {s['medication']}.")

def get_next_medication(name):
    now = datetime.now()
    upcoming = []
    for s in load_medication_schedules():
        if s["name"].lower() == name.lower():
            t = datetime.strptime(s["time"], "%H:%M").time()
            if t >= now.time():
                upcoming.append((t, s))
    if not upcoming:
        return None
    upcoming.sort(key=lambda x: x[0])
    return upcoming[0][1]

def handle_add_medication_conversation(name):
    speak("Please tell me the medication you'd like to add.")
    start = time.time()
    while time.time() - start < 20:
        resp = recognize_speech()
        if not resp:
            speak("I couldn't hear you. Please repeat.")
            continue

        response_text = resp.strip().lower()
        print(f"[DEBUG] User said: '{response_text}'")
        print(f"[DEBUG] Medication list: {MEDICATION_LIST}")

        match = next(
            (m for m in MEDICATION_LIST if m.lower() in response_text),
            None
        )
        if match:
            speak(f"Did you mean {match}? Please confirm by saying 'yes' or 'no'.")
            if listen_for_confirmation(10):
                speak(f"At what time should I schedule {match}?")
                tstart = time.time()
                while time.time() - tstart < 20:
                    tresp = recognize_speech()
                    if not tresp:
                        speak("Please repeat the time.")
                        continue
                    dt = dateparser.parse(tresp)
                    if dt:
                        timestr = dt.strftime("%H:%M")
                        speak(f"You said {match} at {timestr}. Say 'got that' if it's correct.")
                        if listen_for_confirmation(10):
                            add_medication_schedule(name, timestr, match)
                        else:
                            speak("Confirmation missing. Not saved.")
                        return
                    else:
                        speak("Couldn't parse time. Try again.")
                speak("Time input timed out.")
                return
            else:
                speak("Okay, let's try again. Which medication?")
                continue
        else:
            speak("Medication not recognized. Please try again.")
    speak("Input timed out. Please try later.")

def handle_remove_medication_conversation(name):
    speak("Which medication reminder do you want me to remove?")
    start = time.time()
    while time.time() - start < 20:
        resp = recognize_speech()
        if not resp:
            speak("Please repeat the medication name.")
            continue
        med = resp.strip()
        if med:
            speak(f"Did you say {med}? Please confirm by saying 'yes' or 'no'.")
            if listen_for_confirmation(10):
                remove_medication_schedule(name, med)
                return
            else:
                speak("Let's try again. Which medication to remove?")
    speak("Removal timed out. Please try later.")
