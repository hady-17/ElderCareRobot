# If using a streaming URL, you can use the following line instead:

 # Adjust this URL based on your camera setup
import cv2
import time
import os
import urllib.request
import numpy as np

from face_Recoginition.person_detection import detect_person
from face_Recoginition.recognize import recognize_face_from_frame
from movement.move import move_forward, stop_movement, avoid_obstacles
from notifications import send_telegram_notification
from kinematics.arm_move_ik import ArmIK
from common.ros_robot_controller_sdk import Board
from voice_assistant.tts import speak  # ✅ voice support added

# MasterPi hardware setup
arm = ArmIK()
arm.board = Board()
SEARCH_TIMEOUT = 180  # seconds
VIDEO_PATH = "/tmp/buffer.avi"
RESOLUTION = (320, 240)
FPS = 10

# Arm scanning positions
scan_positions = [
    {"coord": (5, 6, 18), "pitch": 0},     # Right
    {"coord": (0, 6, 18), "pitch": 0},     # Center
    {"coord": (-5, 6, 18), "pitch": 0},    # Left
]

# IP camera snapshot URL
CAMERA_SNAPSHOT_URL = "http://127.0.0.1:8080/shot.jpg"
ip_camera_url = "http://127.0.0.1:8080?action=stream"
def get_ip_camera_frame():
    try:
        resp = urllib.request.urlopen(ip_camera_url, timeout=2)
        img_np = np.array(bytearray(resp.read()), dtype=np.uint8)
        frame = cv2.imdecode(img_np, -1)
        return cv2.resize(frame, RESOLUTION)
    except:
        return None

def record_video_from_ipcam(filename, duration_sec=3, fps=FPS, resolution=RESOLUTION):
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, fps, resolution)
    start = time.time()

    while time.time() - start < duration_sec:
        frame = get_ip_camera_frame()
        if frame is not None:
            out.write(frame)
            cv2.imshow("Recording", frame)
            cv2.waitKey(1)
    out.release()
    cv2.destroyWindow("Recording")

def analyze_video_for_person(video_path):
    cap = cv2.VideoCapture(video_path)
    person_crop = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        person_crop, _ = detect_person(frame)
        if person_crop is not None:
            break
    cap.release()
    return person_crop

def search_for_elder_with_rover():
    speak("Starting search for the elder.")
    print("[INFO] Starting search for elder...")
    name_found = "Unknown"
    start_time = time.time()

    try:
        while time.time() - start_time < SEARCH_TIMEOUT:
            person_detected = False

            for idx, pose in enumerate(scan_positions):
                speak(f"Scanning position {idx + 1}")
                print(f"[ARM] Moving to scan position {idx + 1}: {pose['coord']}")
                success = arm.setPitchRangeMoving(
                    coordinate_data=pose["coord"],
                    alpha=pose["pitch"],
                    alpha1=-90,
                    alpha2=90,
                    movetime=2000
                )
                if not success:
                    print(f"[WARN] Failed to move arm to {pose['coord']}")
                    continue

                time.sleep(2.0)
                speak("Recording")
                record_video_from_ipcam(VIDEO_PATH)

                person_crop = analyze_video_for_person(VIDEO_PATH)
                if os.path.exists(VIDEO_PATH):
                    os.remove(VIDEO_PATH)

                if person_crop is not None:
                    person_detected = True
                    stop_movement()
                    print("[DETECTED] Person found.")
                    speak("Person detected. Trying to recognize face.")

                    raise_pose = (
                        pose["coord"][0],
                        pose["coord"][1] + 7,
                        pose["coord"][2] + 5
                    )
                    arm.setPitchRangeMoving(
                        coordinate_data=raise_pose,
                        alpha=pose["pitch"] + 45,
                        alpha1=-90,
                        alpha2=90,
                        movetime=1800
                    )
                    time.sleep(2.0)

                    for attempt in range(3):
                        print(f"[RECOGNITION] Attempt {attempt + 1}")
                        speak(f"Recognition attempt {attempt + 1}")
                        frame = get_ip_camera_frame()
                        if frame is None:
                            continue

                        cropped_retry, _ = detect_person(frame)
                        if cropped_retry is None:
                            continue

                        name_found = recognize_face_from_frame(cropped_retry)
                        if name_found != "Unknown":
                            speak(f"Elder recognized. Hello, {name_found}")
                            print(f"[FOUND] Elder recognized: {name_found}")
                            cv2.destroyAllWindows()
                            return name_found
                        time.sleep(1)

                    speak("Face not recognized. Continuing search.")
                    print("[FAIL] Face not recognized. Continuing search.")
                    break

            if not person_detected:
                speak("No person detected. Moving forward.")
                print("[MOVE] No person detected. Moving robot.")
            move_forward(duration=1)
            avoid_obstacles()
            time.sleep(2.0)

        speak("Elder not found. Please check manually.")
        print("[TIMEOUT] Elder not found.")
        send_telegram_notification("⚠️ Elder was not found or recognized.")
        cv2.destroyAllWindows()
        return "Unknown"

    except KeyboardInterrupt:
        stop_movement()
        speak("Search stopped.")
        cv2.destroyAllWindows()
        print("[INTERRUPTED] Search manually stopped.")

    return name_found
