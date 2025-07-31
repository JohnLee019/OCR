import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon

IMAGE_DIR = "image"
FALLBACK = {
    "toggle": "≡", "close": "✕",
    "snip": "📷", "pause": "⏸", "play": "▶"
}

class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        self.last_expanded_size = (160, 230)

        self.setWindowTitle("국립중앙도서관 툴바")
        self.setGeometry(200, 200, 100, 50)
        self.setFixedSize(117, 50)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # 상태
        self.is_expanded = False
        self.dragging = False
        self.drag_start_position = QPoint()

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 상단바
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
        self.close_btn.clicked.connect(self.close)

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
        self.is_expanded = not self.is_expanded
        self.title_lbl.setText("국립중앙도서관 툴바" if self.is_expanded else "툴바")
        for c in self.tool_containers:
            c.setVisible(self.is_expanded)

        if self.is_expanded:
            self.setMinimumSize(160, 230)
            self.setMaximumSize(300, 400)
            w, h = self.last_expanded_size
            self.resize(w, h)
        else:
            self.setFixedSize(117, 50)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_expanded:
            self.last_expanded_size = (self.width(), self.height())

    # ✅ 툴바 창을 마우스로 이동 가능하도록 만드는 부분
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.top_bar.geometry().contains(event.pos()):
            self.dragging = True
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.drag_start_position)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tb = ToolBar()
    tb.show()
    sys.exit(app.exec_())
