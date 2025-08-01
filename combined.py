import sys
import os
import asyncio
import tempfile
import subprocess # --- subprocess 모듈 임포트 ---
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
    def __init__(self, callback_on_cancel=None, callback_on_snip_done=None):
        super().__init__()
        print("[SnippingTool] SnippingTool __init__ 호출됨")
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
        print(f"[SnippingTool] mouseReleaseEvent 발생. canceled: {self.canceled}")
        if self.canceled:
            print("[SnippingTool] 취소 상태이므로 스니핑 처리 건너뜀.")
            return
        
        x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
        x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
        self.close()
        
        if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            img.save(self.save_path)
            print(f"📸 Screenshot saved to {self.save_path}")
            if self.callback_on_snip_done:
                print("[SnippingTool] callback_on_snip_done 호출됨.")
                self.callback_on_snip_done(self.save_path)
        else:
            print("🚫 Selection too small or invalid. Snipping cancelled by user.")
            if self.callback_on_cancel:
                print("[SnippingTool] callback_on_cancel 호출됨 (유효하지 않은 선택).")
                self.callback_on_cancel()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            print("[SnippingTool] Escape 키 눌림.")
            print("🚫 Snipping cancelled by user (Escape key pressed).")
            self.canceled = True
            self.close()
            if self.callback_on_cancel:
                print("[SnippingTool] callback_on_cancel 호출됨 (Escape 키).")
                self.callback_on_cancel()

# -----------------------------------------
# OCR + TTS 파이프라인
# -----------------------------------------

def run_pipeline(image_path):
    print(f"[run_pipeline] 파이프라인 시작: {image_path}")
    try:
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
        print("[run_pipeline] TTS 오디오 파일 생성 완료.")
        print("▶️ Playing audio...")
        
        # --- os.startfile 대신 subprocess.Popen 사용 ---
        if sys.platform == "win32":
            # Windows에서 오디오 파일을 기본 프로그램으로 비동기 실행
            subprocess.Popen(['start', temp_audio], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "darwin":
            # macOS에서 'open' 명령어로 오디오 파일을 비동기 실행
            subprocess.Popen(['open', temp_audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux에서 'xdg-open' 또는 'aplay' 등으로 실행 (환경에 따라 다름)
            # 여기서는 'xdg-open'을 기본으로 사용합니다.
            subprocess.Popen(['xdg-open', temp_audio], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # --- subprocess.Popen 사용 끝 ---

        print("[run_pipeline] 오디오 재생 명령 완료 (비블로킹).") # 메시지 변경

    except Exception as e:
        print(f"[ERROR] run_pipeline 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[run_pipeline] 파이프라인 완료 (정상 또는 오류로 종료).")

# -----------------------------------------
# 진입점 (이 파일은 직접 실행되지 않고 모듈로 사용됩니다.)
# -----------------------------------------
if __name__ == '__main__':
    print("[combined.py] combined.py 파일이 직접 실행됨. (모듈로 사용 권장)")
    print("combined.py는 직접 실행되지 않고 모듈로 사용됩니다.")