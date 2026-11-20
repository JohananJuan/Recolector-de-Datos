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


class TarjetaEtapa(QFrame):

    _OPCIONES = {
        "filtro": ["mediana", "gaussiano", "bilateral"],
        "formato": ["JPEG", "PNG"],
        "modo": ["recortar", "rellenar", "estirar"],
        "estrategia": ["ancho", "frecuencia"],
        "metodo": ["zscore", "minmax", "robusto", "l2"],
        "metodo_imputacion": ["mediana", "media", "moda"],
    }

    def __init__(
        self, clave, tema, nombre, descripcion, parametros,
        on_toggle=None, on_ejecutar=None, on_reset=None, on_ver=None,
        parent=None,
    ):
        super().__init__(parent)
        from PyQt5.QtWidgets import (
            QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout,
            QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout,
        )
        self.clave = clave
        self.on_toggle = on_toggle
        self.on_ejecutar = on_ejecutar
        self.on_reset = on_reset
        self.on_ver = on_ver

        self.setObjectName("tarjetaEtapa")
        raiz = QVBoxLayout(self)

        cab = QHBoxLayout()
        self.chk = QCheckBox(f"[{tema}] {nombre}")
        self.chk.setChecked(True)
        self.chk.setToolTip(descripcion)
        self.chk.toggled.connect(
            lambda v: self.on_toggle and self.on_toggle(self.clave, v)
        )
        cab.addWidget(self.chk)
        cab.addStretch(1)
        raiz.addLayout(cab)

        self._widgets: dict = {}
        form = QFormLayout()
        for k, v in parametros.items():
            if k in self._OPCIONES:
                w = QComboBox()
                w.addItems(self._OPCIONES[k])
                w.setCurrentText(str(v))
            elif isinstance(v, bool):
                w = QCheckBox()
                w.setChecked(v)
            elif isinstance(v, int):
                w = QSpinBox()
                w.setRange(0, 100_000)
                w.setValue(v)
            elif isinstance(v, float):
                w = QDoubleSpinBox()
                w.setRange(0, 1e6)
                w.setDecimals(3)
                w.setValue(v)
            elif isinstance(v, (list, tuple)):
                w = QLineEdit(", ".join(str(x) for x in v))
            else:
                w = QLineEdit(str(v))
            self._widgets[k] = w
            form.addRow(k, w)
        raiz.addLayout(form)

        self.lbl_res = QLabel("— sin ejecutar —")
        self.lbl_res.setStyleSheet("color:#a6adc8;font-style:italic;")
        raiz.addWidget(self.lbl_res)

        acc = QHBoxLayout()
        for texto, cb in (
            ("Ejecutar solo esta etapa", self.on_ejecutar),
            ("Restablecer parámetros", self.on_reset),
            ("Ver antes/después", self.on_ver),
        ):
            b = QPushButton(texto)
            b.clicked.connect(lambda _, c=cb: c and c(self.clave))
            acc.addWidget(b)
        raiz.addLayout(acc)

    def parametros_actuales(self) -> dict:
        from PyQt5.QtWidgets import (
            QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox,
        )
        out = {}
        for k, w in self._widgets.items():
            if isinstance(w, QComboBox):
                out[k] = w.currentText()
            elif isinstance(w, QCheckBox):
                out[k] = w.isChecked()
            elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
                out[k] = w.value()
            elif isinstance(w, QLineEdit):
                txt = w.text()
                out[k] = [t.strip() for t in txt.split(",") if t.strip()] \
                    if "," in txt else txt
            else:
                out[k] = w.text() if hasattr(w, "text") else None
        return out

    def establecer_parametros(self, parametros: dict) -> None:
        from PyQt5.QtWidgets import (
            QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit, QSpinBox,
        )
        for k, v in parametros.items():
            w = self._widgets.get(k)
            if isinstance(w, QComboBox):
                w.setCurrentText(str(v))
            elif isinstance(w, QCheckBox):
                w.setChecked(bool(v))
            elif isinstance(w, (QSpinBox, QDoubleSpinBox)):
                w.setValue(v)
            elif isinstance(w, QLineEdit):
                w.setText(", ".join(map(str, v))
                          if isinstance(v, (list, tuple)) else str(v))
        self.lbl_res.setText("— sin ejecutar —")
        self.lbl_res.setStyleSheet("color:#a6adc8;font-style:italic;")

    def mostrar_resultado(self, res) -> None:
        icono = "✓" if res.ok else "✗"
        color = "#a6e3a1" if res.ok else "#f38ba8"
        self.lbl_res.setText(
            f"{icono} {res.mensaje}  (afectadas: {res.filas_afectadas})"
        )
        self.lbl_res.setStyleSheet(f"color:{color};font-weight:bold;")