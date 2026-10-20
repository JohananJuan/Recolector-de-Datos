from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QMessageBox,
)

from controladores.controlador_captura import ControladorCaptura
from controladores.controlador_validacion import ControladorValidacion
from controladores.controlador_analisis import ControladorAnalisis
from controladores.controlador_splits import ControladorSplits

from ui.vista_captura import VistaCaptura
from ui.vista_validacion import VistaValidacion
from ui.vista_analisis import VistaAnalisis
from ui.vista_splits import VistaSplits


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clasificador de Residuos · Recolector")
        self.resize(1440, 900)
        self.setMinimumSize(1200, 760)
        self._construir_ui()

    def _construir_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)

        titulo = QLabel("♻ Recolector de datos")
        titulo.setObjectName("titulo")
        header.addWidget(titulo)
        header.addStretch()

        self._btn_salir = QPushButton("Salir")
        self._btn_salir.setObjectName("peligro")
        self._btn_salir.setFixedWidth(110)
        self._btn_salir.clicked.connect(self._salir)
        header.addWidget(self._btn_salir)

        layout.addLayout(header)

        sub = QLabel("Captura, validación, análisis y splits")
        sub.setObjectName("subtitulo")
        layout.addWidget(sub)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(VistaCaptura(ControladorCaptura()), "Captura")
        tabs.addTab(VistaValidacion(ControladorValidacion()), "Validación")
        tabs.addTab(VistaAnalisis(ControladorAnalisis()), "Análisis")
        tabs.addTab(VistaSplits(ControladorSplits()), "Splits")
        layout.addWidget(tabs, stretch=1)

        self.setCentralWidget(central)

    def _salir(self) -> None:
        resp = QMessageBox.question(
            self, "Salir",
            "¿Cerrar la aplicación?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if resp == QMessageBox.Yes:
            self.close()