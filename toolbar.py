import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon
from combined import SnippingTool, run_pipeline, pause_audio, resume_audio, stop_audio, get_last_ocr_text

# 이미지 및 대체 텍스트 설정
IMAGE_DIR = "image"
FALLBACK = {
    "toggle": "≡", "close": "✕",
    "snip": "📷", "pause": "⏸", "play": "▶", "cancel": "✖", "stop": "■"
}
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'result')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'snip_ocr.txt')

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

        # 오디오 버튼 변수 초기화
        self.pause_btn = None
        self.play_btn = None
        self.stop_btn = None

        # 창 크기 조절 관련 변수
        self.resize_margin = 8
        self.resizing = False
        self.resize_direction = {}

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 상단 바 (토글, 제목, 닫기 버튼 포함)
        self.top_bar = QFrame(self)
        self.top_bar.setFixedHeight(40)
        # 상단 바의 스타일에서 하단 테두리를 제거합니다.
        self.top_bar.setStyleSheet("background-color:#004ea2;")
        h = QHBoxLayout(self.top_bar)
        h.setContentsMargins(8, 5, 8, 5)

        self.toggle_btn = self._create_icon("toggle", 28, 20)
        self.toggle_btn.clicked.connect(self.toggle_toolbar)
        self.title_lbl = QLabel("툴바", self)
        self.title_lbl.setStyleSheet("color:#ffffff; font-size:15px; font-weight:900;")
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
            ("오디오 나가기", "stop", 48, 40)
        ]
        
        for label_text, name, btn_size, icon_size in tools:
            row_widget = QWidget(self)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(10, 2, 10, 2)
            btn = self._create_icon(name, btn_size, icon_size)

            if name == "snip":
                btn.clicked.connect(self.start_snipping)
            elif name == "pause":
                self.pause_btn = btn
                self.pause_btn.clicked.connect(self._on_pause_clicked)
            elif name == "play":
                self.play_btn = btn
                self.play_btn.clicked.connect(self._on_play_clicked)
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

        # 툴바 전체 위젯에 테두리 스타일을 적용합니다.
        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    def _update_audio_button_colors(self, status):
        """버튼 색은 유지하면서 클릭 가능 여부만 조정"""
        pause_clickable = (status == 'playing')
        play_clickable = (status == 'paused')
        stop_clickable = (status != 'stopped')

        if self.pause_btn and self.play_btn and self.stop_btn:
            base_style = """
                QPushButton {
                    background-color:#ffffff;
                    font-size:20px;
                }
                QPushButton:disabled {
                    color: #a0a0a0;
                }
            """
            
            # 일시정지 버튼 (빨강)
            self.pause_btn.setStyleSheet(base_style + "color: #dc3545;")
            self.pause_btn.setEnabled(pause_clickable)
            self.pause_btn.setCursor(Qt.PointingHandCursor if pause_clickable else Qt.ArrowCursor)

            # 재생 버튼 (검정)
            self.play_btn.setStyleSheet(base_style + "color: #000000;")
            self.play_btn.setEnabled(play_clickable)
            self.play_btn.setCursor(Qt.PointingHandCursor if play_clickable else Qt.ArrowCursor)
            
            # 정지 버튼 (검정)
            self.stop_btn.setStyleSheet(base_style + "color: #000000;")
            self.stop_btn.setEnabled(stop_clickable)
            self.stop_btn.setCursor(Qt.PointingHandCursor if stop_clickable else Qt.ArrowCursor)

            print(f"✅ 오디오 상태 업데이트: 일시정지({pause_clickable}), 재생({play_clickable}), 정지({stop_clickable})")

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

    def _on_stop_clicked(self):
        """오디오를 완전히 정지하고 상태를 업데이트합니다."""
        if self.audio_status != 'stopped':
            print("[ToolBar] 정지 버튼 클릭됨.")
            stop_audio()
            self.audio_status = 'stopped'
            self._update_audio_button_colors(self.audio_status)
        else:
            print("[ToolBar] 오디오가 이미 정지 상태이므로 정지 버튼 클릭 무시.")
            
    def close_application(self):
        print("[ToolBar] close_application 호출됨. 애플리케이션 종료 시작.")
        stop_audio()
        self.audio_status = 'stopped'
        self._update_audio_button_colors(self.audio_status)
        if hasattr(self, 'snipper') and self.snipper and self.snipper.isVisible():
            print("[ToolBar] 활성 스니퍼가 감지되어 먼저 취소합니다.")
            self.snipper.canceled = True
            self.snipper.close()
        self.close()
        QApplication.instance().quit()
        print("[ToolBar] QApplication.quit() 호출됨. (이 메시지 이후 프로세스 종료 예상)")

    def start_snipping(self):
        print("[ToolBar] start_snipping 호출됨. 툴바 숨김.")
        self.snipping_active = True
        self.hide()
        self.snipper = SnippingTool(
            callback_on_cancel=self.on_snipping_cancelled,
            callback_on_snip_done=self.handle_snipped_image
        )
        self.snipper.show()
        self.show_cancel_button()

    def handle_snipped_image(self, image_path):
        print(f"[ToolBar] handle_snipped_image 콜백 호출됨: {image_path}")
        stop_audio()
        run_pipeline(image_path)
        
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
            
        print("[ToolBar] handle_snipped_image 처리 완료.")

    def cancel_snipping(self):
        print("[ToolBar] cancel_snipping 호출됨 (취소 버튼 클릭).")
        if hasattr(self, 'snipper') and self.snipper and self.snipper.isVisible():
            print("[ToolBar] 활성 스니퍼를 취소합니다.")
            self.snipper.canceled = True
            self.snipper.close()
        self.on_snipping_cancelled()
        print("[ToolBar] cancel_snipping 처리 완료.")

    def on_snipping_cancelled(self):
        print("[ToolBar] on_snipping_cancelled 호출됨. 툴바 상태 복원 시작.")
        self.snipping_active = False
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
        print("[ToolBar] on_snipping_cancelled 처리 완료.")

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
            self.setMinimumSize(160, 230)
            self.setMaximumSize(300, 360)
            self.resize(250, 280)
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
            if btn_name in ("snip", "pause", "play", "stop"):
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
            self.move(event.globalPos() - self.drag_offset)
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