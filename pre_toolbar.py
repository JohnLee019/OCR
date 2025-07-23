import sys
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
from qframelesswindow import FramelessWindow

import pytesseract
from PIL import ImageGrab
import pyttsx3

class ScreenBook(FramelessWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("스크린북 툴바")
        self.is_tts_play = False
        self.tts_engine = pyttsx3.init()
        self.captured_text = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.snip_btn = QPushButton("📸 캡처")
        self.snip_btn.clicked.connect(self.snip_screen)
        layout.addWidget(self.snip_btn)

        self.stop_btn = QPushButton("⏸ 일시정지")
        self.stop_btn.clicked.connect(self.stop_tts)
        layout.addWidget(self.stop_btn)

        self.resume_btn = QPushButton("▶ 재시작")
        self.resume_btn.clicked.connect(self.resume_tts)
        layout.addWidget(self.resume_btn)

        self.setLayout(layout)  # ← 핵심 수정!

    def snip_screen(self):
        img = ImageGrab.grab()
        self.captured_text = pytesseract.image_to_string(img, lang="eng+kor")
        self.tts_engine.say(self.captured_text)
        self.tts_engine.runAndWait()
        self.is_tts_play = True

    def stop_tts(self):
        if self.is_tts_play:
            self.tts_engine.stop()
            self.is_tts_play = False

    def resume_tts(self):
        if not self.is_tts_play and self.captured_text:
            self.tts_engine.say(self.captured_text)
            self.tts_engine.runAndWait()
            self.is_tts_play = True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ScreenBook()
    win.show()
    sys.exit(app.exec_())
