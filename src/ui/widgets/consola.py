from __future__ import annotations
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QColor, QTextCharFormat, QTextCursor

_COLORES = {
    "nucleo": "#888888", "limpieza": "#e67e22", "correlacion": "#3498db",
    "legal": "#9b59b6", "normalizacion": "#2ecc71", "discretizacion": "#f39c12",
    "redimensionado": "#1abc9c", "mejora": "#e74c3c", "texto": "#34495e",
    "score_calidad": "#16a085",
    "ok": "#a6e3a1", "error": "#f38ba8", "warn": "#f9e2af",
}


class Consola(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")

    def log(self, mensaje: str, etapa: str = "") -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        color = _COLORES.get(etapa, "#cdd6f4")
        fmt.setForeground(QColor(color))
        prefijo = f"[{etapa}] " if etapa else ""
        cursor.insertText(prefijo + mensaje + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()