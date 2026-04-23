import cv2
import pyttsx3
import threading
import queue
import time
from ultralytics import YOLO
import easyocr
import face_recognition
import numpy as np

# ============================================
# VOICE ENGINE — priority queue se bolega
# ============================================
class VoiceEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 160)   # speed
        self.engine.setProperty('volume', 1.0)
        self.queue = queue.PriorityQueue()
        self.last_spoken = {}  # repeat avoid karne ke liye
        
        # Background thread mein chalaao
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def speak(self, text, priority=5, cooldown=3):
        """
        priority 1 = URGENT (danger!)
        priority 5 = normal info
        cooldown = same cheez dobara kitne sec baad bolega
        """
        now = time.time()
        if text in self.last_spoken:
            if now - self.last_spoken[text] < cooldown:
                return  # abhi nahi bolna same cheez
        self.last_spoken[text] = now
        self.queue.put((priority, text))

    def _run(self):
        while True:
            try:
                priority, text = self.queue.get(timeout=1)
                self.engine.say(text)
                self.engine.runAndWait()
            except queue.Empty:
                continue

# ============================================
# OBJECT DETECTOR — YOLOv8
# ============================================
class ObjectDetector:
    def __init__(self):
        # yolov8n = nano, fastest — RPi ke liye perfect
        self.model = YOLO('yolov8n.pt')
        
        # Dangerous objects — highest priority
        self.danger_objects = {
            'car', 'truck', 'motorcycle', 'bus',
            'bicycle', 'person', 'dog', 'stairs'
        }

    def detect(self, frame):
        results = self.model(frame, verbose=False)[0]
        detections = []

        for box in results.boxes:
            conf = float(box.conf)
            if conf < 0.5:
                continue

            label = self.model.names[int(box.cls)]
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Distance estimate — bounding box size se
            # (Proper depth ke liye MiDaS use karenge v2 mein)
            box_height = y2 - y1
            frame_height = frame.shape[0]
            
            if box_height > frame_height * 0.6:
                distance = "very close — 1 meter"
                priority = 1  # DANGER
            elif box_height > frame_height * 0.3:
                distance = "nearby — 2 to 3 meters"
                priority = 2
            elif box_height > frame_height * 0.1:
                distance = "ahead — 4 to 6 meters"
                priority = 4
            else:
                distance = "far away"
                priority = 6

            # Danger objects ko extra priority
            if label in self.danger_objects:
                priority = max(1, priority - 2)

            detections.append({
                'label': label,
                'distance': distance,
                'priority': priority,
                'bbox': (x1, y1, x2, y2)
            })

        return detections

# ============================================
# OCR READER — book/text padhega
# ============================================
class TextReader:
    def __init__(self):
        # Hindi + English dono support
        self.reader = easyocr.Reader(['en', 'hi'])
        self.reading_mode = False  # user activate karega

    def read_text(self, frame):
        results = self.reader.readtext(frame)
        texts = []
        for (bbox, text, conf) in results:
            if conf > 0.6 and len(text.strip()) > 2:
                texts.append(text.strip())
        return ' '.join(texts) if texts else None

# ============================================
# FACE RECOGNIZER
# ============================================
class FaceRecognizer:
    def __init__(self):
        # Known faces database
        # format: {"Mom": encoding, "Dad": encoding}
        self.known_faces = {}
        self.known_names = []
        self.known_encodings = []

    def add_face(self, name, image_path):
        """Naya face add karo database mein"""
        img = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(img)
        if encodings:
            self.known_encodings.append(encodings[0])
            self.known_names.append(name)
            print(f"✅ {name} added to database")

    def recognize(self, frame):
        # Har frame mein nahi chalao — heavy hai
        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        names = []
        for encoding in encodings:
            if not self.known_encodings:
                names.append("Unknown person")
                continue
            matches = face_recognition.compare_faces(
                self.known_encodings, encoding, tolerance=0.6
            )
            name = "Unknown person"
            if True in matches:
                idx = matches.index(True)
                name = self.known_names[idx]
            names.append(name)

        return names

# ============================================
# MAIN AI GLASS — sab ek saath
# ============================================
class AIGlass:
    def __init__(self):
        print("🔄 Loading AI models... please wait")
        self.voice = VoiceEngine()
        self.detector = ObjectDetector()
        self.ocr = TextReader()
        self.face_rec = FaceRecognizer()

        self.frame_count = 0
        self.ocr_mode = False

        # Apne known faces add karo yahan
        # self.face_rec.add_face("Mom", "mom.jpg")
        # self.face_rec.add_face("Friend Raju", "raju.jpg")

        print("✅ AI Glass ready!")
        self.voice.speak("AI Glass activated. I am ready to help.", priority=1)

    def process_frame(self, frame):
        self.frame_count += 1

        # --- Object Detection (har frame) ---
        detections = self.detector.detect(frame)
        for det in detections[:2]:  # top 2 objects bolega
            msg = f"{det['label']} {det['distance']}"
            self.voice.speak(msg, priority=det['priority'])

            # Frame pe draw karo (demo ke liye)
            x1, y1, x2, y2 = det['bbox']
            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
            cv2.putText(frame, f"{det['label']} {det['distance']}",
                       (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (0,255,0), 1)

        # --- Face Recognition (har 30 frames) ---
        if self.frame_count % 30 == 0:
            names = self.face_rec.recognize(frame)
            for name in names:
                if name == "Unknown person":
                    self.voice.speak("Unknown person nearby", priority=3)
                else:
                    self.voice.speak(f"{name} is here", priority=2, cooldown=10)

        # --- OCR Mode (user ne activate kiya ho toh) ---
        if self.ocr_mode and self.frame_count % 60 == 0:
            text = self.ocr.read_text(frame)
            if text:
                self.voice.speak(f"Reading: {text}", priority=3)

        return frame

    def run(self):
        """Laptop webcam se demo chalao"""
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        print("\n🎮 Controls:")
        print("  'o' = OCR book reading mode toggle")
        print("  'q' = quit\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = self.process_frame(frame)

            # Status show karo
            status = "OCR ON" if self.ocr_mode else "Detection mode"
            cv2.putText(frame, f"AI Glass | {status}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (0, 255, 255), 2)

            cv2.imshow("AI Glass — Demo", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('o'):
                self.ocr_mode = not self.ocr_mode
                mode = "ON" if self.ocr_mode else "OFF"
                self.voice.speak(f"Reading mode {mode}", priority=2)

        cap.release()
        cv2.destroyAllWindows()

# ============================================
# CHALAAO!
# ============================================
if __name__ == "__main__":
    glass = AIGlass()
    glass.run()


"""## Yeh code kya kya karta hai abhi ✅

| Feature | Status | Kaise |
|---|---|---|
| Object detection | ✅ Ready | YOLOv8 nano, 80 objects |
| Distance estimate | ✅ Ready | Bounding box size se |
| Voice output | ✅ Ready | pyttsx3 offline |
| Priority system | ✅ Ready | Car > person > table |
| OCR book reading | ✅ Ready | 'o' press karo |
| Face recognition | ✅ Ready | faces add karo |
| Repeat avoid | ✅ Ready | Cooldown system |"""

