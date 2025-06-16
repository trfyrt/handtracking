import cv2
import mediapipe as mp
import time
import keyboard

class EfficientHandDetector:
    def _init_(self, detection_conf=0.7, track_conf=0.6):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=track_conf
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_id = 8  # jari telunjuk

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb)

    def get_fingertip(self, frame, hand_landmarks):
        h, w, _ = frame.shape
        lm = hand_landmarks.landmark[self.tip_id]
        return int(lm.x * w), int(lm.y * h)

def draw_virtual_tiles(frame):
    h, w, _ = frame.shape
    lane_width = 120
    lane_height = 180

    spacing_small = 40
    spacing_big = 80

    # Hit area di bawah layar, naik sedikit dari bawah
    start_y = h - lane_height - 40

    # Total width dari semua tombol dan jarak
    total_width = (
        4 * lane_width + 2 * spacing_small + spacing_big
    )
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
    cv2.rectangle(frame, (20, 20), (80, 80), (100, 100, 255), 2)
    cv2.putText(frame, '`', (45, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 255), 2)

    cv2.rectangle(frame, (500, 100), (600, 160), (255, 150, 0), 2)
    cv2.putText(frame, 'ENTER', (510, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 150, 0), 2)

    cv2.rectangle(frame, (500, 180), (600, 240), (0, 255, 255), 2)
    cv2.putText(frame, 'UP', (530, 230), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    cv2.rectangle(frame, (500, 260), (600, 320), (0, 200, 255), 2)
    cv2.putText(frame, 'DOWN', (510, 310), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 255), 2)

def get_key_from_position(x, y):
    lane_width = 120
    lane_height = 180
    spacing_small = 40
    spacing_big = 80
    frame_w = 1920
    frame_h = 1080

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
    key_timers = {}
    repeat_delay_arrow = 0.1

    key_hold_status = {
        '`': False,
        'enter': False,
        'd': False,
        'f': False,
        'j': False,
        'k': False,
    }

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 0)
        result = detector.detect(frame)
        draw_virtual_tiles(frame)
        draw_triggers(frame)

        now = time.time()
        touched_keys = set()

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                cx, cy = detector.get_fingertip(frame, hand_landmarks)
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                # Hold: `
                if 20 <= cx <= 80 and 20 <= cy <= 80:
                    touched_keys.add('`')
                    cv2.putText(frame, "`", (cx - 30, cy - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

                # Hold: ENTER
                if 500 <= cx <= 600 and 100 <= cy <= 160:
                    touched_keys.add('enter')
                    cv2.putText(frame, "ENTER", (cx - 40, cy - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 150, 0), 2)

                # Press-and-release: UP
                if 500 <= cx <= 600 and 180 <= cy <= 240:
                    last_time = key_timers.get('up', 0)
                    if now - last_time > repeat_delay_arrow:
                        keyboard.press_and_release('up')
                        key_timers['up'] = now
                        cv2.putText(frame, "UP", (cx - 20, cy - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                # Press-and-release: DOWN
                if 500 <= cx <= 600 and 260 <= cy <= 320:
                    last_time = key_timers.get('down', 0)
                    if now - last_time > repeat_delay_arrow:
                        keyboard.press_and_release('down')
                        key_timers['down'] = now
                        cv2.putText(frame, "DOWN", (cx - 30, cy - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

                # Hold piano key
                key = get_key_from_position(cx, cy)
                if key:
                    touched_keys.add(key)
                    cv2.putText(frame, f"{key.upper()}", (cx - 30, cy - 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Process key holds and releases
        for k in key_hold_status:
            if k in touched_keys:
                if not key_hold_status[k]:
                    keyboard.press(k)
                    key_hold_status[k] = True
            else:
                if key_hold_status[k]:
                    keyboard.release(k)
                    key_hold_status[k] = False

        # FPS display
        cTime = time.time()
        fps = 1 / (cTime - pTime + 1e-5)
        pTime = cTime
        cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        cv2.imshow("Piano Tiles with Triggers", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()