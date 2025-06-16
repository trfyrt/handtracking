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

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)  # ✅ Mirror mode aktif

        result = detector.detect(frame)
        draw_virtual_tiles(frame)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                cx, cy = detector.get_fingertip(frame, hand_landmarks)
                cv2.circle(frame, (cx, cy), 10, (0, 255, 0), cv2.FILLED)

                key = get_key_from_position(cx, cy)

                repeat_delay = 0.045  # 50ms = 20x per detik

                # Simpan waktu terakhir tombol ditekan ulang
                if 'key_timers' not in locals():
                    key_timers = {}

                if key:
                    now = time.time()
                    last_time = key_timers.get(key, 0)

                    if now - last_time > repeat_delay:
                        keyboard.press_and_release(key)
                        key_timers[key] = now

                    cv2.putText(frame, f"{key}", (cx - 30, cy - 15),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                else:
                    key_timers.clear()

        cTime = time.time()
        fps = 1 / (cTime - pTime + 1e-5)
        pTime = cTime
        cv2.putText(frame, f'FPS: {int(fps)}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        cv2.imshow("Piano Tiles with 2 Hands", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
