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
        self.tip_id = 8  # jari telunjuk

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb)

    def get_fingertip(self, frame, hand_landmarks):
        h, w, _ = frame.shape
        lm = hand_landmarks.landmark[self.tip_id]
        return int(lm.x * w), int(lm.y * h)

def draw_virtual_tiles(frame):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255)]
    keys = ['d', 'f', 'j', 'k']
    for i in range(4):
        x1 = 100 + i * 100
        x2 = x1 + 100
        cv2.rectangle(frame, (x1, 360), (x2, 440), colors[i], 2)
        cv2.putText(frame, keys[i], (x1 + 40, 430), cv2.FONT_HERSHEY_SIMPLEX, 1, colors[i], 2)

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
    if 360 <= y <= 440:
        if 100 <= x < 200:
            return 'd'
        elif 200 <= x < 300:
            return 'f'
        elif 300 <= x < 400:
            return 'j'
        elif 400 <= x < 500:
            return 'k'
    return None

def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    detector = EfficientHandDetector()
    pTime = 0

    # Status boolean tombol hold
    key_hold_status = {
        '`': False,
        'enter': False,
        'd': False,
        'f': False,
        'j': False,
        'k': False,
    }

    key_temp = {
        '`': False,
        'enter': False,
        'd': False,
        'f': False,
        'j': False,
        'k': False,
    }

    last_arrow_time = {
        'up': 0,
        'down': 0
    }

    repeat_delay_arrow = 0.1

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
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
                    if now - last_arrow_time['up'] > repeat_delay_arrow:
                        keyboard.press_and_release('up')
                        last_arrow_time['up'] = now
                        cv2.putText(frame, "UP", (cx - 20, cy - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                # Press-and-release: DOWN
                if 500 <= cx <= 600 and 260 <= cy <= 320:
                    if now - last_arrow_time['down'] > repeat_delay_arrow:
                        keyboard.press_and_release('down')
                        last_arrow_time['down'] = now
                        cv2.putText(frame, "DOWN", (cx - 30, cy - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

                # Detect area dfjk
                key = get_key_from_position(cx, cy)
                if key:
                    touched_keys.add(key)
                    cv2.putText(frame, f"{key.upper()}", (cx - 30, cy - 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Hold logic pakai boolean
        for key in key_temp:
            is_touched = key in touched_keys

            if is_touched != key_temp[key]:
                if is_touched:
                    keyboard.press(key)
                    key_hold_status[key] = True
                else:
                    keyboard.release(key)
                    key_hold_status[key] = False
                key_temp[key] = is_touched  # update temp state

        # FPS
        cTime = time.time()
        fps = 1 / (cTime - pTime + 1e-5)
        pTime = cTime
        cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        cv2.imshow("Piano Tiles with Hold System", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
