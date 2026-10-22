from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QGridLayout, QComboBox, QScrollArea, QFrame,
)

from controladores.controlador_analisis import ControladorAnalisis
from ui.widgets.consola import Consola
from ui.widgets.grafico import GraficoBarras
from ui.widgets.tarjeta import Tarjeta


class VistaAnalisis(QWidget):
    ANCHO_MIN_TARJETA = 120

    def __init__(self, controlador: ControladorAnalisis):
        super().__init__()
        self._ctrl = controlador
        self._df = None
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        titulo = QLabel("Análisis del dataset")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        sub = QLabel("Estadísticos descriptivos y outliers sobre ancho, alto y tamaño.")
        sub.setObjectName("subtitulo")
        layout.addWidget(sub)

        fila_fuente = QHBoxLayout()
        fila_fuente.addWidget(QLabel("Fuente:"))
        self._combo_fuente = QComboBox()
        _, nombre_proc = self._ctrl.preset_procesado()
        _, nombre_cap = self._ctrl.preset_capturas()
        self._combo_fuente.addItems([nombre_proc, nombre_cap])
        fila_fuente.addWidget(self._combo_fuente, stretch=1)
        layout.addLayout(fila_fuente)

        self._btn = QPushButton("▶ Cargar y analizar")
        self._btn.clicked.connect(self._ejecutar)
        layout.addWidget(self._btn)

        scroll_metricas = QScrollArea()
        scroll_metricas.setWidgetResizable(True)
        scroll_metricas.setFrameShape(QFrame.NoFrame)
        scroll_metricas.setHorizontalScrollBarPolicy(
            __import__("PyQt5.QtCore", fromlist=["Qt"]).Qt.ScrollBarAsNeeded
        )
        scroll_metricas.setVerticalScrollBarPolicy(
            __import__("PyQt5.QtCore", fromlist=["Qt"]).Qt.ScrollBarAlwaysOff
        )
        contenedor = QWidget()
        grid = QGridLayout(contenedor)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)

        self._tarjetas: dict[str, dict[str, Tarjeta]] = {}
        for i, col in enumerate(("ancho", "alto", "tamano_bytes")):
            grupo = QGroupBox(col)
            gl = QGridLayout(grupo)
            gl.setHorizontalSpacing(8)
            gl.setVerticalSpacing(8)
            gl.setContentsMargins(8, 8, 8, 8)

            self._tarjetas[col] = {}
            for j, (k, label) in enumerate([
                ("media", "Media"), ("mediana", "Mediana"), ("moda", "Moda"),
                ("std", "Std"), ("min", "Mín"), ("max", "Máx"),
                ("outliers_z", "Z-outliers"), ("outliers_iqr", "IQR"),
                ("interseccion", "Intersección"),
            ]):
                t = Tarjeta(label, "—", compacta=True)
                t.setMinimumWidth(self.ANCHO_MIN_TARJETA)
                self._tarjetas[col][k] = t
                gl.addWidget(t, j // 3, j % 3)

            grupo.setMinimumWidth(self.ANCHO_MIN_TARJETA * 3 + 40)
            grid.addWidget(grupo, 0, i)

        scroll_metricas.setWidget(contenedor)
        layout.addWidget(scroll_metricas, stretch=2)

        grupo_graf = QGroupBox("Distribución por clase")
        gl = QVBoxLayout(grupo_graf)
        self._grafico = GraficoBarras()
        self._grafico.setMinimumHeight(240)
        gl.addWidget(self._grafico)
        layout.addWidget(grupo_graf, stretch=3)

        grupo_log = QGroupBox("Resumen")
        gl = QVBoxLayout(grupo_log)
        self._consola = Consola()
        self._consola.setMaximumHeight(120)
        gl.addWidget(self._consola)
        layout.addWidget(grupo_log)

    def _ruta_por_fuente(self):
        idx = self._combo_fuente.currentIndex()
        if idx == 0:
            return self._ctrl.preset_procesado()
        return self._ctrl.preset_capturas()

    def _formato(self, valor) -> str:
        try:
            return f"{float(valor):,.0f}" if float(valor) == int(float(valor)) else f"{float(valor):,.1f}"
        except (TypeError, ValueError):
            return str(valor)

    def _ejecutar(self) -> None:
        ruta, nombre = self._ruta_por_fuente()
        self._btn.setEnabled(False)
        self._consola.log(f"Analizando {nombre} → {ruta}")
        try:
            self._df = self._ctrl.cargar_dataframe(ruta)
        except Exception as e:
            self._consola.log(f"Error: {e}", "error")
            self._btn.setEnabled(True)
            return

        if self._df is None:
            self._consola.log(f"Sin registros en {ruta}.", "warn")
            self._btn.setEnabled(True)
            return

        df = self._df
        self._consola.log(f"Registros: {len(df)}  |  Columnas: {len(df.columns)}")
        for clase, n in df["clase"].value_counts().items():
            self._consola.appendPlainText(
                f"   {clase:10} {n:5} ({n / len(df) * 100:.2f}%)"
            )

        for col in ("ancho", "alto", "tamano_bytes"):
            r = self._ctrl.resumen_numerico(df, col)
            if not r:
                continue
            t = self._tarjetas[col]
            t["media"].actualizar(self._formato(r["media"]))
            t["mediana"].actualizar(self._formato(r["mediana"]))
            t["moda"].actualizar(self._formato(r["moda"]))
            t["std"].actualizar(self._formato(r["std"]))
            t["min"].actualizar(self._formato(r["min"]))
            t["max"].actualizar(self._formato(r["max"]))
            t["outliers_z"].actualizar(str(r["outliers_z"]))
            t["outliers_iqr"].actualizar(str(r["outliers_iqr"]))
            t["interseccion"].actualizar(str(r["interseccion"]))

        conteos = df["clase"].value_counts().to_dict()
        self._grafico.mostrar(conteos, f"Imágenes por clase · {nombre}")

        self._consola.log("Análisis completado.", "ok")
        self._btn.setEnabled(True)