import cv2
import mediapipe as mp
import time
import keyboard

class EfficientHandDetector:
    def __init__(self, detection_conf=0.7, track_conf=0.6):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=track_conf
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [8, 12]  # Telunjuk dan jari tengah

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb)

    def get_fingertips(self, frame, hand_landmarks):
        h, w, _ = frame.shape
        points = []
        for tid in self.tip_ids:
            lm = hand_landmarks.landmark[tid]
            points.append((int(lm.x * w), int(lm.y * h)))
        return points

def draw_virtual_tiles(frame):
    h, w, _ = frame.shape
    lane_width = 160
    lane_height = 240
    spacing_small = 60
    spacing_big = 80
    start_y = h - lane_height - 40

    total_width = 4 * lane_width + 2 * spacing_small + spacing_big
    start_x = (w - total_width) // 2

    keys = ['d', 'f', 'j', 'k']
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]

    positions_x = [
        start_x,
        start_x + lane_width + spacing_small,
        start_x + 2 * lane_width + spacing_small + spacing_big,
        start_x + 3 * lane_width + 2 * spacing_small + spacing_big
    ]

    for i in range(4):
        x1 = positions_x[i]
        y1 = start_y
        x2 = x1 + lane_width
        y2 = y1 + lane_height

        cv2.rectangle(frame, (x1, y1), (x2, y2), colors[i], 2)
        cv2.putText(frame, keys[i], (x1 + 40, y2 - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, colors[i], 2)

def draw_triggers(frame):
    h, w, _ = frame.shape
    # Gambar hanya tombol ` (tanpa ENTER, UP, DOWN)
    rect_x1 = w - 120
    rect_y1 = h - 140
    rect_x2 = w - 20
    rect_y2 = h - 60
    cv2.rectangle(frame, (rect_x1, rect_y1), (rect_x2, rect_y2), (100, 100, 255), 2)
    cv2.putText(frame, '`', (rect_x1 + 30, rect_y2 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 100, 255), 2)

def get_key_from_position(x, y, frame_w=1920, frame_h=1080):
    lane_width = 160
    lane_height = 240
    spacing_small = 60
    spacing_big = 80

    start_y = frame_h - lane_height - 40
    end_y = start_y + lane_height

    start_x = (frame_w - (4 * lane_width + 2 * spacing_small + spacing_big)) // 2
    positions_x = [
        start_x,
        start_x + lane_width + spacing_small,
        start_x + 2 * lane_width + spacing_small + spacing_big,
        start_x + 3 * lane_width + 2 * spacing_small + spacing_big
    ]

    if start_y <= y <= end_y:
        for i, x1 in enumerate(positions_x):
            if x1 <= x < x1 + lane_width:
                return ['d', 'f', 'j', 'k'][i]
    return None

def main():
    cap = cv2.VideoCapture(1)
    cap.set(3, 1920)
    cap.set(4, 1080)
    detector = EfficientHandDetector()
    pTime = 0

    key_hold_status = {k: False for k in ['`', 'd', 'f', 'j', 'k']}
    key_temp = key_hold_status.copy()

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        result = detector.detect(frame)
        draw_virtual_tiles(frame)
        draw_triggers(frame)

        touched_keys = set()

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                for cx, cy in detector.get_fingertips(frame, hand_landmarks):
                    cv2.circle(frame, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                    h, w, _ = frame.shape

                    # Deteksi tombol `
                    if w - 120 <= cx <= w - 20 and h - 140 <= cy <= h - 60:
                        touched_keys.add('`')

                    key = get_key_from_position(cx, cy, w, h)
                    if key:
                        touched_keys.add(key)

        for key in key_temp:
            is_touched = key in touched_keys
            if is_touched != key_temp[key]:
                if is_touched:
                    keyboard.press(key)
                    key_hold_status[key] = True
                else:
                    keyboard.release(key)
                    key_hold_status[key] = False
                key_temp[key] = is_touched

        cTime = time.time()
        fps = 1 / (cTime - pTime + 1e-5)
        pTime = cTime
        cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        cv2.imshow("Piano Tiles - Clean Version", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

