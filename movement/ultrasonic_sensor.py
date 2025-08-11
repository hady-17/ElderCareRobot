import sys

if sys.platform == "win32":
    import movement.mock_gpio as GPIO  # Use the mock GPIO on Windows
else:
    import RPi.GPIO as GPIO  # Use the real GPIO on Raspberry Pi

import time

# Set up GPIO
TRIG = 23  # GPIO pin for Trigger
ECHO = 24  # GPIO pin for Echo

GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.setup(TRIG, GPIO.OUT)  # Set Trigger pin as output
GPIO.setup(ECHO, GPIO.IN)   # Set Echo pin as input

def distance():
    """
    Measure the distance using the ultrasonic sensor and return the distance in cm.
    """
    # Ensure the Trigger is low
    GPIO.output(TRIG, GPIO.LOW)
    time.sleep(0.5)

    # Send a pulse to the Trigger pin to start the measurement
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)  # Send a 10us pulse
    GPIO.output(TRIG, GPIO.LOW)

    # Wait for the Echo pin to return the pulse and calculate the time it took
    while GPIO.input(ECHO) == GPIO.LOW:
        pulse_start = time.time()

    while GPIO.input(ECHO) == GPIO.HIGH:
        pulse_end = time.time()

    # Calculate pulse duration and convert it to distance in cm
    pulse_duration = pulse_end - pulse_start
    distance_cm = pulse_duration * 17150  # Speed of sound is 343m/s (34300cm/s), divide by 2 for round-trip
    return distance_cm

# Cleanup GPIO on exit
def cleanup():
    GPIO.cleanup()
