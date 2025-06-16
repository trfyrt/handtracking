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
    key_timers = {}

    repeat_delay_arrow = 0.25  # UP/DOWN delay

    # Semua tombol mode hold
    key_hold_status = {
        '`': False,
        'enter': False,
        'd': False,
        'f': False,
        'j': False,
        'k': False
    }

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        result = detector.detect(frame)
        draw_virtual_tiles(frame)
        draw_triggers(frame)

        now = time.time()

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                cx, cy = detector.get_fingertip(frame, hand_landmarks)
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                # Backtick HOLD
                if 20 <= cx <= 80 and 20 <= cy <= 80:
                    if not key_hold_status['`']:
                        keyboard.press('`')
                        key_hold_status['`'] = True
                    cv2.putText(frame, "`", (cx - 30, cy - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
                else:
                    if key_hold_status['`']:
                        keyboard.release('`')
                        key_hold_status['`'] = False

                # ENTER HOLD
                if 500 <= cx <= 600 and 100 <= cy <= 160:
                    if not key_hold_status['enter']:
                        keyboard.press('enter')
                        key_hold_status['enter'] = True
                    cv2.putText(frame, "ENTER", (cx - 40, cy - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 150, 0), 2)
                else:
                    if key_hold_status['enter']:
                        keyboard.release('enter')
                        key_hold_status['enter'] = False

                # UP with delay
                if 500 <= cx <= 600 and 180 <= cy <= 240:
                    last_time = key_timers.get('up', 0)
                    if now - last_time > repeat_delay_arrow:
                        keyboard.press_and_release('up')
                        key_timers['up'] = now
                        cv2.putText(frame, "UP", (cx - 20, cy - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                # DOWN with delay
                if 500 <= cx <= 600 and 260 <= cy <= 320:
                    last_time = key_timers.get('down', 0)
                    if now - last_time > repeat_delay_arrow:
                        keyboard.press_and_release('down')
                        key_timers['down'] = now
                        cv2.putText(frame, "DOWN", (cx - 30, cy - 15),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)

                # Piano HOLD keys (d, f, j, k)
                key = get_key_from_position(cx, cy)
                for k in ['d', 'f', 'j', 'k']:
                    if key == k:
                        if not key_hold_status[k]:
                            keyboard.press(k)
                            key_hold_status[k] = True
                            cv2.putText(frame, f"{k.upper()}", (cx - 30, cy - 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    else:
                        if key_hold_status[k]:
                            keyboard.release(k)
                            key_hold_status[k] = False
        else:
            # Tidak ada tangan: pastikan semua tombol HOLD dilepas
            for k in key_hold_status:
                if key_hold_status[k]:
                    keyboard.release(k)
                    key_hold_status[k] = False

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
