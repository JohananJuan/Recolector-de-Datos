from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox,
)

from controladores.controlador_splits import ControladorSplits
from core.presets import preset_publico, preset_splits
from ui.widgets.consola import Consola
from ui.widgets.tarjeta import Tarjeta


class VistaSplits(QWidget):
    def __init__(self, controlador: ControladorSplits):
        super().__init__()
        self._ctrl = controlador
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        titulo = QLabel("Exportar splits")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        sub = QLabel("70 / 15 / 15 agrupado por sesión, con fallback por clase.")
        sub.setObjectName("subtitulo")
        layout.addWidget(sub)

        fila1 = QHBoxLayout()
        fila1.addWidget(QLabel("Metadata:"))
        self._in_meta = QLineEdit(str(preset_publico().metadata))
        fila1.addWidget(self._in_meta, stretch=1)
        layout.addLayout(fila1)

        fila2 = QHBoxLayout()
        fila2.addWidget(QLabel("Salida:"))
        self._in_out = QLineEdit(str(preset_splits().directorio))
        fila2.addWidget(self._in_out, stretch=1)
        layout.addLayout(fila2)

        self._btn = QPushButton("▶ Exportar splits")
        self._btn.clicked.connect(self._ejecutar)
        layout.addWidget(self._btn)

        fila_t = QHBoxLayout()
        self._t_train = Tarjeta("Train", "—")
        self._t_val = Tarjeta("Val", "—")
        self._t_test = Tarjeta("Test", "—")
        for t in (self._t_train, self._t_val, self._t_test):
            fila_t.addWidget(t)
        layout.addLayout(fila_t)

        grupo = QGroupBox("Salida")
        gl = QVBoxLayout(grupo)
        self._consola = Consola()
        gl.addWidget(self._consola)
        layout.addWidget(grupo)

    def _ejecutar(self) -> None:
        meta = Path(self._in_meta.text().strip())
        salida = Path(self._in_out.text().strip())
        if not meta.exists():
            self._consola.log(f"No existe: {meta}", "error")
            return
        self._btn.setEnabled(False)
        try:
            conteo, log = self._ctrl.exportar(meta, salida)
        except Exception as e:
            self._consola.log(f"Error: {e}", "error")
            self._btn.setEnabled(True)
            return
        self._consola.appendPlainText(log.strip())
        self._t_train.actualizar(str(conteo.get("train", 0)))
        self._t_val.actualizar(str(conteo.get("val", 0)))
        self._t_test.actualizar(str(conteo.get("test", 0)))
        self._consola.log("Splits exportados.", "ok")
        self._btn.setEnabled(True)