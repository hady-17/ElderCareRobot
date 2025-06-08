# recognize.py

import cv2
import dlib
import numpy as np
import pickle

# Load encodings and names from file
with open("encodings.pickle", "rb") as f:
    data = pickle.load(f)
    known_encodings = data["encodings"]
    known_names = data["names"]

# Load models
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")
detector = dlib.get_frontal_face_detector()

# Start webcam
cap = cv2.VideoCapture(0)  # 0 = default webcam

print("[INFO] Starting face recognition. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Failed to grab frame.")
        break

    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    faces = detector(rgb_frame, 1)

    # Loop through each face detected
    for rect in faces:
        # Get landmarks
        shape = shape_predictor(rgb_frame, rect)
        # Get face encoding
        face_descriptor = face_rec_model.compute_face_descriptor(rgb_frame, shape)
        face_encoding = np.array(face_descriptor)

        # Compare with known encodings
        matches = []
        for known_encoding in known_encodings:
            dist = np.linalg.norm(known_encoding - face_encoding)
            matches.append(dist)

        # Find best match
        if matches:
            min_dist = min(matches)
            best_match_index = matches.index(min_dist)

            if min_dist < 0.6:  # Lower threshold = stricter match
                name = known_names[best_match_index]
            else:
                name = "Unknown"
        else:
            name = "Unknown"

        # Draw rectangle around face
        x1, y1, x2, y2 = rect.left(), rect.top(), rect.right(), rect.bottom()
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

    # Display the result
    cv2.imshow("Face Recognition", frame)

    # Exit with 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release and cleanup
cap.release()
cv2.destroyAllWindows()
print("[INFO] Face recognition stopped.")
