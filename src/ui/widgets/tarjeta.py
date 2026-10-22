from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel


class Tarjeta(QFrame):
    def __init__(self, titulo: str, valor: str = "—", subtitulo: str = "",
                 compacta: bool = False):
        super().__init__()
        self.setObjectName("tarjeta")
        self.setStyleSheet("""
            QFrame#tarjeta {
                background: #313244;
                border: 1px solid #45475a;
                border-radius: 10px;
            }
        """)
        margen_h = 8 if compacta else 16
        margen_v = 5 if compacta else 12
        espaciado = 1 if compacta else 4

        layout = QVBoxLayout(self)
        layout.setContentsMargins(margen_h, margen_v, margen_h, margen_v)
        layout.setSpacing(espaciado)

        self._titulo = QLabel(titulo)
        self._titulo.setObjectName("subtitulo")
        self._titulo.setWordWrap(False)
        if compacta:
            self._titulo.setStyleSheet(
                "font-size: 10px; color: #a6adc8; background: transparent;"
            )

        self._valor = QLabel(valor)
        self._valor.setObjectName("valor")
        self._valor.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._valor.setWordWrap(False)
        if compacta:
            self._valor.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #a6e3a1; "
                "background: transparent;"
            )

        self._sub = QLabel(subtitulo)
        self._sub.setObjectName("subtitulo")
        self._sub.setWordWrap(False)
        if compacta:
            self._sub.setStyleSheet(
                "font-size: 9px; color: #a6adc8; background: transparent;"
            )

        layout.addWidget(self._titulo)
        layout.addWidget(self._valor)
        layout.addWidget(self._sub)

    def actualizar(self, valor: str, subtitulo: str = "") -> None:
        self._valor.setText(valor)
        if subtitulo:
            self._sub.setText(subtitulo)