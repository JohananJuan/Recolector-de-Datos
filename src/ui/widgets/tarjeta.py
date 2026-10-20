from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel


class Tarjeta(QFrame):
    def __init__(self, titulo: str, valor: str = "—", subtitulo: str = ""):
        super().__init__()
        self.setObjectName("tarjeta")
        self.setStyleSheet("""
            QFrame#tarjeta {
                background: #313244;
                border: 1px solid #45475a;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._titulo = QLabel(titulo)
        self._titulo.setObjectName("subtitulo")

        self._valor = QLabel(valor)
        self._valor.setObjectName("valor")
        self._valor.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._sub = QLabel(subtitulo)
        self._sub.setObjectName("subtitulo")

        layout.addWidget(self._titulo)
        layout.addWidget(self._valor)
        layout.addWidget(self._sub)

    def actualizar(self, valor: str, subtitulo: str = "") -> None:
        self._valor.setText(valor)
        if subtitulo:
            self._sub.setText(subtitulo)