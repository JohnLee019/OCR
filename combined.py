import sys
import os
import asyncio
import tempfile
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

# TTS 설정
VOICE_NAME = "ko-KR-SunHiNeural"  # 필요 시 변경 가능

# PaddleOCR 초기화 (한국어)
ocr = PaddleOCR(
    use_textline_orientation=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    lang='korean'
)

# -----------------------------------------
# 스니핑 툴
# -----------------------------------------
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
        img.save(self.save_path)
        print(f"📸 Screenshot saved to {self.save_path}")
        run_pipeline(self.save_path)

# -----------------------------------------
# OCR + TTS 파이프라인
# -----------------------------------------

def run_pipeline(image_path):
    # OCR
    print("🧠 Running PaddleOCR...")
    raw = ocr.predict(image_path)
    texts = []
    if isinstance(raw, list) and raw:
        if isinstance(raw[0], dict):
            for page in raw:
                texts.extend(page.get('rec_texts', []))
        else:
            for line in raw:
                for item in line:
                    if isinstance(item, list) and len(item) == 2:
                        t = item[1]
                        if isinstance(t, tuple):
                            texts.append(t[0])
                        else:
                            texts.append(t)
                    elif isinstance(item, list) and len(item) >= 3:
                        texts.append(item[1])
    else:
        print("⚠️ Unexpected OCR format.")
    full_text = "\n".join(texts)
    # 파일로 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"✅ OCR text saved to {OUTPUT_FILE}")

    # TTS 생성 및 재생
    temp_audio = os.path.join(tempfile.gettempdir(), 'snip_tts.mp3')
    async def gen_tts():
        tts = edge_tts.Communicate(text=full_text, voice=VOICE_NAME)
        await tts.save(temp_audio)
    print("🔉 Generating TTS audio...")
    asyncio.run(gen_tts())
    print("▶️ Playing audio...")
    os.startfile(temp_audio)

# -----------------------------------------
# 진입점
# -----------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    tool = SnippingTool()
    sys.exit(app.exec_())
