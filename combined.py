import sys
import os
import asyncio
import tempfile
import uuid
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtGui import QPainter, QPen, QGuiApplication, QFont, QColor
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QObject, QPoint
import time
from PIL import ImageGrab
import pyautogui

#-----------------------------------------
# 설정
#-----------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNIP_PATH = os.path.join(BASE_DIR, 'result/snip.png')
OUTPUT_DIR = os.path.join(BASE_DIR, 'result')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'snip_ocr.txt')

# TTS 설정
# 한국어 TTS 음성 이름
KO_VOICE_NAME = "ko-KR-SunHiNeural"
# 영어 TTS 음성 이름 (원하는 다른 음성으로 변경 가능)
EN_VOICE_NAME = "en-US-JennyNeural"

# 글로벌 변수 선언 (초기화는 initialize_components 함수에서 진행)
ocr = None
_pygame = None
_edge_tts = None
_asyncio = None
_tts_file_path = None
_last_ocr_text = ""

#-----------------------------------------
# 초기화 함수
#-----------------------------------------
def initialize_components(progress_callback):
    """
    애플리케이션의 무거운 초기화 작업을 수행하는 함수.
    이 함수는 별도의 스레드에서 실행되어야 UI가 멈추지 않습니다.
    """
    global ocr, _pygame, _edge_tts, _asyncio
    
    total_steps = 100 # 총 단계를 100개로 늘려 더 세분화
    
    print("[INIT] 초기화 작업 시작...")
    
    # 1. Pygame 초기화 (0-10%)
    progress_callback.emit(0, "Pygame Mixer 초기화 중...")
    try:
        import pygame
        _pygame = pygame
        _pygame.mixer.init()
        print("✅ Pygame Mixer 초기화 완료.")
    except Exception as e:
        print(f"[ERROR] pygame 초기화 실패: {e}")
    progress_callback.emit(10, "Pygame Mixer 초기화 완료")

    # 2. PaddleOCR 모델 로딩 (10-80%)
    progress_callback.emit(15, "OCR 모델 로딩 준비 중...")
    try:
        # 이 부분이 가장 오래 걸리므로, 로딩처럼 보이도록 여러 단계로 나눕니다.
        # 실제 로딩은 단일 함수 호출이지만, 프로그레스바를 부드럽게 만들기 위한 시뮬레이션입니다.
        for i in range(15, 80, 5):
            progress_callback.emit(i, f"OCR 모델 로딩 중... ({i}%)")
            time.sleep(0.1)
        
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(
            use_textline_orientation=False,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            lang='korean'
        )
        print("✅ PaddleOCR 초기화 완료.")
    except Exception as e:
        print(f"[ERROR] PaddleOCR 초기화 실패: {e}")
    progress_callback.emit(80, "PaddleOCR 모델 로딩 완료")

    # 3. edge_tts 초기화 (80-90%)
    progress_callback.emit(85, "TTS 엔진 초기화 중...")
    try:
        import edge_tts
        _edge_tts = edge_tts
    except Exception as e:
        print(f"[ERROR] edge_tts 초기화 실패: {e}")
    progress_callback.emit(90, "TTS 엔진 초기화 완료")

    # 4. asyncio 초기화 (90-100%)
    progress_callback.emit(95, "비동기 모듈 로딩 중...")
    try:
        import asyncio
        _asyncio = asyncio
    except Exception as e:
        print(f"[ERROR] asyncio 초기화 실패: {e}")
    progress_callback.emit(100, "모든 초기화 작업 완료.") # 마지막은 항상 100%로

    print("[INIT] 모든 초기화 작업 완료.")

#-----------------------------------------
# 오디오 제어 함수
#-----------------------------------------
def play_audio(file_path):
    global _tts_file_path, _pygame
    if _pygame is None:
        print("[ERROR] Pygame이 초기화되지 않았습니다.")
        return
    try:
        _pygame.mixer.music.load(file_path)
        _pygame.mixer.music.play()
        _tts_file_path = file_path
        print("▶️ 오디오 재생 시작")
    except _pygame.error as e:
        print(f"[ERROR] 오디오 파일 재생 중 오류 발생: {e}")

def pause_audio():
    global _pygame
    if _pygame is None: return
    if _pygame.mixer.music.get_busy():
        _pygame.mixer.music.pause()
        print("⏸ 오디오 일시정지")

def resume_audio():
    global _pygame
    if _pygame is None: return
    # 오디오가 일시정지 상태일 때만 unpause() 호출
    # pygame.mixer.music.get_busy()는 일시정지 시 False가 되므로, 
    # 오디오가 로드되어 있지만 재생 중이 아닐 때를 확인해야 함
    if _pygame.mixer.music.get_busy() == 0 and _tts_file_path:
        _pygame.mixer.music.unpause()
        print("▶ 오디오 재생 재개")

def restart_audio():
    """현재 오디오를 처음부터 다시 재생합니다."""
    global _pygame, _tts_file_path
    if _pygame is None:
        print("[ERROR] Pygame이 초기화되지 않았습니다.")
        return
    if _tts_file_path:
        print("🔁 오디오 다시듣기")
        play_audio(_tts_file_path)
    else:
        print("[combined] 오디오가 로드되지 않아 다시듣기를 실행할 수 없습니다.")
        
def stop_audio():
    global _tts_file_path, _pygame
    if _pygame is None: return
    if _pygame.mixer.music.get_busy():
        _pygame.mixer.music.stop()
        print("⏹ 오디오 정지")
        _tts_file_path = None

def is_audio_busy():
    global _pygame
    if _pygame is None:
        return False
    return _pygame.mixer.music.get_busy()

def is_audio_finished():
    global _pygame
    if _pygame is None:
        return True
    return not _pygame.mixer.music.get_busy() and _tts_file_path is not None
    
def get_current_audio_file():
    return _tts_file_path

def perform_mouse_click(click_pos):
    """
    저장된 위치에 마우스 클릭을 수행합니다.
    click_pos: QPoint 객체
    """
    if click_pos:
        pyautogui.click(click_pos.x(), click_pos.y())
        print(f"[Automation] 마우스 클릭: {click_pos.x()}, {click_pos.y()}")
    else:
        print("[Automation] 클릭 위치가 설정되지 않았습니다.")

#-----------------------------------------
# 스니핑 툴
#-----------------------------------------
class SnippingTool(QWidget):
    def __init__(self, mode='read_area', callback_on_cancel=None, callback_on_snip_done=None, instruction_text=""):
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
        self.mode = mode
        self.instruction_text = instruction_text
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # 안내 텍스트 그리기
        if self.instruction_text:
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("나눔고딕", 20, QFont.Bold))
            text_rect = QRect(0, 0, self.width(), self.height())
            painter.drawText(text_rect, Qt.AlignCenter, self.instruction_text)

        if self.begin and self.end:
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            if self.mode in ('read_area', 'normal'):
                rect = QRect(self.begin, self.end).normalized()
                painter.drawRect(rect)
            elif self.mode == 'click_pos':
                painter.drawEllipse(self.begin, 5, 5)

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
        
        self.close()

        if self.mode == 'read_area':
            x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
            x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
            if abs(x2 - x1) > 5 and abs(y2 - y1) > 5:
                if self.callback_on_snip_done:
                    self.callback_on_snip_done((x1, y1, x2, y2))
            else:
                if self.callback_on_cancel:
                    self.callback_on_cancel()
        elif self.mode == 'click_pos':
            if self.callback_on_snip_done:
                self.callback_on_snip_done(self.begin)
        else: # 기본 캡처 모드
            x1, y1 = min(self.begin.x(), self.end.x()), min(self.begin.y(), self.end.y())
            x2, y2 = max(self.begin.x(), self.end.x()), max(self.begin.y(), self.end.y())
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

#-----------------------------------------
# OCR + TTS 실행
#-----------------------------------------
def run_pipeline(image_path):
    global _last_ocr_text, ocr, _edge_tts, _asyncio, KO_VOICE_NAME, EN_VOICE_NAME
    if ocr is None or _edge_tts is None or _asyncio is None:
        print("[ERROR] 필수 컴포넌트(OCR, TTS)가 초기화되지 않았습니다.")
        return
    
    print(f"[run_pipeline] 파이프라인 시작: {image_path}")
    
    try:
        # OCR
        print("🧠 Running PaddleOCR...")
        raw = ocr.ocr(image_path)
        
        texts = []
        if isinstance(raw, list) and raw and isinstance(raw[0], dict) and 'rec_texts' in raw[0]:
            texts = raw[0]['rec_texts']
        elif isinstance(raw, list) and raw and isinstance(raw[0], list):
             for line in raw:
                for item in line:
                    if isinstance(item, list) and len(item) >= 2:
                        text_data = item[1]
                        if isinstance(text_data, tuple):
                            texts.append(text_data[0])
                        else:
                            texts.append(text_data)
        
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
        _last_ocr_text = full_text

        # 텍스트에 한국어 문자가 포함되어 있는지 확인
        has_korean = any('\uac00' <= char <= '\ud7a3' for char in full_text)

        # 한국어 문자가 있으면 한국어 TTS, 없으면 영어 TTS 선택
        voice_name = KO_VOICE_NAME if has_korean else EN_VOICE_NAME
        print(f"🎤 선택된 TTS 음성: {voice_name}")

        if _pygame is not None and _pygame.mixer.music.get_busy():
            _pygame.mixer.music.stop()
            time.sleep(0.1)

        temp_audio = os.path.join(tempfile.gettempdir(), f'snip_tts_{uuid.uuid4().hex}.mp3')

        async def gen_tts():
            tts = _edge_tts.Communicate(text=full_text, voice=voice_name)
            await tts.save(temp_audio)

        _asyncio.run(gen_tts())
        print("🔉 TTS 오디오 생성 완료")

        play_audio(temp_audio)

    except Exception as e:
        print(f"[ERROR] run_pipeline 오류: {e}")

def get_last_ocr_text():
    global _last_ocr_text
    return _last_ocr_text