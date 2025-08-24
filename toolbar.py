import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel, QDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QSize, QPoint, QTimer
from PyQt5.QtGui import QIcon
from PIL import ImageGrab
import tempfile
import uuid
from combined import SnippingTool, run_pipeline, pause_audio, resume_audio, stop_audio, get_last_ocr_text, restart_audio, is_audio_busy, is_audio_finished, SNIP_PATH, OUTPUT_FILE, perform_mouse_click, get_current_audio_file


# 이미지 및 대체 텍스트 설정
IMAGE_DIR = "image"
FALLBACK = {
    "toggle": "≡", "close": "✕",
    "snip": "📷", "pause": "⏸", "play": "▶", "cancel": "✖", "restart": "🔁", "stop": "■",
    "continuous_read": "📚"
}


class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        print("[ToolBar] ToolBar __init__ 호출됨")

        self.setWindowTitle("국립중앙도서관 오디오")
        self.setGeometry(200, 200, 100, 50)
        self.setFixedSize(120, 50)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # 상태 변수 초기화
        self.is_expanded = False
        self.dragging = False
        self.drag_start_position = QPoint()
        self.snipping_active = False
        self.snipper = None
        self.audio_status = 'stopped'
        self.continuous_read_active = False
        self.is_setting_next_page_pos = False
        self.is_waiting_for_next_page = False

        self._overlay = None

        # 연속 읽기 기능 관련 속성
        self.reading_area = None
        self.next_page_click_pos = None

        # 오디오 버튼 변수 초기화
        self.pause_btn = None
        self.play_btn = None
        self.stop_btn = None
        self.restart_btn = None
        self.continuous_read_btn = None

        # 창 크기 조절 관련 변수
        self.resize_margin = 8
        self.resizing = False
        self.resize_direction = {}

        self.init_ui()
        
        # 오디오 상태를 주기적으로 확인하는 타이머 추가
        self.audio_timer = QTimer(self)
        self.audio_timer.timeout.connect(self._check_audio_status)
        self.audio_timer.start(250)

    def _show_processing(self, text="처리 중…"):
        if self._overlay is None:
            self._overlay = ProcessingOverlay(self, text=text)
        else:
            self._overlay.set_text(text)
        self._overlay.bar.setValue(0)
        self._overlay.popup_near(self)
        self._overlay.show()
        QApplication.processEvents()  # 동기 호출 직전 한 번 그려주기

    def _hide_processing(self):
        if self._overlay and self._overlay.isVisible():
            self._overlay.hide()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 상단 바 (토글, 제목, 닫기 버튼 포함)
        self.top_bar = QFrame(self)
        self.top_bar.setFixedHeight(50)
        self.top_bar.setStyleSheet("background-color:#004ea2;")
        h = QHBoxLayout(self.top_bar)
        h.setContentsMargins(8, 5, 8, 5)

        self.toggle_btn = self._create_icon("toggle", 28, 20)
        self.toggle_btn.clicked.connect(self.toggle_toolbar)
        self.title_lbl = QLabel("툴바", self)
        self.title_lbl.setStyleSheet("color:#ffffff; font-size:17px; font-weight:900;")
        self.close_btn = self._create_icon("close", 28, 20)
        self.close_btn.clicked.connect(self.close_application)

        h.addWidget(self.toggle_btn)
        h.addWidget(self.title_lbl)
        h.addStretch()
        h.addWidget(self.close_btn)
        self.layout.addWidget(self.top_bar)

        # 도구 버튼
        self.tool_containers = []
        tools = [
            ("캡처", "snip", 48, 36),
            ("일시정지", "pause", 48, 28),
            ("재생", "play", 48, 28),
            ("다시듣기", "restart", 48, 40),
            ("오디오 나가기", "stop", 48, 40)
        ]
        
        for label_text, name, btn_size, icon_size in tools:
            row_widget = QWidget(self)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(10, 2, 10, 2)
            btn = self._create_icon(name, btn_size, icon_size)

            if name == "snip":
                self.snip_btn = btn
                btn.clicked.connect(self.start_snipping)
            elif name == "pause":
                self.pause_btn = btn
                self.pause_btn.clicked.connect(self._on_pause_clicked)
            elif name == "play":
                self.play_btn = btn
                self.play_btn.clicked.connect(self._on_play_clicked)
            elif name == "restart":
                self.restart_btn = btn
                self.restart_btn.clicked.connect(self._on_restart_clicked)
            elif name == "stop":
                self.stop_btn = btn
                self.stop_btn.clicked.connect(self._on_stop_clicked)

            lbl = QLabel(label_text, self)
            lbl.setStyleSheet("font-size:16px; font-weight:900;")
            row.addWidget(btn)
            row.addWidget(lbl)
            row.addStretch()
            row_widget.setVisible(False)
            self.layout.addWidget(row_widget)
            self.tool_containers.append(row_widget)

        # '연속 읽기' 버튼 추가
        read_row_widget = QWidget(self)
        read_row = QHBoxLayout(read_row_widget)
        read_row.setContentsMargins(10, 2, 10, 2)
        self.continuous_read_btn = self._create_icon("continuous_read", 48, 36)
        self.continuous_read_btn.clicked.connect(self.start_continuous_reading)
        read_lbl = QLabel("연속 읽기", self)
        read_lbl.setStyleSheet("font-size:16px; font-weight:900;")
        read_row.addWidget(self.continuous_read_btn)
        read_row.addWidget(read_lbl)
        read_row.addStretch()
        read_row_widget.setVisible(False)
        self.layout.addWidget(read_row_widget)
        self.tool_containers.append(read_row_widget)
        
        self._update_audio_button_colors(self.audio_status)

        # 취소 버튼
        self.cancel_button_widget = QWidget(self)
        cancel_row = QHBoxLayout(self.cancel_button_widget)
        cancel_row.setContentsMargins(10, 2, 10, 2)
        self.cancel_btn = self._create_icon("cancel", 48, 36)
        self.cancel_btn.clicked.connect(self.cancel_snipping)
        cancel_lbl = QLabel("취소", self)
        cancel_lbl.setStyleSheet("font-size:16px; font-weight:900;")
        cancel_row.addWidget(self.cancel_btn)
        cancel_row.addWidget(cancel_lbl)
        cancel_row.addStretch()
        self.cancel_button_widget.setVisible(False)
        self.layout.addWidget(self.cancel_button_widget)

        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    def _check_audio_status(self):
        """오디오 상태가 변경되었는지 확인하고 UI를 업데이트합니다."""
        if self.audio_status == 'playing' and not is_audio_busy():
            print("[ToolBar] 오디오 재생이 자연스럽게 완료됨.")
            self.audio_status = 'finished'
            self._update_audio_button_colors(self.audio_status)
        
        if self.continuous_read_active and self.audio_status == 'finished' and not self.is_waiting_for_next_page:
            print("[Continuous Read] 오디오 재생 완료. 다음 페이지로 이동합니다.")
            self._update_audio_button_colors(self.audio_status)
            self._next_page_action()
        
    def _update_audio_button_colors(self, status):
        """버튼 색은 유지하면서 클릭 가능 여부만 조정"""
        pause_clickable = (status == 'playing' or (self.continuous_read_active and status == 'playing'))
        play_clickable = (status == 'paused' or (self.continuous_read_active and status == 'paused'))
        stop_clickable = (status in ['playing', 'paused', 'finished'] or self.continuous_read_active) 
        restart_clickable = (status in ['playing', 'paused', 'finished'] or self.continuous_read_active)
        snip_clickable = not self.snipping_active and not is_audio_busy() and not self.continuous_read_active
        continuous_read_clickable = not self.snipping_active and not is_audio_busy() and not self.continuous_read_active

        if self.pause_btn and self.play_btn and self.stop_btn and self.restart_btn and self.snip_btn and self.continuous_read_btn:
            base_style = """
                QPushButton {
                    background-color:#ffffff;
                    font-size:20px;
                }
                QPushButton:disabled {
                    color: #a0a0a0;
                    opacity: 0.5;
                }
            """
            
            self.snip_btn.setStyleSheet(base_style + "color: #000000;")
            self.snip_btn.setEnabled(snip_clickable)
            self.snip_btn.setCursor(Qt.PointingHandCursor if snip_clickable else Qt.ArrowCursor)
            
            self.pause_btn.setStyleSheet(base_style + "color: #dc3545;")
            self.pause_btn.setEnabled(pause_clickable)
            self.pause_btn.setCursor(Qt.PointingHandCursor if pause_clickable else Qt.ArrowCursor)

            self.play_btn.setStyleSheet(base_style + "color: #000000;")
            self.play_btn.setEnabled(play_clickable)
            self.play_btn.setCursor(Qt.PointingHandCursor if play_clickable else Qt.ArrowCursor)
            
            self.restart_btn.setStyleSheet(base_style + "color: #000000;")
            self.restart_btn.setEnabled(restart_clickable)
            self.restart_btn.setCursor(Qt.PointingHandCursor if restart_clickable else Qt.ArrowCursor)
            
            self.stop_btn.setStyleSheet(base_style + "color: #000000;")
            self.stop_btn.setEnabled(stop_clickable)
            self.stop_btn.setCursor(Qt.PointingHandCursor if stop_clickable else Qt.ArrowCursor)

            self.continuous_read_btn.setStyleSheet(base_style + "color: #000000;")
            self.continuous_read_btn.setEnabled(continuous_read_clickable)
            self.continuous_read_btn.setCursor(Qt.PointingHandCursor if continuous_read_clickable else Qt.ArrowCursor)

            print(f"✅ 오디오 상태 업데이트: 일시정지({pause_clickable}), 재생({play_clickable}), 다시듣기({restart_clickable}), 정지({stop_clickable}), 캡처({snip_clickable}), 연속읽기({continuous_read_clickable})")

    def _on_pause_clicked(self):
        if self.audio_status == 'playing':
            print("[ToolBar] 일시정지 버튼 클릭됨.")
            pause_audio()
            self.audio_status = 'paused'
            self._update_audio_button_colors(self.audio_status)
        else:
            print("[ToolBar] 오디오가 재생 중이 아니므로 일시정지 버튼 클릭 무시.")

    def _on_play_clicked(self):
        if self.audio_status == 'paused':
            print("[ToolBar] 재생 버튼 클릭됨.")
            resume_audio()
            self.audio_status = 'playing'
            self._update_audio_button_colors(self.audio_status)
        else:
            print("[ToolBar] 오디오가 일시정지 상태가 아니므로 재생 버튼 클릭 무시.")

    def _on_restart_clicked(self):
        if self.audio_status != 'stopped':
            print("[ToolBar] 다시듣기 버튼 클릭됨.")
            restart_audio()
            self.audio_status = 'playing'
            self._update_audio_button_colors(self.audio_status)
        else:
            print("[ToolBar] 오디오가 재생 또는 일시정지 상태가 아니므로 다시듣기 버튼 클릭 무시.")

    def _on_stop_clicked(self):
        print("[ToolBar] 정지 버튼 클릭됨.")
        if self.continuous_read_active:
            print("[ToolBar] 연속 읽기 모드 종료.")
            self.continuous_read_active = False
            self.is_waiting_for_next_page = False
            self.is_setting_next_page_pos = False
        
        stop_audio()
        self.audio_status = 'stopped'
        self._update_audio_button_colors(self.audio_status)
        
    def start_snipping(self):
        print("[ToolBar] start_snipping 호출됨. 툴바 숨김.")
        
        if self.continuous_read_active:
            print("[ToolBar] 연속 읽기 모드 중이므로 모드를 종료하고 캡처 시작.")
            stop_audio()
            self.continuous_read_active = False
            self.is_waiting_for_next_page = False
            self.is_setting_next_page_pos = False
            self.audio_status = 'stopped'
            self._update_audio_button_colors(self.audio_status)
        
        stop_audio()
        self.audio_status = 'stopped'

        self.snipping_active = True
        self.hide()
        self.snipper = SnippingTool(
            mode='normal',
            callback_on_cancel=self.on_snipping_cancelled,
            callback_on_snip_done=self.handle_snipped_image
        )
        self.snipper.show()
        self.show_cancel_button()
        self.audio_timer.stop()
        self._update_audio_button_colors(self.audio_status)

    def handle_snipped_image(self, image_path):
        print(f"[ToolBar] handle_snipped_image 콜백 호출됨: {image_path}")
        stop_audio()

        # ▶ 로딩 오버레이 표시
        self._show_processing("OCR/TTS 처리 중…")

        try:
            run_pipeline(image_path, progress_cb=self._overlay.update_progress)  # 기존 동기 호출 그대로 유지
        finally:
            # ▶ 처리 후 반드시 닫기
            self._hide_processing()

        self.snipping_active = False
        self.hide_cancel_button()
        self.show()
        self.is_expanded = False
        self.toggle_toolbar()
        self.audio_status = 'playing'
        self._update_audio_button_colors(self.audio_status)
        if self.snipper:
            print("[ToolBar] 스니퍼 인스턴스 정리.")
            self.snipper = None
        self.audio_timer.start(250)
        print("[ToolBar] handle_snipped_image 처리 완료.")


    def cancel_snipping(self):
        print("[ToolBar] cancel_snipping 호출됨 (취소 버튼 클릭).")
        if hasattr(self, 'snipper') and self.snipper and self.snipper.isVisible():
            print("[ToolBar] 활성 스니퍼를 취소합니다.")
            self.snipper.canceled = True
            self.snipper.close()
        self.on_snipping_cancelled()
        print("[ToolBar] cancel_snipping 처리 완료.")

    def close_application(self):
        print("[ToolBar] close_application 호출됨. 애플리케이션 종료 시작.")
        stop_audio()
        self.audio_status = 'stopped'
        self._update_audio_button_colors(self.audio_status)
        if hasattr(self, 'snipper') and self.snipper and self.snipper.isVisible():
            print("[ToolBar] 활성 스니퍼가 감지되어 먼저 취소합니다.")
            self.snipper.canceled = True
            self.snipper.close()

        try:
            if os.path.exists(SNIP_PATH):
                os.remove(SNIP_PATH)
            if os.path.exists(OUTPUT_FILE):
                os.remove(OUTPUT_FILE)
            print("[ToolBar] snip.png와 snip_ocr.txt 파일이 삭제되었습니다.")
        except Exception as e:
            print(f"[ERROR] 파일 삭제 중 오류 발생: {e}")

        self.audio_timer.stop()
        self.close()
        QApplication.instance().quit()
        print("[ToolBar] QApplication.quit() 호출됨. (이 메시지 이후 프로세스 종료 예상)")

    def on_snipping_cancelled(self):
        print("[ToolBar] on_snipping_cancelled 호출됨. 툴바 상태 복원 시작.")
        self.snipping_active = False
        self.continuous_read_active = False
        self.is_setting_next_page_pos = False
        self.hide_cancel_button()
        self.show()
        print("[ToolBar] 툴바 창 다시 표시 요청됨 (self.show()).")

        self.is_expanded = False
        self.toggle_toolbar()
        
        self.audio_status = 'stopped'
        self._update_audio_button_colors(self.audio_status)
        
        if self.snipper:
            print("[ToolBar] 스니퍼 인스턴스 정리.")
            self.snipper = None

        self.audio_timer.start(250)
        print("[ToolBar] on_snipping_cancelled 처리 완료.")

    def start_continuous_reading(self):
        """연속 읽기 모드 시작."""
        if self.continuous_read_active:
            self.continuous_read_active = False
            self.continuous_read_btn.setStyleSheet("background:transparent;")
            stop_audio()
            self.audio_status = 'stopped'
            self._update_audio_button_colors(self.audio_status)
            print("[ToolBar] 연속 읽기 모드 종료.")
            return

        print("[ToolBar] 연속 읽기 모드 시작. 읽기 영역 설정 시작.")
        stop_audio()
        self.audio_status = 'stopped'
        
        self.continuous_read_active = True
        self.is_setting_next_page_pos = False
        self.hide()
        self.snipper = SnippingTool(
            mode='read_area',
            callback_on_cancel=self.on_snipping_cancelled,
            callback_on_snip_done=self.handle_continuous_read_area,
            instruction_text="텍스트로 채워진 전자 도서의 범위를 지정해주세요."
        )
        self.snipper.show()
        self.show_cancel_button()

    def handle_continuous_read_area(self, area):
        """읽기 영역 설정 완료 후 호출."""
        if area:
            self.reading_area = area
            print("[ToolBar] 읽기 영역 설정 완료. 다음 페이지 버튼 위치 설정 시작.")
            self.snipper.close()
            self.hide()
            self.is_setting_next_page_pos = True
            self.snipper = SnippingTool(
                mode='click_pos',
                callback_on_cancel=self.on_snipping_cancelled,
                callback_on_snip_done=self.handle_next_page_pos,
                instruction_text="다음 페이지의 버튼 위를 클릭 해주세요."
            )
            self.snipper.show()
        else:
            self.on_snipping_cancelled()

    def handle_next_page_pos(self, pos):
        """다음 페이지 버튼 위치 설정 완료 후 호출."""
        if pos:
            self.next_page_click_pos = pos
            print("[ToolBar] 다음 페이지 버튼 위치 설정 완료. 첫 번째 읽기 시작.")
            self.is_setting_next_page_pos = False
            self.snipper.close()
            self.hide_cancel_button()
            self.show()

            self.is_expanded = False
            self.toggle_toolbar()

            self._start_reading_loop()
        else:
            self.on_snipping_cancelled()

    def _start_reading_loop(self):
        """읽기 루프 시작 (첫 실행 및 다음 페이지 루프 공통)"""
        if not self.continuous_read_active:
            return

        # 화면 캡처 준비
        self.hide()
        QApplication.processEvents()

        if not self.reading_area:
            print("[ERROR] 읽기 영역이 설정되지 않았습니다. 연속 읽기 중단.")
            self.continuous_read_active = False
            self.show()
            return

        # 영역 캡처
        img = ImageGrab.grab(bbox=self.reading_area)
        temp_path = os.path.join(tempfile.gettempdir(), f'snip_continuous_{uuid.uuid4().hex}.png')
        img.save(temp_path)

        # ✅ 로딩창을 먼저 띄우고 0%로 시작
        self._show_processing("OCR/TTS 처리 중…")

        try:
            # ✅ run_pipeline은 딱 한 번만 호출하고, 진행률 콜백 연결
            #    (이전 코드의 이중 호출/무콜백 호출 제거)
            self.audio_status = 'stopped'   # 아직 재생 전 상태로 유지
            run_pipeline(temp_path, progress_cb=self._overlay.update_progress)
        finally:
            self._hide_processing()

        # TTS 생성이 끝나면 play_audio가 내부에서 실행되므로 여기서 상태만 'playing'으로
        self.audio_status = 'playing'
        self.show()
        self._update_audio_button_colors(self.audio_status)
        self.audio_timer.start(250)
        self.is_waiting_for_next_page = False

    
    def _next_page_action(self):
        """다음 페이지로 넘어가는 액션을 수행합니다."""
        if self.continuous_read_active and not is_audio_busy():
            self.is_waiting_for_next_page = True
            perform_mouse_click(self.next_page_click_pos)
            QTimer.singleShot(2000, self._start_reading_loop)

    def show_cancel_button(self):
        print("[ToolBar] show_cancel_button 호출됨.")
        self.setFixedSize(120, 90)
        self.cancel_button_widget.setVisible(True)
        self.top_bar.setVisible(False)
        for c in self.tool_containers:
            c.setVisible(False)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        print("[ToolBar] 취소 버튼 표시 완료.")

    def hide_cancel_button(self):
        print("[ToolBar] hide_cancel_button 호출됨.")
        self.cancel_button_widget.setVisible(False)
        self.top_bar.setVisible(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        print("[ToolBar] 취소 버튼 숨김 완료.")

    def _create_icon(self, name, size, icon_size):
        path = os.path.join(IMAGE_DIR, f"{name}.png")
        btn = QPushButton(self)
        btn.setObjectName(name)
        if os.path.exists(path):
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(icon_size, icon_size))
        else:
            btn.setText(FALLBACK.get(name, "?"))
            color = "#ffffff" if name in ("toggle", "close") else "#004ea2"
            if name == "cancel":
                color = "#dc3545"
            btn.setStyleSheet(f"font-size:{icon_size}px; color:{color};")
        btn.setFixedSize(size, size)
        
        if name == "cancel":
            btn.setStyleSheet("""
                QPushButton {
                    background-color:#ffffff;
                    color: #dc3545;
                    font-size:20px;
                }
                QPushButton:hover {
                    background-color:#f8d7da;
                }
            """)
        else:
            btn.setStyleSheet(btn.styleSheet() + "background:transparent;")
        return btn

    def toggle_toolbar(self):
        print(f"[ToolBar] toggle_toolbar 호출됨. is_expanded: {self.is_expanded}, snipping_active: {self.snipping_active}")
        if self.snipping_active:
            print("[ToolBar] 스니핑 중이므로 툴바 토글 건너뜀.")
            return

        self.is_expanded = not self.is_expanded
        self.title_lbl.setText("국립중앙도서관 오디오" if self.is_expanded else "툴바")
        for c in self.tool_containers:
            c.setVisible(self.is_expanded)

        if self.is_expanded:
            self.setMinimumSize(250, 350)
            self.setMaximumSize(320, 500)
            self.resize(280, 400)
            print("[ToolBar] 툴바 확장됨.")
            self._update_audio_button_colors(self.audio_status)
        else:
            self.setFixedSize(120, 50)
            print("[ToolBar] 툴바 축소됨.")

        if self.is_expanded:
            self.apply_expanded_style()
        else:
            self.apply_collapsed_style()

    def apply_expanded_style(self):
        style = """
            QPushButton {
                background-color:#ffffff;
            }
            QPushButton:hover {
                background-color:#e6f0fa;
            }
        """
        self.findChild(QPushButton, "snip").setStyleSheet(style)

    def apply_collapsed_style(self):
        for c in self.tool_containers:
            btn = c.layout().itemAt(0).widget()
            btn_name = btn.objectName()
            if btn_name in ("snip", "pause", "play", "stop", "restart", "continuous_read"):
                btn.setStyleSheet("background:transparent;")
            
    def mousePressEvent(self, event):
        if self.snipping_active:
            return

        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos()
            self.resize_direction = self._get_resize_direction(event.pos())

            if self.is_expanded and any(self.resize_direction.values()):
                self.resizing = True
            elif self.top_bar.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.snipping_active:
            return

        if self.resizing:
            self._perform_resize(event.globalPos())
        elif self.dragging:
            # 창의 새 위치 계산
            new_pos = event.globalPos() - self.drag_offset

            # 화면 경계 가져오기
            screen_rect = QApplication.desktop().availableGeometry(self)
            
            # 새 위치가 화면 경계를 벗어나지 않도록 조정
            x = max(screen_rect.left(), new_pos.x())
            x = min(screen_rect.right() - self.width(), x)
            y = max(screen_rect.top(), new_pos.y())
            y = min(screen_rect.bottom() - self.height(), y)

            self.move(x, y)
        elif self.is_expanded:
            self._update_cursor(event.pos())

    def mouseReleaseEvent(self, event):
        if self.snipping_active:
            return
            
        self.resizing = False
        self.dragging = False
        self.setCursor(Qt.ArrowCursor)

    def _get_resize_direction(self, pos):
        m = self.resize_margin
        return {
            "left":   pos.x() < m,
            "right":  pos.x() > self.width() - m,
            "top":    pos.y() < m,
            "bottom": pos.y() > self.height() - m
        }

    def _update_cursor(self, pos):
        d = self._get_resize_direction(pos)
        if (d["left"] and d["top"]) or (d["right"] and d["bottom"]):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (d["right"] and d["top"]) or (d["left"] and d["bottom"]):
            self.setCursor(Qt.SizeBDiagCursor)
        elif d["left"] or d["right"]:
            self.setCursor(Qt.SizeHorCursor)
        elif d["top"] or d["bottom"]:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def _perform_resize(self, global_pos):
        diff = global_pos - self.drag_start_position
        g = self.geometry()

        if self.resize_direction.get("left"):
            new_x = g.x() + diff.x()
            new_w = g.width() - diff.x()
            if new_w >= self.minimumWidth():
                g.setX(new_x)
                g.setWidth(new_w)

        if self.resize_direction.get("right"):
            new_w = g.width() + diff.x()
            if new_w >= self.minimumWidth():
                g.setWidth(new_w)

        if self.resize_direction.get("top"):
            new_y = g.y() + diff.y()
            new_h = g.height() - diff.y()
            if new_h >= self.minimumHeight():
                g.setY(new_y)
                g.setHeight(new_h)

        if self.resize_direction.get("bottom"):
            new_h = g.height() + diff.y()
            if new_h >= self.minimumWidth():
                g.setHeight(new_h)

        self.setGeometry(g)
        self.drag_start_position = global_pos

class ProcessingOverlay(QDialog):
    def __init__(self, parent=None, text="처리 중…"):
        super().__init__(parent, flags=Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)
        self.setFixedSize(260, 110)

        cont = QWidget(self)
        cont.setStyleSheet("""
            QWidget{ background: rgba(0,0,0,0.65); border-radius: 12px; }
            QLabel{ color: #ffffff; font-size: 14px; }
            QProgressBar{ background:#222; border:1px solid #444; border-radius:6px;
                          text-align:center; color:#fff; }
            QProgressBar::chunk{ background:#4aa3ff; border-radius:6px; }
        """)
        v = QVBoxLayout(cont); v.setContentsMargins(16,16,16,16)
        self.msg = QLabel(text, cont)
        self.bar = QProgressBar(cont)
        # 동기 처리 중 애니메이션 대신 '바 모드'로 표시 (마퀴 효과)
        self.bar.setRange(0, 100)  # 0,0 => Busy indicator
        v.addWidget(self.msg); v.addWidget(self.bar)

        wrap = QVBoxLayout(self); wrap.setContentsMargins(0,0,0,0); wrap.addWidget(cont)

    def popup_near(self, anchor: QWidget):
        if not anchor:
            self.move(300, 300); return
        g = anchor.frameGeometry()
        x = g.right() + 12; y = g.top()
        screen_rect = QApplication.desktop().availableGeometry(anchor)
        if x + self.width() > screen_rect.right(): x = g.left() - self.width() - 12
        if y + self.height() > screen_rect.bottom(): y = screen_rect.bottom() - self.height() - 12
        self.move(x, y)

    def update_progress(self, value: int, msg: str = ""):
        self.bar.setValue(value)
        if msg:
            self.msg.setText(f"{value}% 완료 — {msg}")
        else:
            self.msg.setText(f"{value}% 완료")
        QApplication.processEvents()

    def set_text(self, text: str):
        if text: self.msg.setText(text)