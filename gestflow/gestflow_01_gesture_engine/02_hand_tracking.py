import cv2 as cv
import mediapipe as mp
import time  # <--- Added for reliable timestamps
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ==========================================
# STEP 1: INITIALIZATION & CONFIGURATION
# ==========================================
base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,                            
    min_hand_detection_confidence=0.5,      
    min_hand_presence_confidence=0.5,       
    min_tracking_confidence=0.5             
)
detector = vision.HandLandmarker.create_from_options(options)

# ==========================================
# STEP 2: VIDEO CAPTURE LOOP
# ==========================================
capture = cv.VideoCapture(1)  # Assumes your target camera is index 1

print("GestFlow Engine Running...")
print("⚠️ CRITICAL: Click on the video window and press 'q' to safely exit!")

# Track start time to calculate true elapsed milliseconds
start_time = time.time()

while True:
    isTrue, frame = capture.read()
    if not isTrue:
        print("Failed to grab frame from camera.")
        break
        
    frame = cv.flip(frame, 1)
    rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    # Generate a flawless, steadily increasing timestamp using Python's system time
    timestamp_ms = int((time.time() - start_time) * 1000)
    
    # Process the frame
    results = detector.detect_for_video(mp_image, timestamp_ms)

    # ==========================================
    # STEP 3: PROCESSING & DRAWING RESULTS
    # ==========================================
    if results.hand_landmarks:
        for hand_landmarks in results.hand_landmarks:
            h, w, c = frame.shape
            for landmark in hand_landmarks:
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                # Draw high-visibility bright green dots on joints
                cv.circle(frame, (cx, cy), 6, (0, 255, 0), cv.FILLED)

    # Display window
    cv.imshow("GestFlow Hand Tracking", frame)
    
    # Explicitly catch the 'q' key or check if user closed the window frame
    key = cv.waitKey(1) & 0xFF
    if key == ord('q'):
        print("Safely closing GestFlow...")
        break

# Clean up resources completely
capture.release()
cv.destroyAllWindows()