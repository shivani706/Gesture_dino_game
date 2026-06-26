import cv2
import numpy as np
import mediapipe as mp

def main():
    # MediaPipe Tasks
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    # Download this model file once (I tell you how below)
    MODEL_PATH = "hand_landmarker.task"

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
    timestamp_ms = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Camera not working")
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # VIDEO mode needs timestamp (ms)
        timestamp_ms += 33
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        # Draw landmarks (simple dots)
        if result.hand_landmarks:
            h, w, _ = frame.shape
            for hand in result.hand_landmarks:
                for lm in hand:
                    x, y = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

        cv2.imshow("HandLandmarker (Tasks) Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()