# train_model.py

import os
import cv2
import dlib
import numpy as np
import pickle

# Initialize face detector and shape predictor from dlib
detector = dlib.get_frontal_face_detector()
shape_predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
face_rec_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")

# Path to dataset directory
dataset_path = r"C:\Users\USER\Desktop\senior\ElderCareRobot\face_Recoginition\dataSet"

# Lists to hold encodings and labels
known_encodings = []
known_names = []

# Loop over each person in the dataset
for person_name in os.listdir(dataset_path):
    person_folder = os.path.join(dataset_path, person_name)
    if not os.path.isdir(person_folder):
        continue

    print(f"[INFO] Processing {person_name}...")

    # Loop over each image of the person
    for image_name in os.listdir(person_folder):
        image_path = os.path.join(person_folder, image_name)
        image = cv2.imread(image_path)

        if image is None:
            print(f"[WARNING] Could not read image {image_path}. Skipping...")
            continue

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces in the image
        faces = detector(rgb_image, 1)

        if len(faces) == 0:
            print(f"[WARNING] No faces found in {image_path}. Skipping...")
            continue

        # For each detected face
        for face_rect in faces:
            # Get landmarks
            shape = shape_predictor(rgb_image, face_rect)
            # Get embedding
            face_descriptor = face_rec_model.compute_face_descriptor(rgb_image, shape)
            # Convert to numpy array
            face_encoding = np.array(face_descriptor)
            # Append encoding and label
            known_encodings.append(face_encoding)
            known_names.append(person_name)

print("[INFO] Saving encodings to file...")

# Save encodings and labels to file
data = {"encodings": known_encodings, "names": known_names}
with open("encodings.pickle", "wb") as f:
    pickle.dump(data, f)

print("[INFO] Training completed and encodings saved to encodings.pickle.")
