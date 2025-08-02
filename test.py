import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon
from combined_copy import SnippingTool, run_pipeline, pause_audio, resume_audio, stop_audio

IMAGE_DIR = "image"
FALLBACK = {
    "toggle": "≡", "close": "✕",
    "snip": "📷", "pause": "⏸", "play": "▶", "cancel": "✖"
}
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'result')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'snip_ocr.txt')

class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        print("[ToolBar] ToolBar __init__ 호출됨")

        self.setWindowTitle("국립중앙도서관 오디오")
        self.setGeometry(200, 200, 100, 50)
        self.setFixedSize(117, 50)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.is_expanded = False
        self.dragging = False
        self.drag_start_position = QPoint()
        self.snipping_active = False
        self.snipper = None

        self.resize_margin = 8
        self.resizing = False
        self.resize_direction = {}

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.top_bar = QFrame(self)
        self.top_bar.setFixedHeight(40)
        self.top_bar.setStyleSheet("background-color:#004ea2;")
        h = QHBoxLayout(self.top_bar)
        h.setContentsMargins(8, 5, 8, 5)

        self.toggle_btn = self._create_icon("toggle", 28)
        self.toggle_btn.clicked.connect(self.toggle_toolbar)
        self.title_lbl = QLabel("툴바", self)
        self.title_lbl.setStyleSheet("color:#ffffff; font-size:14px; font-weight:bold;")
        self.close_btn = self._create_icon("close", 28)
        self.close_btn.clicked.connect(self.close_application)

        h.addWidget(self.toggle_btn)
        h.addWidget(self.title_lbl)
        h.addStretch()
        h.addWidget(self.close_btn)
        self.layout.addWidget(self.top_bar)

        self.tool_containers = []
        tools = [("캡처", "snip"), ("일시정지", "pause"), ("재시작", "play")]
        for label_text, name in tools:
            row_widget = QWidget(self)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(10, 2, 10, 2)
            btn = self._create_icon(name, 48)
            if name == "snip":
                btn.clicked.connect(self.start_snipping)
            elif name == "pause":
                btn.clicked.connect(pause_audio)
            elif name == "play":
                btn.clicked.connect(resume_audio)
            lbl = QLabel(label_text, self)
            lbl.setStyleSheet("font-size:14px; font-weight:bold;")
            row.addWidget(btn)
            row.addWidget(lbl)
            row.addStretch()
            row_widget.setVisible(False)
            self.layout.addWidget(row_widget)
            self.tool_containers.append(row_widget)

        self.cancel_button_widget = QWidget(self)
        cancel_row = QHBoxLayout(self.cancel_button_widget)
        cancel_row.setContentsMargins(10, 2, 10, 2)
        self.cancel_btn = self._create_icon("cancel", 48)
        self.cancel_btn.clicked.connect(self.cancel_snipping)
        cancel_lbl = QLabel("취소", self)
        cancel_lbl.setStyleSheet("font-size:14px; font-weight:bold;")
        cancel_row.addWidget(self.cancel_btn)
        cancel_row.addWidget(cancel_lbl)
        cancel_row.addStretch()
        self.cancel_button_widget.setVisible(False)
        self.layout.addWidget(self.cancel_button_widget)
        
        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    def close_application(self):
        print("[ToolBar] close_application 호출됨. 애플리케이션 종료 시작.")
        stop_audio()
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
        self.on_snipping_cancelled()
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
        if self.snipper:
            print("[ToolBar] 스니퍼 인스턴스 정리.")
            self.snipper = None
        print("[ToolBar] on_snipping_cancelled 처리 완료.")

    def show_cancel_button(self):
        print("[ToolBar] show_cancel_button 호출됨.")
        self.setFixedSize(117, 90)
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


    def _create_icon(self, name, size):
        path = os.path.join(IMAGE_DIR, f"{name}.png")
        btn = QPushButton(self)
        if os.path.exists(path):
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(size - 12, size - 12))
        else:
            btn.setText(FALLBACK.get(name, "?"))
            color = "#ffffff" if name in ("toggle", "close") else "#004ea2"
            if name == "cancel":
                color = "#dc3545"
            btn.setStyleSheet(f"font-size:20px; color:{color};")
        btn.setFixedSize(size, size)
        btn.setStyleSheet(btn.styleSheet() + "border:none; background:transparent;")
        
        if name == "cancel":
            btn.setStyleSheet("""
                QPushButton {
                    background-color:#ffffff;
                    border:1px solid #dc3545;
                    border-radius:4px;
                    color: #dc3545;
                    font-size:20px;
                }
                QPushButton:hover {
                    background-color:#f8d7da;
                }
            """)
        return btn

    def toggle_toolbar(self):
        print(f"[ToolBar] toggle_toolbar 호출됨. is_expanded: {self.is_expanded}, snipping_active: {self.snipping_active}")
        if self.snipping_active:
            print("[ToolBar] 스니핑 중이므로 툴바 토글 건너뜀.")
            return

        self.is_expanded = not self.is_expanded
        self.title_lbl.setText("국립중앙도서관 툴바" if self.is_expanded else "툴바")
        for c in self.tool_containers:
            c.setVisible(self.is_expanded)

        if self.is_expanded:
            self.setMinimumSize(160, 230)
            self.setMaximumSize(300, 360)
            self.resize(235, 280)
            print("[ToolBar] 툴바 확장됨.")
        else:
            self.setFixedSize(117, 50)
            print("[ToolBar] 툴바 축소됨.")

        if self.is_expanded:
            self.apply_expanded_style()
        else:
            self.apply_collapsed_style()

    def apply_expanded_style(self):
        for c in self.tool_containers:
            btn = c.layout().itemAt(0).widget()
            btn.setStyleSheet("""
                QPushButton {
                    background-color:#ffffff;
                    border:1px solid #004ea2;
                    border-radius:4px;
                }
                QPushButton:hover {
                    background-color:#e6f0fa;
                }
            """)

    def apply_collapsed_style(self):
        for c in self.tool_containers:
            btn = c.layout().itemAt(0).widget()
            btn.setStyleSheet("border:none; background:transparent;")

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
            if new_h >= self.minimumHeight():
                g.setHeight(new_h)

        self.setGeometry(g)
        self.drag_start_position = global_pos

if __name__ == "__main__":
    print("[toolbar.py] toolbar.py 직접 실행됨. QApplication 시작.")
    app = QApplication(sys.argv)
    tb = ToolBar()
    tb.show()
    print("[toolbar.py] ToolBar.show() 호출 완료. 이벤트 루프 진입 전.")
    sys.exit(app.exec_())
    print("[toolbar.py] QApplication.exec_() 종료됨. (이 메시지는 도달하기 어려울 수 있음)")