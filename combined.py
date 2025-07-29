import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QGuiApplication
from PIL import ImageGrab
import cv2
import pytesseract

# (Windows 전용) Tesseract 설치 경로 설정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class SnippingTool(QWidget):
    def __init__(self):
        super().__init__()
        # 창 세팅: 가장 위, 테두리 없음, 반투명
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.5)
        self.setCursor(Qt.CrossCursor)

        # 화면 전체 크기로 창 띄우기
        screen_rect = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_rect)
        self.begin = self.end = None
        self.save_path = "snip.png"
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
        # 선택 영역 좌표 계산
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        self.close()

        # 화면 캡처 및 파일 저장
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img.save(self.save_path)
        print(f"📸 Screenshot saved to {self.save_path}")

        # OCR 처리
        run_ocr(self.save_path)

def run_ocr(image_path):
    print("🧠 Running OCR (영어+한국어)...")
    if not os.path.exists(image_path):
        print(f"[❌ Error] File not found: {image_path}")
        return

    # OpenCV로 이미지 읽기
    image = cv2.imread(image_path)
    if image is None:
        print(f"[❌ Error] Failed to load image: {image_path}")
        return

    # 그레이스케일 + 이진화 처리 (OCR 정확도 향상)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Tesseract OCR (영어+한국어)
    # kor.traineddata가 tessdata 폴더에 있어야 합니다.
    text = pytesseract.image_to_string(binary, lang='eng+kor')
    if not text.strip():
        print("[⚠️ Warning] OCR returned empty text. Saving anyway.")

    # 결과 디렉토리 확보
    output_dir = "result"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "snipping_ocr_result.txt")

    # 텍스트 파일로 저장
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"✅ OCR complete. Text saved to {output_path}")
    print("📄 Recognized text:")
    print(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = SnippingTool()
    sys.exit(app.exec_())
