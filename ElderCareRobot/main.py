from face_Recoginition.recognize import recognize_face
from voice_assistant.speech_recoginition import recognize_speech
from voice_assistant.tts import speak

def main():
    print("[INFO] Elder Care Rover is starting up...")

    while True:
        # 1️⃣ Face Recognition
        name = recognize_face()
        if name != "Unknown":
            speak(f"Hello, {name}! How can I assist you today?")
        else:
            speak("I couldn't recognize you. Please try again.")

        # 2️⃣ Listen for command
        command = recognize_speech()

        # 3️⃣ Process the command
        if "medication" in command:
            speak("It’s time for your medication. Please take it now.")
        elif "emergency" in command:
            speak("Calling for help now.")
            # Integrate your emergency module here
        elif "close" in command or "exit" in command:
            speak("Goodbye!")
            break
        else:
            speak(f"You said: {command}")

    print("[INFO] Elder Care Rover is shutting down.")

if __name__ == "__main__":
    main()
