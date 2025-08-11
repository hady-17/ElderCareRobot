import time
from threading import Thread, Event
from datetime import datetime
#from videoLaptopTest import search_for_elder_with_rover,search_for_person_only

from LapTestCode import search_for_elder_with_rover
from face_Recoginition.recognize import recognize_face
from voice_assistant.wake_word import detect_wake_word
from voice_assistant.speech_recoginition import recognize_speech,listen_for_confirmation
from voice_assistant.tts import speak
from emergency_call.emergency_call import make_emergency_call
from reminders.custom_reminder import (
    handle_interactive_reminder,
    check_due_reminders,
    load_reminders,
    remove_old_done_reminders
)
from reminders.medication_reminder import (
    check_medication_schedule,
    get_next_medication,
    load_medication_schedules
)
from reminders.sleep_alarm import (
    handle_add_sleep_alarm_conversation,
    handle_remove_sleep_alarm_conversation,
    check_due_sleep_alarm,
    load_sleep_alarms
)
from notifications import (
    send_telegram_notification,
    notify_medication_taken,
    notify_sleep_alarm,
    monitor_response,
    notify_reminder_not_responded
)
from speaker_reco.voice_recognition import record_temp_voice, identify_speaker
from voice_assistant.verify_user import verify_user_by_voice
interrupt_flag = Event()

def elder_response_received():
    print("Elder has responded to the reminder!")
    send_telegram_notification("The elder has responded to the reminder!")  # :contentReference[oaicite:3]{index=3}

def repeat_reminder_until_acknowledged(name, task, reminder_type, timeout=5):
    """
    Verifies the elder by voice before delivering the reminder.
    If voice match fails, sends Telegram notification and retries later.
    """

    # Step 1: Voice verification loop
    while True:
        speak("Please say something so I can verify you before the reminder.")
        voice_file = record_temp_voice()
        detected_name = identify_speaker(voice_file)

        if detected_name != name:
            speak(f"I could not verify that you are {name}.")
            send_telegram_notification(
                f"⚠ Reminder '{task}' was triggered for {name}, "
                f"but voice match failed (detected: {detected_name})."
            )
            time.sleep(3)  # retry delay
            speak("I will try again later.")
            continue  # Retry the voice verification
        else:
            break  # Verification passed

    # Step 2: Deliver reminder until acknowledged
    acknowledged = False
    while not acknowledged:
        speak(f"Sorry for interrupting you. It's time to {task}. "
              "Please say 'done', 'got it', or 'stop'.")
        
        if listen_for_confirmation(timeout=timeout):
            speak(f"Reminder for {task} acknowledged.")
            acknowledged = True
            send_telegram_notification(
                f"The elder has acknowledged the reminder: {task}."
            )
        else:
            speak(f"Still waiting for acknowledgment. Repeating reminder for {task}.")
            send_telegram_notification(
                f"Still waiting for acknowledgment. Repeating reminder for {task}."
            )
            time.sleep(1)

        # If you need to monitor responses over time, define elder_response_received before this
        # monitor_response(task, elder_response_received)

def background_check_loop(name):
    while True:
        print(f"[DEBUG] Background thread active for {name}")
        time.sleep(30)
        now = datetime.now().strftime("%I:%M %p")
        print(f"[BG] Checking reminders for {name} at {now}")

        reminders = load_reminders()
        for r in reminders:
            if r["name"].lower() == name.lower() and r["time"] == now and not r["done"]:
                repeat_reminder_until_acknowledged(name, r["task"], r["type"])

        next_med = get_next_medication(name)
        if next_med and next_med['time'] == now and not next_med['done']:
            repeat_reminder_until_acknowledged(name, f"take your medication: {next_med['medication']}", "once")

        check_due_sleep_alarm(name)

def main():
    print("[INFO] Elder Care Rover is starting up...")

    while True:
        check_due_reminders("all")
        check_medication_schedule("all")
        check_due_sleep_alarm("all")
        remove_old_done_reminders()
        time.sleep(5)

        detect_wake_word()
        speak("I'm here. Let me identify you.")
        time.sleep(0.5)
        speak("recording your voice for identification.")
        name = "Unknown"
        voice_file = record_temp_voice()
        name = identify_speaker(voice_file)
        speak("finished recording your voice.")
        time.sleep(0.5)
          # Placeholder for voice recognition
        if name == "Unknown":
            speak("I couldn't recognize you by voice. Let me try using the camera.")
            #name = recognize_face()
            name= search_for_elder_with_rover()
            if name == "Unknown":
                speak("I still couldn't recognize you. I will notify your family to check on you.")
                timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
                alert_message = f"\u26a0\ufe0f The elder could not be recognized by voice or face at {timestamp}. Please check on them."
                send_telegram_notification(alert_message)
                continue

        if name != "Unknown":
            Thread(target=background_check_loop, args=(name,), daemon=True).start()
            speak(f"Hello {name}! How can I help you today?")
            session_active = True

            while session_active:
                if interrupt_flag.is_set():
                    interrupt_flag.clear()
                    continue

                command = recognize_speech(
                    timeout=6,
                    choices=["close", "end", "exit",
                             "wake me up", "remind me", "remove sleep alarm", "add sleep alarm",
                             "medication", "emergency", "what are my reminders", "list my reminders",
                             "sleep alarm", "my sleep"]
                )
                if not command:
                    continue
                command = command.lower()

                if "end" in command or "exit" in command:
                    speak("Ending conversation. Awaiting next elder.")
                    session_active = False

                elif "close" in command:
                    speak("Going into standby mode. Say 'Jarvis' or 'Rover' when you need me.")
                    session_active = False

                elif "remind me" in command or "remember me" in command:
                    handle_interactive_reminder(name, initial_prompt=command)

                elif "medication" in command:
                    next_med = get_next_medication(name)
                    if next_med:
                        speak(f"Your next medication is {next_med['medication']} at {next_med['time']}.")
                    else:
                        speak("You have no upcoming medications scheduled.")

                    speak("Would you like to hear your full medication schedule?")
                    response = recognize_speech()
                    if response and "yes" in response.lower():
                        schedules = load_medication_schedules()
                        elder_meds = [s for s in schedules if s["name"].lower() == name.lower()]
                        for med in elder_meds:
                            speak(f"{med['medication']} {med['dose']} at {med['time']}.")
                    else:
                        speak("Okay, let me know if you need anything else.")

                elif "add sleep alarm" in command:
                    handle_add_sleep_alarm_conversation(name)

                elif "remove sleep alarm" in command:
                    handle_remove_sleep_alarm_conversation(name)

                elif "sleep alarm" in command or "my sleep " in command:
                    speak("Would you like to hear your upcoming sleep alarms?")
                    response = recognize_speech()
                    if response and "yes" in response.lower():
                        alarms = load_sleep_alarms()
                        elder_alarms = [a for a in alarms if a["name"].lower() == name.lower()]
                        for alarm in elder_alarms:
                            speak(f"{alarm['task']} at {alarm['time']} ({alarm['type']}).")
                    else:
                        speak("Okay, let me know if you need anything else.")

                elif "what are my reminders" in command or "list my reminders" in command:
                    from reminders.custom_reminder import list_reminders_for
                    list_reminders_for(name)

                elif "emergency" in command:
                    speak("Calling for help now.")
                    make_emergency_call()

                elif "wake me up" in command or "i want to sleep" in command:
                    handle_add_sleep_alarm_conversation(name)

                else:
                    speak(f"You said: {command}")

if __name__ == "__main__":
    main()
