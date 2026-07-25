import cv2 as cv
import mediapipe as mp
import numpy as np
import tensorflow as tf
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ==========================================
# STEP 1: INITIALIZATION
# ==========================================
# Load the optimized hand gesture classification model
try:
    gesture_interpreter = tf.lite.Interpreter(model_path='gesture_classifier.tflite')
    gesture_interpreter.allocate_tensors()
except Exception as e:
    print(f"❌ Error loading gesture model: {e}")
    exit()

# Get input and output tensor details
input_details = gesture_interpreter.get_input_details()
output_details = gesture_interpreter.get_output_details()

# Initialize the MediaPipe hand landmark detector
base_options = python.BaseOptions(model_asset_path = 'hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options = base_options,
    running_mode = vision.RunningMode.IMAGE,
    num_hands = 1,
    min_hand_detection_confidence = 0.7,
    min_hand_presence_confidence = 0.5,
)
detector = vision.HandLandmarker.create_from_options(options)

# Human-readable gesture names corresponding to model output labels
GESTURE_NAMES = {0: "FIST / GRAB ✊", 1: "OPEN / RELEASE 🖐️", 2: "PINCH 🤏", 3:"THROW RIGHT",4:"THROW lEFT ",5:"EXPAND (spread fingers) 🖖", 6:"ELECT MULTIPLE (two fingers up) ✌️",7:"CANCEL/UNDO (shake fingers) 🤙"}

# =========================================
# STEP 2: VIDEO CAPTURE & PREDICTION LOOP
# =========================================
# open the webcam feed
capture = cv.VideoCapture(1)
print("🚀 GestFlow Live Engine Active (Modern Tasks API)! Press 'q' to quit.")
while capture.isOpened():
    isTrue, frame = capture.read()
    if not isTrue:
        print('The frame is not yet captured')
        continue
    frame = cv.flip(frame,1)
    h,w,c = frame.shape
    # convert the frame from BGR to RGB
    rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    # Run the hand detector
    results = detector.detect(mp_image)
    prediction_text = "NO Hand Detcted"
    confidence_text = ""

    # Check if the hand is detected
    if results.hand_landmarks:
        hand_landmarks = results.hand_landmarks[0]
        # Extract the 63 coordinates
        landmarks_list = []
        for lm in hand_landmarks:
            landmarks_list.extend([lm.x,lm.y,lm.z])
            cx,cy = int(lm.x*w),int(lm.y*h)
            cv.circle(frame, (cx, cy), 4, (0, 255, 125), -1)
        # onvert to numpy array and shape to (1,63) for any custom model
        input_data = np.array([landmarks_list], dtype=np.float32)

        # Run Inference through your custom gesture model
        gesture_interpreter.set_tensor(input_details[0]['index'],input_data)
        gesture_interpreter.invoke()

        # Extract output distribution
        output_data = gesture_interpreter.get_tensor(output_details[0]['index'])[0]
        predicted_class = np.argmax(output_data)
        confidence = output_data[predicted_class]

        if confidence > 0.80:
            prediction_text = GESTURE_NAMES.get(predicted_class, "Unknown")
            confidence_text = f"({confidence * 100:.1f}%)"
        else:
            prediction_text = "Uncertain..."
    # Build the HUD overlay banner
    cv.rectangle(frame,(0,0),(w ,65), (45,45,45),-1)
    cv.putText(frame, f"Glow Engine: {prediction_text} {confidence_text}", (20, 42), 
                cv.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 125), 2, cv.LINE_AA)
    cv.imshow("GestFlow Live Diagnostics", frame)

    if cv.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up resources
capture.release()
cv.destroyAllWindows()
detector.close()
print("👋 Live engine stopped successfully.")


