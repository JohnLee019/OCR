import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QIcon
from combined import SnippingTool  # Combined 모듈의 스니핑 기능 import

IMAGE_DIR = "image"
FALLBACK = {
    "toggle": "≡", "close": "✕",
    "snip": "📷", "pause": "⏸", "play": "▶"
}

class ToolBar(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("국립중앙도서관 오디오")
        self.setGeometry(200, 200, 100, 50)
        self.setFixedSize(117, 50)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.is_expanded = False
        self.dragging = False
        self.drag_start_position = QPoint()

        # 리사이즈 관련 상태
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
            # 스니핑 기능 연동
            if name == "snip":
                btn.clicked.connect(self.start_snipping)
            lbl = QLabel(label_text, self)
            lbl.setStyleSheet("font-size:14px; font-weight:bold;")
            row.addWidget(btn)
            row.addWidget(lbl)
            row.addStretch()
            row_widget.setVisible(False)
            self.layout.addWidget(row_widget)
            self.tool_containers.append(row_widget)

        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    def start_snipping(self):
        # Combined 모듈의 SnippingTool 실행
        self.snipper = SnippingTool()
        self.snipper.show()

    def _create_icon(self, name, size):
        path = os.path.join(IMAGE_DIR, f"{name}.png")
        btn = QPushButton(self)
        if os.path.exists(path):
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(size - 12, size - 12))
        else:
            btn.setText(FALLBACK.get(name, "?"))
            color = "#ffffff" if name in ("toggle", "close") else "#004ea2"
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
            self.setMaximumSize(300, 360)
            self.resize(235, 280)
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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos()
            self.resize_direction = self._get_resize_direction(event.pos())

            if self.is_expanded and any(self.resize_direction.values()):
                self.resizing = True
            elif self.top_bar.geometry().contains(event.pos()):
                self.dragging = True
                self.drag_offset = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.resizing:
            self._perform_resize(event.globalPos())
        elif self.dragging:
            self.move(event.globalPos() - self.drag_offset)
        elif self.is_expanded:
            self._update_cursor(event.pos())

    def mouseReleaseEvent(self, event):
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
    app = QApplication(sys.argv)
    tb = ToolBar()
    tb.show()
    sys.exit(app.exec_())
