from gesture_detector import get_gesture

while True:
    g = get_gesture(show_cam=True)
    print("Gesture:", g)