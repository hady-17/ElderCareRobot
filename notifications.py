# notification.py

import requests
from threading import Timer
from dotenv import load_dotenv
import os

load_dotenv()
# Telegram Bot Token and Chat ID
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Function to send message via Telegram
def send_telegram_notification(message):
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(TELEGRAM_API_URL, data=payload)
    if response.status_code == 200:
        print(f"Notification sent: {message}")
    else:
        print("Failed to send notification.")

# Function to notify when medication is taken or missed
def notify_medication_taken(is_taken, medication_name):
    if is_taken:
        send_telegram_notification(f"The elder has taken their medication: {medication_name}.")
    else:
        send_telegram_notification(f"Reminder: The elder has not responded to the medication reminder for: {medication_name}.")

# Function to notify when sleep alarm is triggered or if there's no response
def notify_sleep_alarm(is_responded):
    if is_responded:
        send_telegram_notification("The elder has responded to the sleep alarm.")
    else:
        send_telegram_notification("The elder did not respond to the sleep alarm within 5 minutes.")

# Function to notify if elder doesn't respond to reminders
def notify_reminder_not_responded(reminder_name):
    send_telegram_notification(f"The elder has not responded to the reminder: {reminder_name} within 5 minutes.")

# Monitor function for reminders (e.g., medication, sleep alarm, etc.)
def monitor_response(reminder_name, response_received_callback, timeout=180):
    """Monitor for 5 minutes for the elder's response, if no response, notify the family."""
    def on_timeout():
        # This function sends a notification after the timeout is reached
        notify_reminder_not_responded(reminder_name)

    # Start a timer for 5 minutes (300 seconds)
    timer = Timer(timeout, on_timeout)
    timer.start()

    # Simulate the case where the elder does not respond within the timeout period.
    response = False  # Change this to True if elder responds before timeout.
    if response:
        response_received_callback()
        timer.cancel()  # Stop the timeout timer if response is received.
    else:
        # If no response within timeout, the timer will send a notification.
        pass

# Function to simulate elder response (can be triggered from other parts of the system)
def elder_response_received():
    send_telegram_notification("The elder has responded to the reminder!")
