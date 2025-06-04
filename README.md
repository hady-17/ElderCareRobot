# ElderCareRobot
senior project for my BS in computer Science
Elder Care Monitoring Rover with Voice Assistant
This project is an AI-powered mobile rover designed to assist elderly individuals in their homes. Built on a Raspberry Pi 4, the rover combines facial recognition, voice interaction, and safety features to enhance independence and well-being.

Key Features:

Facial Recognition: Identifies the user using dlib and OpenCV.

Voice Assistant: Supports offline speech recognition (Vosk) and text-to-speech (eSpeak).

Wake Word Detection: Uses Picovoice Porcupine to activate the system with a specific keyword.

Medication Reminders: Provides timely reminders for medications.

Emergency Alerts: Notifies family members via Discord/SMS if the user is unresponsive.

Urgent Phone Calls: Places direct calls (e.g., to ambulance or firefighters) based on voice commands.

Sleep Alarm: Allows the user to set a sleep duration alarm; notifies family if the user does not respond.

Custom Reminders: Allows users to set reminders with voice commands (e.g., “remind me on [date and time]”).

Tech Stack:

Hardware: Raspberry Pi 4, Pi Camera, microphone module, speaker module, ultrasonic sensors, motor driver, wheels and chassis kit, and battery pack.

Software: Python, dlib, OpenCV, Vosk, Picovoice Porcupine, eSpeak, Discord/SMS integration.

Project Structure:

face_recognition/ — Facial recognition module

voice_assistant/ — Speech recognition, wake word, and TTS modules

reminders/ — Medication, sleep, and custom reminders

emergency_call.py — Emergency call functionality

notifications.py — Discord/SMS notification system

config.py — Project configuration

This project is currently in development and aims to provide a reliable and accessible solution for elderly care at home.
