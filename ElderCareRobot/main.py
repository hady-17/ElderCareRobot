from voice_assistant.wake_word import detect_wake_word
from face_Recoginition.recognize import recognize_face
from voice_assistant.speech_recoginition import recognize_speech
from voice_assistant.tts import speak
from reminders.custom_reminder import (
    handle_interactive_reminder,
    check_due_reminders
)
from reminders.medication_reminder import (
    check_medication_schedule,
    handle_add_medication_conversation,
    handle_remove_medication_conversation,
    get_next_medication,
    load_medication_schedules
)
from reminders.sleep_alarm import handle_sleep_alarm, check_due_sleep_alarm
import time

def main():
    print("[INFO] Elder Care Rover is starting up...")

    while True:
        # 💤 Standby loop with background checks
        while True:
            check_due_reminders("all")
            check_medication_schedule("all")
            check_due_sleep_alarm("all")
            time.sleep(30)

            # Listen for wake word
            detect_wake_word()
            speak("I'm here. Let me check who's speaking.")
            name = recognize_face()

            if name != "Unknown":
                break
            else:
                speak("I couldn't recognize you. Please try again.")

        # 🧠 Active session after recognition
        speak(f"Hello {name}! How can I help you today?")
        session_active = True

        while session_active:
            check_due_reminders(name)
            check_medication_schedule(name)
            check_due_sleep_alarm(name)

            command = recognize_speech()
            if not command:
                continue
            command = command.lower()

            if "end" in command or "exit" in command:
                speak("Ending conversation. Awaiting next elder.")
                session_active = False
                break

            elif "close" in command:
                speak("Going into standby mode. Say 'Jarvis' or 'Rover' when you need me.")
                session_active = False
                break

            elif "remind me" in command or "remember me" in command:
                handle_interactive_reminder(name, initial_prompt=command)

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

            elif "emergency" in command:
                speak("Calling for help now.")
                # Emergency handling code goes here

            elif "wake me up" in command or "i want to sleep" in command:
                wake_time_str = handle_sleep_alarm(name, command)
                speak(f"Alarm set for {wake_time_str}.")

            else:
                speak(f"You said: {command}")

if __name__ == "__main__":
    main()
