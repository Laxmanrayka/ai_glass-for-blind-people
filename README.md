# 🕶️ AI Glass — Navigation Edition

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square)

AI Glass is a passion project I built to help visually impaired people move around independently. It runs on a simple webcam and talks to you — telling you what's nearby, reading signs and text out loud, and guiding you to your destination step by step.

No fancy hardware. Just Python, a webcam, and a speaker.

---

## What it does

- Detects obstacles like cars, people, chairs in real time and says how far and which direction
- Reads text from the environment aloud — signs, boards, labels (English + Hindi)
- Gives turn-by-turn walking directions to any destination using OpenStreetMap
- Describes the full scene around you on demand
- Shows a live HUD with mode, city, FPS and current nav step

---

## Tech used

- **YOLOv8** (Ultralytics) — object detection
- **EasyOCR** — text recognition
- **OpenCV** — camera and video
- **pyttsx3 / Windows SAPI** — voice output
- **OpenStreetMap + OSRM** — geocoding and routing
- **Python 3.8+**

---

## Getting started

```bash
git clone https://github.com/Laxmanrayka/ai_glass-for-blind-people.git
cd ai_glass-for-blind-people
C:\Users\dell\.EasyOCR\aiglass_env\Scripts\activate
pip install -r requirements.txt
python ai_glass.py
```

---

## Controls

| Key | What it does |
|-----|--------------|
| `n` | Type a destination |
| `.` | Next step |
| `,` | Previous step |
| `s` | Repeat current step |
| `x` | Stop navigation |
| `o` | OCR mode on/off |
| `r` | Reading session on/off |
| `d` | Describe scene |
| `q` | Quit |

---

## Project structure
ai_glass-for-blind-people/
├── ai_glass.py
├── requirements.txt
├── .gitignore
└── README.md
