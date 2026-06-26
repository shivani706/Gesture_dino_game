import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

MODEL_PATH = "hand_landmarker.task"

BaseOptions = mp_tasks.BaseOptions
HandLandmarker = vision.HandLandmarker
HandLandmarkerOptions = vision.HandLandmarkerOptions
VisionRunningMode = vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.6,
)

landmarker = HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

timestamp_ms = 0


def _dist(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))


def get_gesture():
    """
    Returns: (gesture, frame_bgr)
      gesture: "JUMP" | "BEND" | "RUN" | "NONE"
      frame_bgr: OpenCV frame for embedding in pygame
    """
    global timestamp_ms

    ok, frame = cap.read()
    if not ok:
        return "NONE", None

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    timestamp_ms += 33
    result = landmarker.detect_for_video(mp_image, timestamp_ms)

    gesture = "NONE"

    if result.hand_landmarks:
        hand = result.hand_landmarks[0]
        lms = [(lm.x, lm.y) for lm in hand]

        wrist = lms[0]
        thumb_tip = lms[4]
        index_tip = lms[8]

        # RUN (pinch)
        if _dist(thumb_tip, index_tip) < 0.05:
            gesture = "RUN"

        # BEND (fist)
        elif all(_dist(lms[i], wrist) < 0.15 for i in [8, 12, 16, 20]):
            gesture = "BEND"

        # JUMP (L-shape)
        else:
            index_pip = lms[6]
            if index_tip[1] < index_pip[1] and _dist(thumb_tip, wrist) > 0.20:
                gesture = "JUMP"

    return gesture, frame


def release():
    cap.release()
    cv2.destroyAllWindows()