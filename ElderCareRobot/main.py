# main.py

from face_Recoginition.recognize import recognize_face
from voice_assistant.speech_recoginition import recognize_speech
from voice_assistant.tts import speak
from reminders.custom_reminder import (
    handle_new_reminder,
    load_reminders,
    handle_remove_reminder,
    handle_modify_reminder,
    check_due_reminders
)
from reminders.medication_reminder import (
    check_medication_schedule,
    handle_add_medication_conversation,
    handle_remove_medication_conversation,
    get_next_medication,
    load_medication_schedules
)
from datetime import datetime
import time

def main():
    print("[INFO] Elder Care Rover is starting up...")

    while True:
        # Recognize elder's face
        name = recognize_face()
        if name != "Unknown":
            speak(f"Hello, {name}! How can I assist you today?")
            check_due_reminders(name)  # Check if there are due reminders
            check_medication_schedule(name)  # Check if there are any medication reminders

            while True:
                command = recognize_speech()  # Capture the command from speech
                if not command:
                    continue
                command = command.lower()

                # Command to end the conversation
                if "end" in command or "end it" in command:
                    speak("Ending conversation. Awaiting next elder.")
                    break

                # Command to set a new reminder
                elif "remind me" in command or "remember me" in command:
                    speak("What would you like me to remind you of?")
                    task = recognize_speech()  # Capture task (e.g., "To walk")
                    if task:
                        speak(f"Got it. You want to be reminded to {task}. At what time?")
                        time_str = recognize_speech()  # Capture time (e.g., "at 3:30 PM")
                        if time_str:
                            handle_new_reminder(name, task, time_str)

                # Command to remove a reminder
                elif "remove reminder" in command:
                    speak("Which reminder would you like to remove?")
                    task_command = recognize_speech()  # Capture task to be removed
                    handle_remove_reminder(name, task_command)

                # Command to modify a reminder
                elif "modify reminder" in command:
                    speak("Which reminder would you like to modify?")
                    old_task = recognize_speech()  # Capture the old task name
                    speak("What should be the new task?")
                    new_task = recognize_speech()  # Capture the new task
                    speak("What time should I remind you?")
                    new_time = recognize_speech()  # Capture the new time
                    speak("Should I remind you daily or once?")
                    new_type = recognize_speech()  # Capture the new type
                    handle_modify_reminder(name, old_task, new_task, new_time, new_type)

                # Command to manage medications
                elif "add medication" in command:
                    handle_add_medication_conversation(name)

                elif "remove medication" in command or "cancel medication" in command:
                    handle_remove_medication_conversation(name)

                elif "medication" in command or "my medication" in command:
                    next_med = get_next_medication(name)
                    if next_med:
                        speak(f"Your next medication is {next_med['medication']} at {next_med['time']}.")
                    else:
                        speak("You have no upcoming medications scheduled.")

                    speak("Would you like to know your medication schedule, add a new medication, or modify or remove an existing one?")
                    start_time = time.time()
                    while time.time() - start_time < 20:
                        response = recognize_speech()
                        if response:
                            response = response.lower()
                            if "schedule" in response:
                                schedules = load_medication_schedules()
                                elder_meds = [s for s in schedules if s["name"].lower() == name.lower()]
                                if elder_meds:
                                    speak("Here is your medication schedule:")
                                    for med in elder_meds:
                                        speak(f"{med['medication']} at {med['time']}.")
                                else:
                                    speak("You have no medications scheduled.")
                                break
                            elif "add" in response:
                                handle_add_medication_conversation(name)
                                break
                            elif "remove" in response or "modify" in response:
                                handle_remove_medication_conversation(name)
                                break
                            elif "no" in response:
                                speak("Okay, let me know if you need anything else.")
                                break
                            else:
                                speak("I couldn't understand. Please say schedule, add, remove, or no.")
                        else:
                            speak("I couldn't hear you. Please repeat.")
                    else:
                        speak("No response received. Let me know if you need anything else.")

                # Emergency situation
                elif "emergency" in command:
                    speak("Calling for help now.")
                    # Integrate your emergency module here

                # Command to exit
                elif "close" in command or "exit" in command:
                    speak("Goodbye!")
                    exit(0)

                # Unknown command
                else:
                    speak(f"You said: {command}")
        else:
            speak("I couldn't recognize you. Please try again.")

    print("[INFO] Elder Care Rover is shutting down.")

if __name__ == "__main__":
    main()
