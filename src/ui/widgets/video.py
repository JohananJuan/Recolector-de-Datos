from __future__ import annotations

from typing import Optional

import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QSizePolicy


class WidgetVideo(QLabel):
    def __init__(self, resolucion: tuple[int, int], texto_espera: str = "Cámara detenida"):
        super().__init__(texto_espera)
        self._resolucion = resolucion
        self._texto_espera = texto_espera
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(720, 405)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "background:#11111b; border:1px solid #313244; "
            "border-radius:8px; color:#6c7086; font-size:16px;"
        )

    def mostrar_frame(self, frame_bgr) -> None:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.setPixmap(QPixmap.fromImage(img).scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def mostrar_espera(self, mensaje: Optional[str] = None) -> None:
        self.setPixmap(QPixmap())
        self.setText(mensaje or self._texto_espera)