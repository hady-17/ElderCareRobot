import json
from datetime import datetime
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import recognize_speech

MED_FILE = "medication_schedules.json"

def load_medication_schedules():
    try:
        with open(MED_FILE, "r") as f:
            data = json.load(f)
            return data.get("schedules", [])
    except (FileNotFoundError, json.JSONDecodeError):
        print("[WARN] Medication file missing or corrupted.")
        return []

def check_medication_schedule(name):
    schedules = load_medication_schedules()
    now = datetime.now().strftime("%I:%M %p")

    for med in schedules:
        if med["name"].lower() == name.lower() and med["time"] == now:
            speak(f"It’s time to take your medication: {med['medication']} {med['dose']}.")

def get_next_medication(name):
    schedules = load_medication_schedules()
    now = datetime.now()
    upcoming = []

    for med in schedules:
        if med["name"].lower() == name.lower():
            try:
                med_time = datetime.strptime(med["time"], "%I:%M %p")
                med_datetime = now.replace(hour=med_time.hour, minute=med_time.minute)
                if med_datetime >= now:
                    upcoming.append((med_datetime, med))
            except Exception as e:
                print(f"[WARN] Skipping med entry due to time error: {med} — {e}")

    if upcoming:
        upcoming.sort()
        next_med = upcoming[0][1]
        # Add 'done' key if missing, and set it to False by default
        if "done" not in next_med:
            next_med["done"] = False
        return next_med
    return None


def handle_add_medication_conversation(name):
    # Medication additions are not allowed directly
    speak("Medication changes should be done by your caregiver.")
    # TODO: Notify the doctor or caregiver about this request
    print(f"[REQUEST] {name} requested to add medication.")

def handle_remove_medication_conversation(name):
    # Medication removals are not allowed directly
    speak("I can’t remove medications directly. I’ll notify your doctor.")
    # TODO: Notify the doctor or caregiver about this request
    print(f"[REQUEST] {name} requested to remove medication.")
