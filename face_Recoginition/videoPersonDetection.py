

ip_camera_url = "http://127.0.0.1:8080?action=stream"   # Replace with your actual IP
import cv2
import time
import os
import numpy as np

from face_Recoginition.person_detection import detect_person
from face_Recoginition.recognize import recognize_face,recognize_face_from_frame
from movement.move import move_forward, stop_movement, avoid_obstacles
from notifications import send_telegram_notification
from kinematics.arm_move_ik import ArmIK
from common.ros_robot_controller_sdk import Board
from voice_assistant.tts import speak

# Setup
arm = ArmIK()
arm.board = Board()
SEARCH_TIMEOUT = 180  # seconds
SHOW_CAMERA_VIEW = True  # Set to False if no GUI

scan_positions = [
    {"coord": (5, 6, 18), "pitch": 0},     # Right
    {"coord": (0, 6, 18), "pitch": 0},     # Center
    {"coord": (-5, 6, 18), "pitch": 0},    # Left
]

cap = None

def init_ip_camera_stream():
    global cap
    cap = cv2.VideoCapture(ip_camera_url)
    if not cap.isOpened():
        print("[ERROR] Could not open IP camera stream.")
        return False
    return True

def get_ip_camera_frame():
    global cap
    if cap is None or not cap.isOpened():
        if not init_ip_camera_stream():
            return None
    ret, frame = cap.read()
    if SHOW_CAMERA_VIEW and ret:
        cv2.imshow("IP Camera", frame)
        cv2.waitKey(1)
    return frame if ret else None

def record_video_from_ipcam(filename, duration_sec=3, fps=10, resolution=(480, 360)):
    global cap
    if cap is None or not cap.isOpened():
        if not init_ip_camera_stream():
            return

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(filename, fourcc, fps, resolution)
    start_time = time.time()

    while time.time() - start_time < duration_sec:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Frame not received.")
            continue
        frame = cv2.resize(frame, resolution)
        out.write(frame)

        if SHOW_CAMERA_VIEW:
            cv2.imshow("Recording", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    out.release()
    if SHOW_CAMERA_VIEW:
        cv2.destroyWindow("Recording")

def analyze_video_for_person(video_path):
    cap_vid = cv2.VideoCapture(video_path)
    person_crop = None
    while True:
        ret, frame = cap_vid.read()
        if not ret:
            break
        person_crop, _ = detect_person(frame)
        if person_crop is not None:
            break
    cap_vid.release()
    return person_crop

def analyze_video_for_face(video_path):
    cap_vid = cv2.VideoCapture(video_path)
    while True:
        ret, frame = cap_vid.read()
        if not ret:
            break
        cropped_retry, _ = detect_person(frame)
        if cropped_retry is not None:
	
            name = recognize_face_from_frame(cropped_retry)#recognize_face()

            if name != "Unknown":
                cap_vid.release()
                return name
    cap_vid.release()
    return "Unknown"

def search_for_elder_with_rover():
    print("[INFO] Starting search...")
    speak("Starting search for the elder.")
    name_found = "Unknown"
    start_time = time.time()

    try:
        while time.time() - start_time < SEARCH_TIMEOUT:
            person_detected = False

            for idx, pose in enumerate(scan_positions):
                message = f"Moving to scan position {idx + 1}."
                print(f"[ARM] {message}")
                speak(message)

                result = arm.setPitchRangeMoving(
                    coordinate_data=pose["coord"],
                    alpha=pose["pitch"],
                    alpha1=-90,
                    alpha2=90,
                    movetime=1800
                )
                if not result:
                    print(f"[WARN] Arm could not reach position {pose['coord']}")
                    speak("Arm movement failed. Trying next position.")
                    continue

                time.sleep(1.5)

                video_path = "/tmp/buffer.avi"
                speak("Recording short video for detection.")
                print("[INFO] Recording video...")
                record_video_from_ipcam(video_path, duration_sec=3)

                person_crop = analyze_video_for_person(video_path)
                if os.path.exists(video_path):
                    os.remove(video_path)

                if person_crop is not None:
                    person_detected = True
                    stop_movement()
                    print("[DETECTED] Person found.")
                    speak("Person detected. Raising arm to see face better.")

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
                    time.sleep(2)

                    speak("Recording short video for face recognition.")
                    face_video_path = "/tmp/face_buffer.avi"
                    record_video_from_ipcam(face_video_path, duration_sec=3)

                    name_found = analyze_video_for_face(face_video_path)
                    if os.path.exists(face_video_path):
                        os.remove(face_video_path)

                    if name_found != "Unknown":
                        print(f"[FOUND] Elder recognized: {name_found}")
                        speak(f"Elder recognized. Hello, {name_found}")
                        if SHOW_CAMERA_VIEW:
                            cv2.destroyAllWindows()
                        return name_found
                    else:
                        speak("Face not recognized. Continuing search.")
                        print("[FAIL] Face not recognized.")
                    break

            if not person_detected:
                speak("No person detected. Moving forward and scanning again.")
                print("[MOVE] No person detected.")
            #move_forward(duration=1)
            #avoid_obstacles()
            time.sleep(2)

        print("[TIMEOUT] Elder not found within time limit.")
        speak("Elder not found within time. Please check manually.")
        send_telegram_notification("\u26a0\ufe0f The elder was not found or recognized.")
        if SHOW_CAMERA_VIEW:
            cv2.destroyAllWindows()
        return "Unknown"

    except KeyboardInterrupt:
        stop_movement()
        speak("Search stopped manually.")
        if SHOW_CAMERA_VIEW:
            cv2.destroyAllWindows()
        print("[INTERRUPTED] Search manually stopped.")
        return "Unknown"
# --- videoPersonDetection.py ---

def search_for_person_only(timeout_sec=60):
    """
    Scan positions and record short clips looking ONLY for a person.
    Returns True if a person is detected during the scan window.
    """
    start = time.time()
    try:
        while time.time() - start < timeout_sec:
            for idx, pose in enumerate(scan_positions):
                msg = f"Scanning position {idx + 1}."
                print(f"[ARM] {msg}")
                speak(msg)

                ok = arm.setPitchRangeMoving(
                    coordinate_data=pose["coord"],
                    alpha=pose["pitch"],
                    alpha1=-90, alpha2=90,
                    movetime=1800
                )
                if not ok:
                    print(f"[WARN] Arm could not reach {pose['coord']}")
                    continue

                time.sleep(1.5)

                video_path = "/tmp/person_probe.avi"
                record_video_from_ipcam(video_path, duration_sec=3)

                person_crop = analyze_video_for_person(video_path)  # uses detect_person under the hood
                if os.path.exists(video_path):
                    os.remove(video_path)

                if person_crop is not None:
                    stop_movement()
                    print("[DETECTED] Person present.")
                    if SHOW_CAMERA_VIEW:
                        cv2.destroyAllWindows()
                    return True

            time.sleep(2)  # brief pause before another scan cycle

        if SHOW_CAMERA_VIEW:
            cv2.destroyAllWindows()
        return False
    except KeyboardInterrupt:
        stop_movement()
        if SHOW_CAMERA_VIEW:
            cv2.destroyAllWindows()
        return False
