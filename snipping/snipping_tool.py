import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QPen, QGuiApplication
from PyQt5.QtCore import Qt, QRect
from PIL import ImageGrab

class SnippingTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowOpacity(0.5)  # Set to 0.5 so you can see it
        # self.setAttribute(Qt.WA_TranslucentBackground)  # Disable for now
        self.setCursor(Qt.CrossCursor)

        screen = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.begin = self.end = None
        self.showFullScreen()
        print("Snipping tool started. Drag to select.")

    def paintEvent(self, event):
        if self.begin and self.end:
            qp = QPainter(self)
            qp.setPen(QPen(Qt.red, 2))
            rect = QRect(self.begin, self.end)
            qp.drawRect(rect.normalized())

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        self.close()

        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img.save("snip.png")
        img.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SnippingTool()
    sys.exit(app.exec_())
