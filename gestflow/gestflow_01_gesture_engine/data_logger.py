import os
import csv
import cv2 as cv
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

CSV_FILE = 'gesture_data.csv'

# ==========================================
# STEP 1: INITIALIZE CSV HEADERS ONLY ONCE
# ==========================================
file_exists = os.path.exists(CSV_FILE)
if not file_exists:
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        headers = ['label']
        for i in range(21):
            # Fixed: Extend as distinct elements for correct table generation
            headers.extend([f'x{i}', f'y{i}', f'z{i}'])
        writer.writerow(headers)
    print(f"📝 Created new clean file: {CSV_FILE}")
else:
    print(f"📚 Appending to existing dataset: {CSV_FILE}")

# ==========================================
# STEP 2: MEDIAPAPE V2 INITIALIZATION
# ==========================================
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.5,       
    min_tracking_confidence=0.5  
)
detector = vision.HandLandmarker.create_from_options(options)

# Open the webcam 
capture = cv.VideoCapture(1)

print("\n📊 DATA LOGGER ACTIVE")
print("Instructions:")
print("  - Hold down '0' for GRAB ✊")
print("  - Hold down '1' for OPEN PALM 🖐️")
print("  - Hold down '2' for PINCH 🤏")
print("  - Hold down '3' for THROW RIGHT 👉")
print("  - Hold down '4' for THROW lEFT 👈")
print("  - Hold down '5' for EXPAND (spread fingers) 🖖")
print("  - Hold down '6' for  SELECT MULTIPLE (two fingers up) ✌️")
print("  - Hold down '7' for CANCEL/UNDO (shake fingers) 🤙")


print("  - Press 'q' to stop logging data safely.\n")

while capture.isOpened():
    isTrue, frame = capture.read()
    if not isTrue:
        print('frame is not detected properly')
        continue
        
    frame = cv.flip(frame, 1)
    h, w, c = frame.shape
    rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    # Fixed: Use explicit .detect method
    results = detector.detect(mp_image)
    status_text = "Waiting for key press..."

    # Detect key press
    key = cv.waitKey(1) & 0xFF
    if key == ord('q'):
        break

    # Check if a numeric logging key was pressed
    is_numeric_key = chr(key) in '0123456789' if key != 255 else False

    if results.hand_landmarks:
        # Fixed: Safely extract the first hand landmark list layer
        hand_landmarks = results.hand_landmarks[0]
        
        # Draw the tracking landmarks
        for lm in hand_landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv.circle(frame, (cx, cy), 4, (0, 165, 255), -1)
            
        # Fixed: Encapsulated coordinate compilation inside the key condition check
        if is_numeric_key:
            label = int(chr(key))
            landmarks_list = [label]
            
            for lm in hand_landmarks:
                landmarks_list.extend([float(lm.x), float(lm.y), float(lm.z)])
                
            # Append pristine numerical data to the file
            with open(CSV_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(landmarks_list)
                
            status_text = f"🔴 SAVING CLASS [{label}]"

    # Display HUD
    cv.rectangle(frame, (0, 0), (w, 50), (20, 20, 20), -1)
    cv.putText(frame, status_text, (20, 35), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv.imshow("GestFlow Data Collector", frame)

# Clean up resources
capture.release()
cv.destroyAllWindows()
detector.close()
print("💾 Data collection closed safely.")