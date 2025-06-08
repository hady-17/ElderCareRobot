# main.py

from face_Recoginition.recognize import recognize_face
from voice_assistant.speech_recoginition import recognize_speech
from voice_assistant.tts import speak
from voice_assistant.wake_word import listen_for_wake_word

def main():
    print("[INFO] Elder Care Rover is starting up...")

    while True:
        # 1️⃣ Listen for wake word
        listen_for_wake_word()  # Blocks until wake word detected
        speak("Hello! I'm listening.")

        # 2️⃣ Perform face recognition
        name = recognize_face()
        if name != "Unknown":
            speak(f"Hello, {name}! How can I assist you today?")
        else:
            speak("I couldn't recognize you. Please try again.")

        # 3️⃣ Listen for command
        command = recognize_speech()

        # 4️⃣ Process the command
        if "medication" in command:
            speak("It’s time for your medication. Please take it now.")
        elif "emergency" in command:
            speak("Calling for help now.")
            # Here you can integrate your emergency module
        elif "goodbye" in command or "exit" in command:
            speak("Goodbye!")
            break
        else:
            speak(f"You said: {command}")

    print("[INFO] Elder Care Rover is shutting down.")

if __name__ == "__main__":
    main()
