# ==========================================
# GESTFLOW GESTURE ENGINE
# ==========================================

import cv2 as cv
import mediapipe as mp
import numpy as np
import tensorflow as tf
import json
import os
import sys
import time
import threading

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# ── Model paths ──
MODEL_PATH       = os.path.join(BASE_DIR, 'gestflow_01_gesture_engine',
                                 'gesture_classifier.tflite')
HAND_LANDMARKER  = os.path.join(BASE_DIR, 'gestflow_01_gesture_engine',
                                 'hand_landmarker.task')
GESTURE_MAP_PATH = os.path.join(BASE_DIR, 'gestflow_01_gesture_engine',
                                 'gesture_map.json')

# ── Detection settings ──
CONFIDENCE_THRESHOLD = 0.80
GESTURE_HOLD_FRAMES  = 15
COOLDOWN_SECONDS     = 2

# ── Action callbacks registry ──
_action_callbacks = {}

# ── Shared grabbed state ──
_grabbed_packet      = None
_grabbed_content     = None
_grab_status         = None
_waiting_for_release = False


# ══════════════════════════════════════════
# NOTIFICATION SYSTEM
# ══════════════════════════════════════════

def _notify(title, message):
    """
    Cross-platform desktop notification.
    Automatically detects OS and uses correct method.
    """
    import platform
    os_name = platform.system()

    try:
        if os_name == 'Linux':
            # Linux — use notify-send directly
            import subprocess
            subprocess.Popen([
                'notify-send',
                f'🤚 GestFlow — {title}',
                message,
                '--urgency=normal',
                '--expire-time=3000'
            ])

        elif os_name == 'Windows':
            # Windows — use win10toast
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    f"🤚 GestFlow — {title}",
                    message,
                    duration=3,
                    threaded=True
                )
            except ImportError:
                # Fallback — use plyer
                from plyer import notification
                notification.notify(
                    title  =f"GestFlow — {title}",
                    message=message,
                    timeout=3
                )

        elif os_name == 'Darwin':
            # Mac — use osascript (built into macOS, zero install)
            import subprocess
            script = f'display notification "{message}" with title "GestFlow — {title}"'
            subprocess.Popen(['osascript', '-e', script])

    except Exception as e:
        # Silent fallback — terminal already shows everything
        pass


def _print_status(emoji, title, message):
    """
    Prints clean status to terminal.
    Always visible regardless of notification support.
    """
    print(f"\n{'─' * 40}")
    print(f"{emoji} {title}")
    print(f"   {message}")
    print(f"{'─' * 40}")


# ══════════════════════════════════════════
# LOAD RESOURCES
# ══════════════════════════════════════════

def _load_gesture_model():
    try:
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        print(f"✅ Gesture model loaded")
        return interpreter
    except Exception as e:
        print(f"❌ Could not load gesture model: {e}")
        return None


def _load_hand_detector():
    try:
        base_options = python.BaseOptions(
            model_asset_path=HAND_LANDMARKER
        )
        options = vision.HandLandmarkerOptions(
            base_options                 = base_options,
            running_mode                 = vision.RunningMode.IMAGE,
            num_hands                    = 1,
            min_hand_detection_confidence= 0.7,
            min_hand_presence_confidence = 0.5,
            min_tracking_confidence      = 0.5,
        )
        detector = vision.HandLandmarker.create_from_options(options)
        print(f"✅ Hand landmarker loaded")
        return detector
    except Exception as e:
        print(f"❌ Could not load hand landmarker: {e}")
        return None


def _load_gesture_map():
    try:
        with open(GESTURE_MAP_PATH, 'r') as f:
            gesture_map = json.load(f)
        print(f"✅ Gesture map loaded — {len(gesture_map)} gestures")
        return gesture_map
    except Exception as e:
        print(f"❌ Could not load gesture map: {e}")
        return {}


# ══════════════════════════════════════════
# ACTION REGISTRATION
# ══════════════════════════════════════════

def register_action(action_name, callback_fn):
    _action_callbacks[action_name] = callback_fn
    print(f"✅ Action registered: {action_name}")


def _trigger_action(action_name, gesture_info):
    callback = _action_callbacks.get(action_name)
    if callback:
        thread = threading.Thread(
            target=callback,
            args=(gesture_info,),
            daemon=True
        )
        thread.start()
    else:
        print(f"⚠️  No callback for: {action_name}")


# ══════════════════════════════════════════
# TERMINAL PROGRESS BAR
# Shows hold progress in terminal
# instead of camera window
# ══════════════════════════════════════════

def _print_progress(gesture_name, confidence, hold_count, hold_max):
    """
    Prints a progress bar in terminal showing hold progress.
    Updates on same line — no screen flooding.
    """
    progress  = min(hold_count / hold_max, 1.0)  # ← cap at 1.0
    bar_len   = 20
    filled    = int(bar_len * progress)
    bar       = '█' * filled + '░' * (bar_len - filled)
    percent   = int(progress * 100)

    print(
        f"\r  ✋ {gesture_name} ({confidence * 100:.0f}%)  "
        f"[{bar}] {percent}%   ",
        end='',
        flush=True
    )


# ══════════════════════════════════════════
# MAIN CAMERA LOOP — NO WINDOW
# ══════════════════════════════════════════

def start_gesture_engine():
    global _waiting_for_release

    print("\n🎥 GestFlow gesture engine running silently...")
    print("   Camera is active — no window shown")
    print("   Press Ctrl+C to stop\n")

    interpreter = _load_gesture_model()
    detector    = _load_hand_detector()
    gesture_map = _load_gesture_map()

    if not interpreter or not detector:
        print("❌ Cannot start gesture engine")
        return

    input_details  = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # ── Open camera silently ──
    capture = cv.VideoCapture(1)
    if not capture.isOpened():
        capture = cv.VideoCapture(0)
    if not capture.isOpened():
        print("❌ Cannot open camera")
        return

    print("✅ Camera active — show your hand!\n")
    print("Waiting for gesture...")

    # Notify user GestFlow is ready
    _notify("Ready", "Show your hand to gesture")

    # ── Hold tracking ──
    current_gesture_index = None
    hold_frame_count      = 0
    last_trigger_time     = 0
    last_printed_gesture  = None

    while True:
        isTrue, frame = capture.read()
        if not isTrue:
            continue

        frame     = cv.flip(frame, 1)
        h, w, _   = frame.shape
        rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        mp_image  = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        results = detector.detect(mp_image)

        if results.hand_landmarks:
            hand_landmarks = results.hand_landmarks[0]

            landmarks_list = []
            for lm in hand_landmarks:
                landmarks_list.extend([lm.x, lm.y, lm.z])

            input_data = np.array([landmarks_list], dtype=np.float32)
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()

            output_data     = interpreter.get_tensor(
                output_details[0]['index']
            )[0]
            predicted_class = int(np.argmax(output_data))
            confidence      = float(output_data[predicted_class])

            if confidence > CONFIDENCE_THRESHOLD:
                gesture_info = gesture_map.get(str(predicted_class), {})
                gesture_name = gesture_info.get('name', f"Gesture {predicted_class}")
                action       = gesture_info.get('action', '')
                emoji        = gesture_info.get('emoji', '✋')

                # Hold detection
                if predicted_class == current_gesture_index:
                    hold_frame_count += 1
                else:
                    current_gesture_index = predicted_class
                    hold_frame_count      = 1
                    _waiting_for_release  = False

                # Show progress bar in terminal
                _print_progress(
                    gesture_name,
                    confidence,
                    hold_frame_count,
                    GESTURE_HOLD_FRAMES
                )

                now = time.time()

                # Trigger when held long enough
                if (hold_frame_count >= GESTURE_HOLD_FRAMES and
                        action and
                        now - last_trigger_time > COOLDOWN_SECONDS and
                        not _waiting_for_release):

                    print()  # new line after progress bar
                    _print_status(emoji, gesture_name, f"Triggering {action}...")

                    # Desktop notification
                    _notify(gesture_name, f"Detected! Triggering {action}")

                    # Fire action
                    _trigger_action(action, {
                        **gesture_info,
                        'confidence': confidence,
                        'index'     : predicted_class
                    })

                    last_trigger_time    = now
                    hold_frame_count     = 0
                    _waiting_for_release = True

                    print("   Waiting for next gesture...\n")

            else:
                # Low confidence
                if current_gesture_index is not None:
                    print()  # clear progress bar line
                current_gesture_index = None
                hold_frame_count      = 0

        else:
            # No hand detected
            if current_gesture_index is not None:
                print()  # clear progress bar line
                print("   Hand removed\n")
            current_gesture_index = None
            hold_frame_count      = 0
            _waiting_for_release  = False

        # Small sleep to reduce CPU usage
        time.sleep(0.01)

    capture.release()
    detector.close()
    print("\n👋 Gesture engine stopped")