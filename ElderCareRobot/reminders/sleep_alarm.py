# sleep_alarm.py

import json
import re
from datetime import datetime, timedelta
from voice_assistant.tts import speak
from voice_assistant.speech_recoginition import recognize_speech
from face_Recoginition.recognize import recognize_face

ALARM_SCHEDULE_FILE = "sleep_alarm_schedule.json"  # File to store the alarm schedule

def load_alarm_schedule():
    """Load the alarm schedule from the JSON file."""
    try:
        with open(ALARM_SCHEDULE_FILE, "r") as file:
            schedule = json.load(file)
    except FileNotFoundError:
        schedule = {}  # If the file does not exist, return an empty dictionary
    return schedule

def save_alarm_schedule(wake_time_str):
    """Save the wake-up time schedule to the JSON file."""
    alarm_schedule = {
        "wake_time": wake_time_str
    }
    with open(ALARM_SCHEDULE_FILE, "w") as file:
        json.dump(alarm_schedule, file, indent=4)

def clear_alarm_schedule():
    """Clear the alarm schedule in the JSON file."""
    with open(ALARM_SCHEDULE_FILE, "w") as file:
        json.dump({}, file)  # Empty the file by writing an empty dictionary

def handle_sleep_alarm(name, command):
    """Handle setting the wake-up alarm based on spoken time input in 12-hour format."""
    
    # Handle "wake me up after X hours"
    if "after" in command or "for" in command:
        match = re.search(r"(\w+)\s*hours?", command)  # Match word time like "one hour"
        if match:
            hours_word = match.group(1)
            # Convert word to number (e.g., "one" to 1)
            hours_map = {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
                "eleven": 11, "twelve": 12
            }
            hours = hours_map.get(hours_word.lower(), None)
            if hours is None:
                speak("Sorry, I didn't understand the number of hours.")
                return None
            wake_time = datetime.now() + timedelta(hours=hours)
            wake_time_str = wake_time.strftime("%I:%M %p")  # 12-hour format (e.g., "3:00 PM")
            print(f"Time set after {hours} hours: {wake_time_str}")  # Debug print
        else:
            speak("Sorry, I couldn't understand the time you mentioned.")
            return None

    # Handle "wake me up at X AM/PM" (12-hour format)
    elif "at" in command or "till" in command:
        time_str = re.search(r"(at|till)\s*(\d{1,2})\s*(AM|PM|am|pm)", command)  # Match format like "3 AM"
        if time_str:
            hour = int(time_str.group(2))  # Extract the hour (e.g., 3)
            period = time_str.group(3).upper()  # Extract AM/PM (e.g., "PM")
            
            # Convert to 24-hour format
            if period == "PM" and hour != 12:
                hour += 12  # Convert PM hour to 24-hour format (e.g., "3 PM" -> 15)
            elif period == "AM" and hour == 12:
                hour = 0  # Convert 12 AM to 00:00 (midnight)
            
            wake_time_str = f"{hour:02d}:00"  # Format the time as "13:00"
            print(f"Time parsed: {wake_time_str}")  # Debug print
        else:
            speak("Sorry, I couldn't understand the time format you provided.")
            return None

    else:
        speak("At what time would you like me to wake you up?")
        wake_time_str = recognize_speech()  # Capture time from speech
        try:
            wake_time = datetime.strptime(wake_time_str, "%I:%M %p")  # Expecting 12-hour format (e.g., "3:00 PM")
            wake_time_str = wake_time.strftime("%I:%M %p")  # Convert to 12-hour format
            print(f"Time from speech: {wake_time_str}")  # Debug print
        except ValueError:
            speak("Sorry, I couldn't understand the time you provided.")
            return None

    # Save the wake-up time to the JSON file
    save_alarm_schedule(wake_time_str)

    # Notify the elder about the alarm
    speak(f"Wake-up alarm set for {name} at {wake_time_str}.")
    return wake_time_str  # Return the wake-up time for further processing

def trigger_random_alarm(name, attempts=5):
    """Trigger random alarm if face recognition fails after several attempts."""
    retries = 0
    while retries < attempts:
        # Attempt face recognition
        if recognize_face() == name:
            speak(f"Good morning {name}! Time to wake up!")
            return True  # Successfully woke up the elder

        retries += 1
        speak(f"Attempt {retries}: I couldn't recognize you. Trying again...")
    
    # If face recognition failed multiple times, trigger random alarm
    random_alarms = [
        "Wake up! Time to start your day!",
        "Good morning! Rise and shine!",
        "Time to wake up, let's start your day!",
        "Good morning, it's time to get up!"
    ]
    alarm = random.choice(random_alarms)
    speak(alarm)
    return False  # The alarm is triggered, but face recognition failed

def check_due_sleep_alarm(name):
    """Check if the wake-up alarm is due and trigger it."""
    schedule = load_alarm_schedule()
    if "wake_time" in schedule:
        wake_time_str = schedule["wake_time"]
        now = datetime.now().strftime("%I:%M %p")  # Get current time in 12-hour format

        if wake_time_str == now:
            speak(f"Good morning {name}! It’s time to wake up!")
            # Trigger the alarm and face recognition
            if recognize_face() == name:
                speak(f"Good morning {name}! Time to wake up!")
                clear_alarm_schedule()  # Clear the alarm schedule after waking up
                return True  # Successfully woke up the elder
            else:
                trigger_random_alarm(name)  # Retry with random alarm
                return False
    return False
