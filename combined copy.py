import sys
import os
import asyncio
import tempfile
import threading
import re
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen, QGuiApplication
from PyQt5.QtCore import Qt, QRect
from PIL import ImageGrab
from paddleocr import PaddleOCR
import edge_tts

# -----------------------------------------
# 설정
# -----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNIP_PATH = os.path.join(BASE_DIR, 'snip.png')
OUTPUT_DIR = os.path.join(BASE_DIR, 'result')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'snip_ocr.txt')
VOICE_NAME = "ko-KR-SunHiNeural"

# PaddleOCR 초기화 (한국어)
ocr = PaddleOCR(
    use_textline_orientation=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    lang='korean'
)

class SnippingTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.5)
        self.setCursor(Qt.CrossCursor)
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.begin = self.end = None
        self.save_path = SNIP_PATH
        self.showFullScreen()
        print("🖼️ Snipping tool started. Drag to select area.")

    def paintEvent(self, event):
        if self.begin and self.end:
            painter = QPainter(self)
            painter.setPen(QPen(Qt.red, 2))
            painter.drawRect(QRect(self.begin, self.end).normalized())

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        self.close()
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        img.save(self.save_path)
        print(f"📸 Screenshot saved to {self.save_path}")
        # 백그라운드에서 OCR + TTS 스트리밍 실행
        threading.Thread(target=stream_pipeline, args=(self.save_path,), daemon=True).start()

# -----------------------------------------
# OCR + 스트리밍 TTS 파이프라인
# -----------------------------------------
def stream_pipeline(image_path):
    print("🧠 Running PaddleOCR...")
    raw = ocr.predict(image_path)
    lines = []
    if isinstance(raw, list) and raw:
        if isinstance(raw[0], dict):
            for page in raw:
                lines.extend(page.get('rec_texts', []))
        else:
            for line in raw:
                for item in line:
                    if isinstance(item, list):
                        if len(item) >= 2:
                            t = item[1]
                            lines.append(t[0] if isinstance(t, tuple) else t)
    full_text = "\n".join(lines)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"✅ OCR text saved to {OUTPUT_FILE}")

    # 문장 단위로 분할
    sentences = []
    for line in lines:
        # 마침표, 물음표, 느낌표 기준
        parts = re.split(r'(?<=[\.\?!])\s*', line)
        sentences.extend([s.strip() for s in parts if s.strip()])

    # TTS 스트리밍: 문장별로 생성·재생
    for idx, sentence in enumerate(sentences):
        temp_audio = os.path.join(tempfile.gettempdir(), f'snip_tts_{idx}.mp3')
        async def gen_tts(text, path):
            tts = edge_tts.Communicate(text=text, voice=VOICE_NAME)
            await tts.save(path)
        print(f"🔉 Generating TTS for sentence {idx+1}/{len(sentences)}...")
        asyncio.run(gen_tts(sentence, temp_audio))
        print(f"▶️ Playing sentence {idx+1}")
        os.startfile(temp_audio)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = SnippingTool()
    sys.exit(app.exec_())
