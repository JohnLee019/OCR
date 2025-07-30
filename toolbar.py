import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

IMAGE_DIR = "image"
FALLBACK = {
    "toggle": "≡", "close": "✕",
    "snip": "📷", "pause": "⏸", "play": "▶"
}

class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        # 마지막 확대 크기 저장 (기본 확대 사이즈)
        self.last_expanded_size = (160, 230)

        # 기본 창 설정: 축소 상태
        self.setWindowTitle("국립중앙도서관 툴바")
        self.setGeometry(200, 200, 100, 50)
        self.setFixedSize(117, 50)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # 상태 관리
        self.resize_margin = 8
        self.resizing = False
        self.moving = False
        self.drag_position = None
        self.resize_direction = None
        self.is_expanded = False

        # UI 초기화
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 상단바: 토글, 제목, 닫기
        top = QFrame(self)
        top.setFixedHeight(40)
        top.setStyleSheet("background-color:#004ea2;")
        h = QHBoxLayout(top)
        h.setContentsMargins(8, 5, 8, 5)

        self.toggle_btn = self._create_icon("toggle", 28)
        self.toggle_btn.clicked.connect(self.toggle_toolbar)
        self.title_lbl = QLabel("툴바", self)
        self.title_lbl.setStyleSheet("color:#ffffff; font-size:14px; font-weight:bold;")
        self.close_btn = self._create_icon("close", 28)
        self.close_btn.clicked.connect(self.close)

        h.addWidget(self.toggle_btn)
        h.addWidget(self.title_lbl)
        h.addStretch()
        h.addWidget(self.close_btn)
        self.layout.addWidget(top)

        # 확장 시 보이는 도구 컨테이너
        self.tool_containers = []
        tools = [("캡처", "snip"), ("일시정지", "pause"), ("재시작", "play")]
        for label_text, name in tools:
            row_widget = QWidget(self)
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(10, 2, 10, 2)
            btn = self._create_icon(name, 48)
            lbl = QLabel(label_text, self)
            lbl.setStyleSheet("font-size:14px; font-weight:bold;")
            row.addWidget(btn)
            row.addWidget(lbl)
            row.addStretch()
            row_widget.setVisible(False)
            self.layout.addWidget(row_widget)
            self.tool_containers.append(row_widget)

        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    def _create_icon(self, name, size):
        path = os.path.join(IMAGE_DIR, f"{name}.png")
        btn = QPushButton(self)
        if os.path.exists(path):
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(size-12, size-12))
        else:
            btn.setText(FALLBACK.get(name, "?"))
            color = "#ffffff" if name in ("toggle","close") else "#004ea2"
            btn.setStyleSheet(f"font-size:20px; color:{color};")
        btn.setFixedSize(size, size)
        btn.setStyleSheet(btn.styleSheet() + "border:none; background:transparent;")
        return btn

    def toggle_toolbar(self):
        # 토글 상태 변경
        self.is_expanded = not self.is_expanded
        # 제목 변경
        self.title_lbl.setText("국립중앙도서관 툴바" if self.is_expanded else "툴바")
        # 도구 컨테이너 표시/숨김
        for c in self.tool_containers:
            c.setVisible(self.is_expanded)
        if self.is_expanded:
            # 확장 시: 크기 제한 해제, 최소/최대 크기 설정
            self.setMinimumSize(160, 230)
            self.setMaximumSize(300, 400)
            # 마지막 저장된 크기로 복원
            w, h = self.last_expanded_size
            self.resize(w, h)
        else:
            # 축소 시: 고정 크기
            self.setFixedSize(117, 50)
        # 스타일 업데이트
        if self.is_expanded:
            self.apply_expanded_style()
        else:
            self.apply_collapsed_style()

    def apply_expanded_style(self):
        for c in self.tool_containers:
            btn = c.layout().itemAt(0).widget()
            btn.setStyleSheet("""
                QPushButton { background-color:#ffffff; border:1px solid #004ea2; border-radius:4px; }
                QPushButton:hover { background-color:#e6f0fa; }
            """)

    def apply_collapsed_style(self):
        for c in self.tool_containers:
            btn = c.layout().itemAt(0).widget()
            btn.setStyleSheet("border:none; background:transparent;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_expanded:
            # 사용자가 직접 리사이즈하면 크기 저장
            self.last_expanded_size = (self.width(), self.height())

    # 마우스 이동/리사이즈 핸들링은 생략 (기존 로직 그대로)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tb = ToolBar()
    tb.show()
    sys.exit(app.exec_())
