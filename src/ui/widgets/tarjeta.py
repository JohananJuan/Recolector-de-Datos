from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout


class Tarjeta(QFrame):

    def __init__(
        self,
        titulo: str,
        valor: str = "—",
        subtitulo: str = "",
        compacta: bool = False,
        variante: str = "default",
    ):
        super().__init__()
        object_name = "tarjetaMetrica" if variante == "metrica" else "tarjeta"
        self.setObjectName(object_name)
        if variante == "default":
            self.setStyleSheet("""
                QFrame#tarjeta {
                    background: #313244;
                    border: 1px solid #45475a;
                    border-radius: 10px;
                }
            """)

        margen_h = 8 if compacta else (14 if variante == "metrica" else 16)
        margen_v = 5 if compacta else (10 if variante == "metrica" else 12)
        espaciado = 1 if compacta else (2 if variante == "metrica" else 4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(margen_h, margen_v, margen_h, margen_v)
        layout.setSpacing(espaciado)

        nombre_titulo = "tarjetaTitulo" if variante == "metrica" else "subtitulo"
        nombre_valor = "tarjetaValor" if variante == "metrica" else "valor"

        self._titulo = QLabel(titulo)
        self._titulo.setObjectName(nombre_titulo)
        self._titulo.setAlignment(Qt.AlignLeft)
        self._titulo.setWordWrap(False)

        self._valor = QLabel(valor)
        self._valor.setObjectName(nombre_valor)
        self._valor.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._valor.setWordWrap(False)

        self._sub = QLabel(subtitulo)
        self._sub.setObjectName("subtitulo")
        self._sub.setWordWrap(False)

        if compacta:
            self._titulo.setStyleSheet(
                "font-size: 10px; color: #a6adc8; background: transparent;"
            )
            self._valor.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #a6e3a1; "
                "background: transparent;"
            )
            self._sub.setStyleSheet(
                "font-size: 9px; color: #a6adc8; background: transparent;"
            )

        layout.addWidget(self._titulo)
        layout.addWidget(self._valor)
        if subtitulo or variante == "default":
            layout.addWidget(self._sub)

    def actualizar(self, valor: str, subtitulo: str = "") -> None:
        self._valor.setText(str(valor))
        if subtitulo:
            self._sub.setText(subtitulo)