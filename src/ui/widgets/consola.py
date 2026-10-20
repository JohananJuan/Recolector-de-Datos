from datetime import datetime
from PyQt5.QtWidgets import QPlainTextEdit


class Consola(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setMaximumBlockCount(2000)

    def log(self, mensaje: str, nivel: str = "info") -> None:
        iconos = {"info": "·", "ok": "✔", "warn": "⚠", "error": "✖"}
        h = datetime.now().strftime("%H:%M:%S")
        self.appendPlainText(f"[{h}] {iconos.get(nivel, '·')}  {mensaje}")
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())