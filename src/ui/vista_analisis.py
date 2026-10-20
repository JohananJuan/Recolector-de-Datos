import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QGridLayout,
)

from controladores.controlador_analisis import ControladorAnalisis
from ui.widgets.consola import Consola
from ui.widgets.tarjeta import Tarjeta


class VistaAnalisis(QWidget):
    def __init__(self, controlador: ControladorAnalisis):
        super().__init__()
        self._ctrl = controlador
        self._df = None
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)

        titulo = QLabel("Análisis del dataset")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        sub = QLabel("Estadísticos descriptivos y outliers sobre ancho, alto y tamaño.")
        sub.setObjectName("subtitulo")
        layout.addWidget(sub)

        self._btn = QPushButton("▶ Cargar y analizar")
        self._btn.clicked.connect(self._ejecutar)
        layout.addWidget(self._btn)

        grid = QGridLayout()
        self._tarjetas: dict[str, dict[str, Tarjeta]] = {}
        for i, col in enumerate(("ancho", "alto", "tamano_bytes")):
            grupo = QGroupBox(col)
            gl = QGridLayout(grupo)
            self._tarjetas[col] = {}
            for j, (k, label) in enumerate([
                ("media", "Media"), ("mediana", "Mediana"), ("moda", "Moda"),
                ("std", "Std"), ("min", "Mín"), ("max", "Máx"),
                ("outliers_z", "Z-outliers"), ("outliers_iqr", "IQR"),
                ("interseccion", "Intersección"),
            ]):
                t = Tarjeta(label, "—")
                self._tarjetas[col][k] = t
                gl.addWidget(t, j // 3, j % 3)
            grid.addWidget(grupo, 0, i)
        layout.addLayout(grid)

        grupo_graf = QGroupBox("Distribución por clase")
        gl = QVBoxLayout(grupo_graf)
        self._figura = Figure(figsize=(6, 3), facecolor="#181825")
        self._canvas = FigureCanvasQTAgg(self._figura)
        gl.addWidget(self._canvas)
        layout.addWidget(grupo_graf)

        grupo_log = QGroupBox("Resumen")
        gl = QVBoxLayout(grupo_log)
        self._consola = Consola()
        self._consola.setMaximumHeight(140)
        gl.addWidget(self._consola)
        layout.addWidget(grupo_log)

    def _ejecutar(self) -> None:
        self._btn.setEnabled(False)
        try:
            self._df = self._ctrl.cargar_dataframe()
        except Exception as e:
            self._consola.log(f"Error: {e}", "error")
            self._btn.setEnabled(True)
            return

        if self._df is None:
            self._consola.log("Sin registros para analizar.", "warn")
            self._btn.setEnabled(True)
            return

        df = self._df
        self._consola.log(f"Registros: {len(df)}  |  Columnas: {len(df.columns)}")
        for clase, n in df["clase"].value_counts().items():
            self._consola.appendPlainText(f"   {clase:10} {n:5} ({n / len(df) * 100:.2f}%)")

        for col in ("ancho", "alto", "tamano_bytes"):
            r = self._ctrl.resumen_numerico(df, col)
            if not r:
                continue
            t = self._tarjetas[col]
            t["media"].actualizar(f"{r['media']:.1f}")
            t["mediana"].actualizar(f"{r['mediana']:.1f}")
            t["moda"].actualizar(f"{r['moda']}")
            t["std"].actualizar(f"{r['std']:.1f}")
            t["min"].actualizar(f"{r['min']:.0f}")
            t["max"].actualizar(f"{r['max']:.0f}")
            t["outliers_z"].actualizar(str(r["outliers_z"]))
            t["outliers_iqr"].actualizar(str(r["outliers_iqr"]))
            t["interseccion"].actualizar(str(r["interseccion"]))

        self._figura.clear()
        ax = self._figura.add_subplot(111)
        ax.set_facecolor("#181825")
        df["clase"].value_counts().plot(kind="bar", ax=ax, color="#89b4fa")
        ax.set_title("Imágenes por clase", color="#cdd6f4")
        ax.tick_params(colors="#cdd6f4")
        for spine in ax.spines.values():
            spine.set_color("#45475a")
        self._figura.tight_layout()
        self._canvas.draw()

        self._consola.log("Análisis completado.", "ok")
        self._btn.setEnabled(True)