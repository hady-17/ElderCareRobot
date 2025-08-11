import time
import random
import pandas as pd

import common.yaml_handle as yaml_handle
from common.ros_robot_controller_sdk import Board
from face_Recoginition.recognize import recognize_face

# Initialize MasterPi board
board = Board()
sonar_data = yaml_handle.get_yaml_data(yaml_handle.Deviation_file_path)

# === PARAMETERS ===
Threshold = 30.0  # cm
distance_data = []

# === MOTOR CONTROL ===

def set_all_motors(duty1, duty2, duty3, duty4):
    board.set_motor_duty([
        [1, duty1],
        [2, duty2],
        [3, duty3],
        [4, duty4]
    ])

def stop_movement():
    print("[MOVE] Stopping all motors")
    set_all_motors(0, 0, 0, 0)

# === MOVEMENT FUNCTIONS ===

def move_forward(duration=2, speed=45):
    print("[MOVE] Moving forward")
    set_all_motors(speed, speed, speed, speed)
    time.sleep(duration)
    stop_movement()

def rotate_left_90():
    print("[MOVE] Rotating left 90°")
    set_all_motors(-45, 45, -45, 45)
    time.sleep(1.2)
    stop_movement()

def rotate_right_90():
    print("[MOVE] Rotating right 90°")
    set_all_motors(45, -45, 45, -45)
    time.sleep(1.2)
    stop_movement()

def strafe_left(duration=2):
    print("[MOVE] Strafing left")
    set_all_motors(-45, 45, 45, -45)
    time.sleep(duration)
    stop_movement()

def strafe_right(duration=2):
    print("[MOVE] Strafing right")
    set_all_motors(45, -45, -45, 45)
    time.sleep(duration)
    stop_movement()

# === OBSTACLE AVOIDANCE ===

def get_filtered_distance():
    from common import sonar
    sensor = sonar.Sonar()
    global distance_data
    raw_distance = sensor.getDistance() / 10.0
    distance_data.append(raw_distance)

    if len(distance_data) > 5:
        distance_data.pop(0)

    df = pd.DataFrame(distance_data)
    mean = df.mean()
    std = df.std()
    filtered = df[abs(df - mean) <= std]
    return filtered.mean()[0]

def avoid_obstacles():
    distance = get_filtered_distance()
    print(f"[OBSTACLE] Distance: {distance:.1f} cm")

    if distance <= Threshold:
        print("[OBSTACLE] Obstacle detected! Avoiding...")
        stop_movement()
        rotate_left_90()
       # move_forward(duration=0.3)
        print("[OBSTACLE] Avoided.")

# === SEARCH LOGIC ===

def random_search():
    directions = [move_forward, rotate_left_90, rotate_right_90, strafe_left, strafe_right]
    random.choice(directions)()
    print("[SEARCH] Random exploration step.")

def random_search_pattern():
    for _ in range(3):
        random_search()
        move_forward(2)
        rotate_left_90()

def search_for_elder():
    print("[SEARCH] Searching for elder...")
    move_forward(3)

    name = recognize_face()
    if name != "Unknown":
        print(f"[FOUND] Elder found: {name}")
        stop_movement()
        return name
    else:
        print("[INFO] Face not recognized.")
        avoid_obstacles()
        random_search_pattern()
        return "Unknown"
