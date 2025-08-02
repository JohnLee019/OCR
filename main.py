import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QDesktopWidget, QProgressBar
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from toolbar import ToolBar
from combined import initialize_components

#------------------------------------------
# 로딩 스크린 클래스
#------------------------------------------
class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid #004ea2;
                border-radius: 10px;
            }
            QLabel {
                color: #004ea2;
            }
            QProgressBar {
                border: 2px solid #004ea2;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        self.setFixedSize(300, 150)
        self.center()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # 로딩 메시지 라벨 (고정)
        self.status_label = QLabel("로딩 중입니다", self)
        loading_font = QFont("Helvetica", 18)
        self.status_label.setFont(loading_font)
        self.status_label.setAlignment(Qt.AlignCenter)

        # 프로그레스 바
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def update_progress(self, value, message):
        """진행률을 업데이트하는 슬롯 함수"""
        # 메시지는 무시하고 진행률만 업데이트합니다.
        self.progress_bar.setValue(value)

#------------------------------------------
# 초기화 작업을 위한 워커 스레드
#------------------------------------------
class Worker(QObject):
    finished = pyqtSignal()
    progress_updated = pyqtSignal(int, str) # 진행률(int)과 메시지(str)를 전달하는 시그널

    def run(self):
        """무거운 초기화 함수를 실행하고 완료 시그널을 보냅니다."""
        initialize_components(self.progress_updated)
        self.finished.emit()

#------------------------------------------
# 메인 애플리케이션
#------------------------------------------
# 전역 변수로 toolbar 인스턴스를 유지하여 가비지 컬렉션을 방지합니다.
global_toolbar = None

def show_toolbar_and_cleanup(loading_screen):
    """초기화가 완료되면 호출되어 로딩 스크린을 닫고 툴바를 표시합니다."""
    global global_toolbar
    print("[main.py] 초기화 완료, 툴바 표시 시작.")
    loading_screen.close()
    
    global_toolbar = ToolBar()
    global_toolbar.show()
    
    print("[main.py] 툴바 표시 완료.")

if __name__ == "__main__":
    print("[main.py] 애플리케이션 시작...")
    app = QApplication(sys.argv)

    loading_screen = LoadingScreen()
    loading_screen.show()

    thread = QThread()
    worker = Worker()
    worker.moveToThread(thread)
    
    # 워커 스레드의 진행률 시그널을 로딩 스크린의 업데이트 함수에 연결
    worker.progress_updated.connect(loading_screen.update_progress)
    
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    worker.finished.connect(lambda: show_toolbar_and_cleanup(loading_screen))
    
    thread.start()
    
    sys.exit(app.exec_())