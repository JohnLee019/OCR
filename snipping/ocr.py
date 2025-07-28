import sys
import tempfile
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit
from PyQt5.QtGui import QGuiApplication, QPixmap

class SnippingTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Snipping Tool with Microsoft OCR")
        self.setGeometry(100, 100, 500, 400)

        self.image_path = None

        layout = QVBoxLayout()
        self.snip_btn = QPushButton("Snip")
        self.ocr_btn = QPushButton("OCR")
        self.copy_btn = QPushButton("Copy")
        self.text_area = QTextEdit()

        layout.addWidget(self.snip_btn)
        layout.addWidget(self.ocr_btn)
        layout.addWidget(self.copy_btn)
        layout.addWidget(self.text_area)

        self.setLayout(layout)

        self.snip_btn.clicked.connect(self.snip)
        self.ocr_btn.clicked.connect(self.do_ocr)
        self.copy_btn.clicked.connect(self.copy_text)

    def snip(self):
        self.hide()
        QGuiApplication.processEvents()

        subprocess.run(["snippingtool", "/clip"])  # Copies to clipboard
        self.show()

        image = QGuiApplication.clipboard().image()
        if not image.isNull():
            temp_path = tempfile.mktemp(suffix=".png")
            image.save(temp_path)
            self.image_path = temp_path
            self.text_area.setPlainText("Snip captured. Ready for OCR.")

    def do_ocr(self):
        if not self.image_path:
            self.text_area.setPlainText("No image captured yet.")
            return

        # Use Azure or Windows OCR – here we'll use Windows OCR via PowerShell
        powershell_script = f"""
            Add-Type -AssemblyName System.Drawing
            Add-Type -AssemblyName Windows.Graphics
            Add-Type -AssemblyName Windows.Media.Ocr

            $stream = [Windows.Storage.Streams.RandomAccessStreamReference]::CreateFromFile((New-Object -ComObject Shell.Application).NameSpace(0).ParseName('{self.image_path}'))
            $decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetResults()
            $bitmap = $decoder.GetSoftwareBitmapAsync().GetResults()
            $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
            $result = $ocrEngine.RecognizeAsync($bitmap).GetAwaiter().GetResult()
            $result.Text
        """

        with tempfile.NamedTemporaryFile(delete=False, suffix=".ps1") as f:
            f.write(powershell_script.encode("utf-8"))
            script_path = f.name

        completed = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
            capture_output=True,
            text=True,
        )
        text = completed.stdout.strip()
        self.text_area.setPlainText(text if text else "No text recognized.")

    def copy_text(self):
        QGuiApplication.clipboard().setText(self.text_area.toPlainText())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tool = SnippingTool()
    tool.show()
    sys.exit(app.exec_())
