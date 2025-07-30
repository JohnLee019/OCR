import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QGuiApplication
from PIL import ImageGrab
from paddleocr import PaddleOCR

# -----------------------------------------
# 설정
# -----------------------------------------
# 스크립트 디렉토리
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 캡처 이미지 경로
SNIP_PATH = os.path.join(BASE_DIR, 'snip.png')
# OCR 결과 저장 폴더 및 파일
OUTPUT_DIR = os.path.join(BASE_DIR, 'result')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'snip_ocr_result.txt')

# PaddleOCR 초기화 (한국어+영어 등 다국어 지원 가능)
ocr = PaddleOCR(
    use_textline_orientation=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    lang='korean'  # 필요 시 'en+kor' 등 변경
)

# -----------------------------------------
# 스니핑 툴
# -----------------------------------------
class SnippingTool(QWidget):
    def __init__(self):
        super().__init__()
        # 창 설정
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.5)
        self.setCursor(Qt.CrossCursor)

        # 화면 전체
        screen_rect = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_rect)
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
        # 선택 영역 계산
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        self.close()

        # 캡처 및 저장
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img.save(self.save_path)
        print(f"📸 Screenshot saved to {self.save_path}")

        # OCR 실행
        run_ocr(self.save_path)

# -----------------------------------------
# OCR 처리
# -----------------------------------------
def run_ocr(image_path):
    print("🧠 Running PaddleOCR...")
    if not os.path.exists(image_path):
        print(f"[❌ Error] File not found: {image_path}")
        return

    # OCR 수행
    raw = ocr.predict(image_path)

    # 텍스트 추출
    texts = []
    if isinstance(raw, list) and raw:
        # JSON-like 결과
        if isinstance(raw[0], dict):
            for page in raw:
                texts.extend(page.get('rec_texts', []))
        else:
            # nested list 형태
            for line in raw:
                for item in line:
                    # item: [box, (text,score)] or [box, text, score]
                    # 첫 번째 브랜치
                    if isinstance(item, list) and len(item) == 2:
                        t = item[1]
                        if isinstance(t, tuple):
                            texts.append(t[0])
                        else:
                            texts.append(t)
                    elif isinstance(item, list) and len(item) >= 3:
                        # [box, text, score]
                        texts.append(item[1])
    else:
        print("⚠️ Unexpected OCR result format.")

    # 파일 저장
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(texts))

    print(f"✅ OCR complete. Text saved to {OUTPUT_FILE}")
    print("📄 Recognized text:")
    for line in texts:
        print(line)

# -----------------------------------------
# 진입점
# -----------------------------------------
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SnippingTool()
    sys.exit(app.exec_())
