National Library of Korea Audio (OCR → TTS Toolbar)
A desktop toolbar that lets you capture any screen area, extract text with PaddleOCR, and listen to it with edge-tts.
Note: The National Library of Korea is a public library located in South Korea.

Features
Capture → OCR → Speech
Select an on-screen region, run OCR, generate an MP3, and play it immediately.
OCR text is saved to result/snip_ocr.txt.

Audio controls
Pause, Play, Restart (from the beginning), and Stop.

Continuous reading (auto page-turning)

Mark a reading area → 2) Mark the Next Page button → 3) After each page is read, the toolbar auto-clicks “next” and continues.

Loading screen
Shows progress while initializing Pygame / OCR / TTS.

UI Overview
Top bar: toggle/title/close. The window is frameless and always on top.

Toolbar buttons: Capture · Pause · Play · Restart · Stop (Exit Audio) · Continuous Reading.
If icon files are missing, emoji/text icons are used automatically.

Window title: “국립중앙도서관 오디오” (National Library of Korea Audio).

Project Structure
arduino

project/

├─ main.py

├─ combined.py

├─ toolbar.py

├─ image/                # optional icon files (emoji fallback if missing)

└─ result/
   ├─ snip.png          # latest captured image
   └─ snip_ocr.txt       # OCR output text
   
result/snip.png and result/snip_ocr.txt are created automatically at runtime.

Quick Start
1) Setup
bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
Example requirements.txt:
nginx
PyQt5
paddleocr
edge-tts
pygame
Pillow
pyautogui

2) Run
bash
python main.py
main.py displays a loading screen, initializes components, then shows the toolbar.

How to Use
Basic reading
Click Capture, then drag to select the screen area to read.

OCR runs, TTS generates audio, and playback starts automatically.

Continuous reading
Click Continuous Reading and select the reading area on the current page.

Click the Next Page button on your viewer/app to register it.

After finishing a page, the app auto-clicks Next and continues to the next page.

Audio controls
Pause / Play / Restart / Stop are available.

If the detected text includes Korean, a Korean voice (e.g., ko-KR-SunHiNeural) is chosen; otherwise, an English voice (e.g., en-US-JennyNeural) is used.

Tips & Troubleshooting
Slow first run: Initializing OCR models and TTS can take time on first launch (a progress indicator is shown).

No icon files: The app automatically falls back to emoji/text icons.

Output locations: Captures go to result/snip.png; OCR text to result/snip_ocr.txt.

Developer Notes
Entry point: main.py (loading screen, initialization thread, toolbar spawn).

Core pipeline: combined.py handles capture → OCR → TTS (MP3) → playback.

UI & actions: toolbar.py manages buttons and continuous reading (auto next-page click).

