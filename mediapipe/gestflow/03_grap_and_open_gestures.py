import cv2 as cv
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time

# ==========================================
# STEP 1: INITIALIZATION & CONFIGURATION
# ==========================================
HAND_CONNECTIONS = [
    # Wrist to finger bases
    (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),      # Index Finger
    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle Finger
    (0, 13), (13, 14), (14, 15), (15, 16),# Ring Finger
    (0, 17), (17, 18), (18, 19), (19, 20),# Pinky
    # Knuckle-to-knuckle connections to fill out the palm shape
    (5, 9), (9, 13), (13, 17)
]
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options = base_options,
    running_mode = vision.RunningMode.VIDEO,
    num_hands = 1,
    min_hand_detection_confidence = 0.5,
    min_hand_presence_confidence = 0.5,
    min_tracking_confidence = 0.5,
)

detector = vision.HandLandmarker.create_from_options(options)
current_gesture = ''


# ==========================================
# STEP 2: VIDEO CAPTURE LOOP
# ==========================================
capture = cv.VideoCapture(1)
current_time = time.time()
print("GestFlow Engine Running...")

while True:
    isTrue , frame = capture.read()
    if not isTrue:
        print("Failed to grab frame from camera.")
        break
    frame = cv.flip(frame, 1)
    rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

    timestamp_ms = int((time.time() - current_time) * 1000)

    results = detector.detect_for_video(mp_image, timestamp_ms)
    
    if results.hand_landmarks:
        for hand_landmarks in results.hand_landmarks:
            h, w, c = frame.shape
            # Draw the line segments connecting the landmarks
            for connection in HAND_CONNECTIONS:
                #Every connection pair contains two indices, representing the start and end points of the line segment
                start_idx = connection[0]
                end_idx = connection[1]

                # Normalize the landmark coordinates to pixel values
                start_x = hand_landmarks[start_idx]
                end_x = hand_landmarks[end_idx]

                # Convert both points to pixel coordinates
                x1, y1 = int(start_x.x * w), int(start_x.y * h)
                x2, y2 = int(end_x.x * w), int(end_x.y * h)

                cv.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv.circle(frame, (cx, cy), 6, (0, 255, 0), cv.FILLED)

            # HEURISTIC GESTURE LOGIC
            finger_tips = [8, 12, 16, 20]  # Indices for the tips of the fingers
            finger_knuckles = [6, 10, 14, 18]  # Indices for the knuckles of the fingers

            open_fingers = 0
            for i in range(4):
                tip_y = hand_landmarks[finger_tips[i]].y
                knuckle_y = hand_landmarks[finger_knuckles[i]].y

                if tip_y < knuckle_y:  # If the tip is above the knuckle, the finger is considered open
                    open_fingers += 1
                    
            # Handle thumb using 2D distance heuristic
            thumb_tip = hand_landmarks[4]
            thumb_knuckle = hand_landmarks[3]

            thumb_distance = ((thumb_tip.x - thumb_knuckle.x) ** 2 + (thumb_tip.y - thumb_knuckle.y) ** 2) ** 0.5
            if thumb_distance > 0.12:  # Threshold for thumb being open
                open_fingers += 1
            # Classify gestures based on the number of open fingers
            if open_fingers == 0:
                current_gesture = "✊ GESTFLOW: SELECT / GRAB"
            elif open_fingers >= 4:
                current_gesture = "🖐️ GESTFLOW: PASTE / RELEASE"
            else:
                current_gesture = f"HOLDING ({open_fingers} fingers up)"
        # Render data HUD text
    cv.putText(frame, current_gesture, (30, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv.LINE_AA)
    
    cv.imshow("GestFlow Live Prototype", frame)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break
capture.release()
cv.destroyAllWindows()
