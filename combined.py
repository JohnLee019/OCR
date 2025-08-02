import sys
import os
import asyncio
import tempfile
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QGuiApplication
from PyQt5.QtCore import Qt, QRect
from PIL import ImageGrab
from paddleocr import PaddleOCR
import edge_tts
import pygame

# -----------------------------------------
# 설정
# -----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNIP_PATH = os.path.join(BASE_DIR, 'result/snip.png')
OUTPUT_DIR = os.path.join(BASE_DIR, 'result')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'snip_ocr.txt')

# TTS 설정
VOICE_NAME = "ko-KR-SunHiNeural"

# PaddleOCR 초기화 (기울어진 글자 인식 활성화)
ocr = PaddleOCR(
    use_textline_orientation=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    lang='korean'
)

# pygame mixer 초기화
pygame.mixer.init()

# -----------------------------------------
# 오디오 제어 함수
# -----------------------------------------
def play_audio(file_path):
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        print("▶️ 오디오 재생 시작")
    except pygame.error as e:
        print(f"[ERROR] pygame 오디오 재생 중 오류 발생: {e}")

def pause_audio():
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        print("⏸ 오디오 일시정지")

def resume_audio():
    pygame.mixer.music.unpause()
    print("▶ 오디오 재시작")

def stop_audio():
    pygame.mixer.music.stop()
    print("⏹ 오디오 정지")

# -----------------------------------------
# 스니핑 툴
# -----------------------------------------
class SnippingTool(QWidget):
    def __init__(self, callback_on_cancel=None, callback_on_snip_done=None):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.5)
        self.setCursor(Qt.CrossCursor)
        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.begin = self.end = None
        self.save_path = SNIP_PATH
        self.showFullScreen()
        self.canceled = False
        self.callback_on_cancel = callback_on_cancel
        self.callback_on_snip_done = callback_on_snip_done

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
        if self.canceled:
            return
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        self.close()
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img.save(self.save_path)
            if self.callback_on_snip_done:
                self.callback_on_snip_done(self.save_path)
        else:
            if self.callback_on_cancel:
                self.callback_on_cancel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.canceled = True
            self.close()
            if self.callback_on_cancel:
                self.callback_on_cancel()

# -----------------------------------------
# OCR + TTS 실행
# -----------------------------------------
import time
import uuid

def run_pipeline(image_path):
    print(f"[run_pipeline] 파이프라인 시작: {image_path}")
    try:
        # OCR
        print("🧠 Running PaddleOCR...")
        # ✅ ocr.ocr() 대신 ocr.predict() 사용
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
        full_text = "\n".join(texts)
        print(f"📄 OCR로 인식된 텍스트:\n{full_text}")
        
        if not full_text.strip():
            print("🚫 인식된 텍스트가 없습니다. 오디오를 생성하지 않습니다.")
            return

        # 파일로 저장
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(full_text)
        print(f"✅ OCR text saved to {OUTPUT_FILE}")

        # 재생 중이면 먼저 중지
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            time.sleep(0.1)

        # 매번 고유한 파일 이름 생성
        temp_audio = os.path.join(tempfile.gettempdir(), f'snip_tts_{uuid.uuid4().hex}.mp3')

        async def gen_tts():
            tts = edge_tts.Communicate(text=full_text, voice=VOICE_NAME)
            await tts.save(temp_audio)

        asyncio.run(gen_tts())
        print("🔉 TTS 오디오 생성 완료")

        play_audio(temp_audio)

    except Exception as e:
        print(f"[ERROR] run_pipeline 오류: {e}")

if __name__ == '__main__':
    print("[combined.py] combined.py 파일이 직접 실행됨. (모듈로 사용 권장)")
    print("combined.py는 직접 실행되지 않고 모듈로 사용됩니다.")