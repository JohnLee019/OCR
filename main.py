# main.py
import sys
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QCoreApplication
from toolbar import ToolBar, ProcessingOverlay
from combined import initialize_components

# -------------------------------
# 초기화 작업 워커 (별도 스레드)
# -------------------------------
class Worker(QObject):
    finished = pyqtSignal()
    progress_updated = pyqtSignal(int, str)  # (진행률, 메시지)

    def run(self):
        # initialize_components가 진행률/메시지를 계속 올려줌
        initialize_components(self.progress_updated)
        self.finished.emit()

# -------------------------------
# 유틸
# -------------------------------
def center_widget(widget):
    screen_center = QDesktopWidget().availableGeometry().center()
    geo = widget.frameGeometry()
    geo.moveCenter(screen_center)
    widget.move(geo.topLeft())

# 전역 툴바 핸들(가비지 컬렉션 방지)
global_toolbar = None

def show_toolbar_and_cleanup(overlay: ProcessingOverlay):
    """초기화 완료 → 오버레이 닫고 툴바 표시"""
    global global_toolbar
    overlay.hide()
    overlay.deleteLater()

    global_toolbar = ToolBar()
    global_toolbar.show()

# -------------------------------
# 엔트리 포인트
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ✅ 캡처/연속읽기 때 쓰는 ProcessingOverlay를 그대로 사용
    overlay = ProcessingOverlay(None, text="0% 완료")
    # 퍼센트 진행바로 사용(0~100)
    overlay.bar.setRange(0, 100)
    overlay.bar.setValue(0)
    center_widget(overlay)
    overlay.show()

    # 초기화 워커/스레드
    thread = QThread()
    worker = Worker()
    worker.moveToThread(thread)

    # 진행률을 예쁜 오버레이에 업데이트 (퍼센트 + 메시지)
    def _on_progress(v, msg):
        try:
            v = int(v)
        except Exception:
            v = 0
        overlay.bar.setValue(v)
        overlay.set_text(f"{v}% 완료" + (f" — {msg}" if msg else ""))

        # UI 즉시 갱신 (초기 로딩 중에도 부드럽게)
        QCoreApplication.processEvents()

    worker.progress_updated.connect(_on_progress)

    # 완료 시: 오버레이 닫고 툴바 띄우기
    worker.finished.connect(lambda: show_toolbar_and_cleanup(overlay))

    # 스레드 생명주기 연결
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    # 앱 종료 직전, 남은 초기화 스레드 안전 종료
    def _ensure_init_thread_stopped():
        if thread.isRunning():
            thread.quit()
            thread.wait(5000)  # 최대 5초 대기
    app.aboutToQuit.connect(_ensure_init_thread_stopped)

    thread.start()
    sys.exit(app.exec_())
