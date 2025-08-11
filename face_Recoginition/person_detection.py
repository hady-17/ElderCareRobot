# person_detection.py using YOLOv4-Tiny + OpenCV DNN (Optimized for Raspberry Pi 5)
import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE_DIR, "models/yolov4_tiny/yolov4-tiny.cfg")
WEIGHTS = os.path.join(BASE_DIR, "models/yolov4_tiny/yolov4-tiny.weights")
NAMES = os.path.join(BASE_DIR, "models/yolov4_tiny/coco.names")

# Load class labels
with open(NAMES, "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Load YOLOv4-Tiny model using OpenCV DNN
net = cv2.dnn.readNetFromDarknet(CFG, WEIGHTS)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)  # CPU backend
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def detect_person(frame, conf_threshold=0.5, input_size=(256, 256)):
    """
    Detect a person in the frame using YOLOv4-Tiny.
    Optimized for Raspberry Pi 5 performance.
    """
    height, width = frame.shape[:2]

    # Create input blob
    blob = cv2.dnn.blobFromImage(frame, scalefactor=1/255.0, size=input_size, swapRB=True, crop=False)
    net.setInput(blob)

    # Get output layer names and run inference
    output_layers = net.getUnconnectedOutLayersNames()
    outputs = net.forward(output_layers)

    # Loop through detections
    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = int(scores.argmax())
            confidence = scores[class_id]

            if confidence > conf_threshold and classes[class_id] == "person":
                # Scale bounding box to image size
                center_x, center_y, w, h = (detection[0:4] * [width, height, width, height]).astype("int")
                x1 = max(0, int(center_x - w / 2))
                y1 = max(0, int(center_y - h / 2))
                x2 = min(x1 + int(w), width - 1)
                y2 = min(y1 + int(h), height - 1)

                # Check for valid crop size
                if x2 <= x1 or y2 <= y1:
                    print("[WARN] Invalid bounding box size.")
                    return None, None

                print(f"[DETECTED] Person with confidence: {confidence:.2f}")
                person_crop = frame[y1:y2, x1:x2]
                if person_crop.size == 0:
                    print("[WARN] Cropped image is empty.")
                    return None, None

                return person_crop, (x1, y1, x2, y2)

    return None, None
