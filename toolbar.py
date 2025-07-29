import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFrame, QLabel
)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QIcon

IMAGE_DIR = "image"
FALLBACK = {
    "toggle": "≡", "close": "✕",
    "snip": "📷", "pause": "⏸", "play": "▶"
}

class ToolBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("국립중앙도서관 툴바")
        self.setGeometry(200, 200, 100, 50)
        self.setMinimumSize(100, 50)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        self.resize_margin = 8
        self.resizing = self.moving = False
        self.drag_position = None
        self.resize_direction = None
        self.is_expanded = False

        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # ── 1) 항상 보이는 상단바 (≡, ✕) ──
        top = QFrame()
        top.setFixedHeight(40)
        top.setStyleSheet("background-color:#004ea2;")
        h = QHBoxLayout()
        h.setContentsMargins(8, 5, 8, 5)

        # 토글 버튼 (축소/확장)
        self.toggle_btn = self._create_icon("toggle", 28)
        self.toggle_btn.clicked.connect(self.toggle_toolbar)
        # 닫기 버튼
        self.close_btn  = self._create_icon("close", 28)
        self.close_btn.clicked.connect(self.close)

        h.addWidget(self.toggle_btn)
        h.addStretch()
        h.addWidget(self.close_btn)
        top.setLayout(h)
        self.layout.addWidget(top)

        # ── 2) 확장 시에만 보이는 콘텐츠 ──
        # (레이아웃 + 아이콘 + 라벨)
        self.tool_containers = []
        tools = [
            ("캡처",   "snip"),
            ("일시정지","pause"),
            ("재시작", "play")
        ]
        for label_text, name in tools:
            btn = self._create_icon(name, 48)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size:14px; font-weight:bold;")
            row = QHBoxLayout(); row.setContentsMargins(10,2,10,2)
            row.addWidget(btn); row.addWidget(lbl); row.addStretch()
            container = QWidget()
            container.setLayout(row)
            container.setVisible(False)
            self.layout.addWidget(container)
            self.tool_containers.append(container)

        # collapsed 기본 배경
        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    def _create_icon(self, name, size):
        path = os.path.join(IMAGE_DIR, f"{name}.png")
        btn = QPushButton()
        if os.path.exists(path):
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(size-12, size-12))
        else:
            btn.setText(FALLBACK[name])
            btn.setStyleSheet("font-size:20px; color:#ffffff;" 
                              if name in ("toggle","close") 
                              else "font-size:20px; color:#004ea2;")
        btn.setFixedSize(size, size)
        btn.setStyleSheet(btn.styleSheet() + "border:none; background:transparent;")
        return btn

    def toggle_toolbar(self):
        self.is_expanded = not self.is_expanded
        # 콘텐츠 영역만 보이기/숨기기
        for c in self.tool_containers:
            c.setVisible(self.is_expanded)
        # 크기 조정
        if self.is_expanded:
            self.resize(160, 230)
            self.apply_expanded_style()
        else:
            self.resize(100, 50)
            self.apply_collapsed_style()

    def apply_expanded_style(self):
        for c in self.tool_containers:
            btn = c.layout().itemAt(0).widget()
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #004ea2;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e6f0fa;
                }
            """)
        # 배경 유지
        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    def apply_collapsed_style(self):
        # 콘텐츠 버튼 스타일만 리셋
        for c in self.tool_containers:
            btn = c.layout().itemAt(0).widget()
            btn.setStyleSheet("border:none; background:transparent;")
        self.setStyleSheet("QWidget{background:#f9f9f9;}")

    # ── 마우스 이벤트 (이동/리사이즈) ──
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_position = e.globalPos()
            d = self.get_resize_direction(e.pos())
            if any(d.values()):
                self.resizing = True; self.resize_direction = d
            else:
                w = self.childAt(e.pos())
                if w not in (self.toggle_btn, self.close_btn):
                    self.moving = True

    def mouseMoveEvent(self, e):
        if self.resizing:
            self.resize_window(e.globalPos())
        elif self.moving:
            delta = e.globalPos() - self.drag_position
            self.move(self.pos() + delta)
            self.drag_position = e.globalPos()
        else:
            self.setCursorByDirection(self.get_resize_direction(e.pos()))

    def mouseReleaseEvent(self, e):
        self.resizing = self.moving = False
        self.setCursor(Qt.ArrowCursor)

    def get_resize_direction(self, pos):
        m = self.resize_margin
        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        return {
            "left":   x < m,
            "right":  x > w - m,
            "top":    y < m,
            "bottom": y > h - m
        }

    def setCursorByDirection(self, d):
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

    def resize_window(self, gp):
        diff = gp - self.drag_position
        g, d = self.geometry(), self.resize_direction
        if d["left"]:
            nx, nw = g.x() + diff.x(), g.width() - diff.x()
            if nw >= self.minimumWidth(): g.setX(nx); g.setWidth(nw)
        if d["right"]:
            nw = g.width() + diff.x()
            if nw >= self.minimumWidth(): g.setWidth(nw)
        if d["top"]:
            ny, nh = g.y() + diff.y(), g.height() - diff.y()
            if nh >= self.minimumHeight(): g.setY(ny); g.setHeight(nh)
        if d["bottom"]:
            nh = g.height() + diff.y()
            if nh >= self.minimumHeight(): g.setHeight(nh)
        self.setGeometry(g)
        self.drag_position = gp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tb = ToolBar()
    tb.show()
    sys.exit(app.exec_())
