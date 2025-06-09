# main.py

from face_Recoginition.recognize import recognize_face
from voice_assistant.speech_recoginition import recognize_speech
from voice_assistant.tts import speak
from reminders.custom_reminder import (
    handle_new_reminder,
    load_reminders,
    parse_remove_command,
    remove_reminder
)
from reminders.medication_reminder import (
    check_medication_schedule,
    handle_add_medication_conversation,
    handle_remove_medication_conversation,
    get_next_medication
)
from datetime import datetime
import time

def check_due_reminders(name):
    reminders = load_reminders()
    now = datetime.now().strftime("%H:%M")
    for r in reminders:
        if r["name"].lower() == name.lower():
            reminder_time = r["time"]
            reminder_hour, reminder_minute = map(int, reminder_time.split(":"))
            now_hour, now_minute = map(int, now.split(":"))
            if abs((now_hour * 60 + now_minute) - (reminder_hour * 60 + now_minute)) <= 5:
                speak(f"It’s time to {r['task']}.")

def main():
    print("[INFO] Elder Care Rover is starting up...")

    while True:
        # Detect elder face
        name = recognize_face()
        if name != "Unknown":
            speak(f"Hello, {name}! How can I assist you today?")
            check_due_reminders(name)
            check_medication_schedule(name)

            while True:
                command = recognize_speech()
                if not command:
                    continue
                command = command.lower()

                if "end" in command or "end it" in command:
                    speak("Ending conversation. Awaiting next elder.")
                    break

                elif "remind me" in command or "remember me" in command:
                    handle_new_reminder(name, command)

                elif "add medication" in command:
                    handle_add_medication_conversation(name)

                elif "remove medication" in command or "cancel medication" in command:
                    handle_remove_medication_conversation(name)

                elif "medication" in command or "my medication" in command:
                    next_med = get_next_medication(name)
                    if next_med:
                        speak(f"Your next medication is {next_med['medication']} at {next_med['time']}.")
                    else:
                        speak("You have no medication scheduled. Would you like me to add a new medication reminder?")
                        start_time = time.time()
                        while time.time() - start_time < 20:
                            response = recognize_speech()
                            if response:
                                response = response.lower()
                                if "yes" in response:
                                    handle_add_medication_conversation(name)
                                    break
                                elif "no" in response:
                                    speak("Okay, how else can I assist you today?")
                                    break
                                else:
                                    speak("I couldn't understand. Please say yes or no.")
                            else:
                                speak("I couldn't hear you. Please repeat.")
                        else:
                            speak("No response received. Let me know if you need anything else.")

                elif "emergency" in command:
                    speak("Calling for help now.")
                    # Integrate your emergency module here

                elif "close" in command or "exit" in command:
                    speak("Goodbye!")
                    exit(0)

                else:
                    speak(f"You said: {command}")
        else:
            speak("I couldn't recognize you. Please try again.")

    print("[INFO] Elder Care Rover is shutting down.")

if __name__ == "__main__":
    main()
