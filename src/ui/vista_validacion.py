from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox,
)

from controladores.controlador_validacion import ControladorValidacion
from core.presets import preset_capturas, preset_publico
from ui.widgets.consola import Consola
from ui.widgets.tarjeta import Tarjeta


class VistaValidacion(QWidget):
    def __init__(self, controlador: ControladorValidacion):
        super().__init__()
        self._ctrl = controlador
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        titulo = QLabel("Validación de dataset")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        sub = QLabel("Extensión, decodificación, duplicados SHA/pHash y calidad visual.")
        sub.setObjectName("subtitulo")
        layout.addWidget(sub)

        fila_preset = QHBoxLayout()
        fila_preset.addWidget(QLabel("Preset:"))
        self._combo_preset = QComboBox()
        self._combo_preset.addItems(["Dataset público", "Capturas propias"])
        self._combo_preset.currentIndexChanged.connect(self._aplicar_preset)
        fila_preset.addWidget(self._combo_preset, stretch=1)
        layout.addLayout(fila_preset)

        fila_dir = QHBoxLayout()
        fila_dir.addWidget(QLabel("Directorio:"))
        self._input_dir = QLineEdit()
        fila_dir.addWidget(self._input_dir, stretch=1)
        layout.addLayout(fila_dir)

        fila_fuente = QHBoxLayout()
        fila_fuente.addWidget(QLabel("Fuente:"))
        self._combo_fuente = QComboBox()
        self._combo_fuente.addItems(["dataset_publico", "captura_controlada", "prototipo"])
        fila_fuente.addWidget(self._combo_fuente, stretch=1)
        layout.addLayout(fila_fuente)

        self._btn_ejecutar = QPushButton("▶ Ejecutar validación")
        self._btn_ejecutar.clicked.connect(self._ejecutar)
        layout.addWidget(self._btn_ejecutar)

        fila_tarjetas = QHBoxLayout()
        self._t_total = Tarjeta("Total", "—")
        self._t_validas = Tarjeta("Válidas", "—")
        self._t_revisar = Tarjeta("A revisar", "—")
        self._t_invalidas = Tarjeta("Inválidas", "—")
        for t in (self._t_total, self._t_validas, self._t_revisar, self._t_invalidas):
            fila_tarjetas.addWidget(t)
        layout.addLayout(fila_tarjetas)

        grupo = QGroupBox("Salida")
        gl = QVBoxLayout(grupo)
        self._consola = Consola()
        gl.addWidget(self._consola)
        layout.addWidget(grupo)

        self._aplicar_preset(0)

    def _aplicar_preset(self, idx: int) -> None:
        preset = preset_publico() if idx == 0 else preset_capturas()
        self._input_dir.setText(str(preset.directorio))
        self._combo_fuente.setCurrentText(
            "dataset_publico" if idx == 0 else "captura_controlada"
        )

    def _ejecutar(self) -> None:
        directorio = Path(self._input_dir.text().strip())
        fuente = self._combo_fuente.currentText()
        if not directorio.exists():
            self._consola.log(f"No existe: {directorio}", "error")
            return
        self._btn_ejecutar.setEnabled(False)
        self._consola.log(f"Validando {directorio} ...")
        try:
            resumen, salida = self._ctrl.validar(directorio, fuente)
        except Exception as e:
            self._consola.log(f"Error: {e}", "error")
            self._btn_ejecutar.setEnabled(True)
            return

        self._consola.appendPlainText(salida.strip())
        self._t_total.actualizar(str(resumen.get("total", 0)))
        self._t_validas.actualizar(str(resumen.get("validas", 0)))
        self._t_revisar.actualizar(str(resumen.get("revisar", 0)))
        self._t_invalidas.actualizar(str(resumen.get("invalidas", 0)))
        self._consola.log("Validación completada.", "ok")
        self._btn_ejecutar.setEnabled(True)