# recognize.py

import cv2
import dlib
import numpy as np
import pickle

# Paths to models and encodings
ENCODINGS_PATH = "encodings.pickle"
PREDICTOR_PATH = "face_Recoginition/shape_predictor_68_face_landmarks.dat"
MODEL_PATH = "face_Recoginition/dlib_face_recognition_resnet_model_v1.dat"

# Load models once
shape_predictor = dlib.shape_predictor(PREDICTOR_PATH)
face_rec_model = dlib.face_recognition_model_v1(MODEL_PATH)
detector = dlib.get_frontal_face_detector()

# Load known encodings
with open(ENCODINGS_PATH, "rb") as f:
    data = pickle.load(f)
    known_encodings = data["encodings"]
    known_names = data["names"]

def recognize_face_from_frame(cropped_frame):
    """
    Identify a face from a cropped frame.
    """
    rgb_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
    faces = detector(rgb_frame, 1)

    if not faces:
        print("[INFO] No face detected.")
        return "Unknown"

    for rect in faces:
        shape = shape_predictor(rgb_frame, rect)
        face_descriptor = face_rec_model.compute_face_descriptor(rgb_frame, shape)
        face_encoding = np.array(face_descriptor)

        distances = [np.linalg.norm(known - face_encoding) for known in known_encodings]
        if distances:
            min_dist = min(distances)
            index = distances.index(min_dist)
            if min_dist < 0.6:
                name = known_names[index]
                print(f"[INFO] Recognized: {name}")
                return name

    return "Unknown"

def recognize_face():
    """
    Capture a single frame from the IP camera and recognize the face in it.
    """
    # Replace with your actual phone IP address
    ip_camera_url = "http://127.0.0.1:8080?=action=stream"  # Update this line!

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print(f"[ERROR] Could not open IP camera at {ip_camera_url}")
        return "Unknown"

    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("[ERROR] Failed to capture frame from IP camera.")
        return "Unknown"

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector(rgb_frame, 1)

    if not faces:
        print("[INFO] No face detected.")
        return "Unknown"

    for rect in faces:
        shape = shape_predictor(rgb_frame, rect)
        face_descriptor = face_rec_model.compute_face_descriptor(rgb_frame, shape)
        face_encoding = np.array(face_descriptor)

        distances = [np.linalg.norm(known - face_encoding) for known in known_encodings]
        if distances:
            min_dist = min(distances)
            index = distances.index(min_dist)
            if min_dist < 0.6:
                name = known_names[index]
                print(f"[INFO] Recognized: {name}")
                return name
            else:
                print("[INFO] Face not recognized.")

    return "Unknown"
