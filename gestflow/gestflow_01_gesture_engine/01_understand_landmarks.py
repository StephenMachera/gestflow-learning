import mediapipe as mp
from mediapipe.tasks.python import vision

# Get the hand landmark names from the vision module
# MediaPipe tracks 21 landmarks on each hand
hand_landmark_names = [
    "WRIST", "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_FINGER_MCP", "INDEX_FINGER_PIP", "INDEX_FINGER_DIP", "INDEX_FINGER_TIP",
    "MIDDLE_FINGER_MCP", "MIDDLE_FINGER_PIP", "MIDDLE_FINGER_DIP", "MIDDLE_FINGER_TIP",
    "RING_FINGER_MCP", "RING_FINGER_PIP", "RING_FINGER_DIP", "RING_FINGER_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP"
]

# Print all 21 landmark names
print("The 21 landmarks MediaPipe tracks:\n")

for idx, landmark_name in enumerate(hand_landmark_names):
    print(f"  {idx:2d} → {landmark_name}")