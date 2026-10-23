from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from analisis.pipeline_analisis import AnalisisResultado, PipelineAnalisis
from limpieza.normalizacion import metodos_disponibles
from ui.widgets.consola import Consola
from ui.widgets.grafica_analisis import GraficaAnalisis
from ui.widgets.tabla_datos import TablaDatos
from ui.widgets.tarjeta import Tarjeta


class _WorkerPipeline(QThread):

    progreso = pyqtSignal(str)
    terminado = pyqtSignal(object)   
    error = pyqtSignal(str)

    def __init__(self, raiz: Path, metodo_norm: str, parent=None):
        super().__init__(parent)
        self._raiz = raiz
        self._metodo = metodo_norm

    def run(self):
        try:
            pipeline = PipelineAnalisis(metodo_normalizacion=self._metodo)
            resultado = pipeline.analizar(
                self._raiz, al_progresar=self.progreso.emit
            )
            self.terminado.emit(resultado)
        except Exception as e:  # noqa: BLE001
            self.error.emit(f"{type(e).__name__}: {e}")


class VistaAnalisis(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._raiz: Optional[Path] = None
        self._resultado: Optional[AnalisisResultado] = None
        self._worker: Optional[_WorkerPipeline] = None
        self._construir_ui()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        cabecera = QHBoxLayout()

        self._lbl_ruta = QLabel("Sin directorio seleccionado")
        self._lbl_ruta.setObjectName("rutaSeleccionada")
        self._lbl_ruta.setWordWrap(True)

        btn_elegir = QPushButton("Elegir carpeta…")
        btn_elegir.clicked.connect(self._elegir_carpeta)

        self._combo_norm = QComboBox()
        self._combo_norm.addItems(metodos_disponibles())
        self._combo_norm.setCurrentText("zscore")
        self._combo_norm.setToolTip("Método de normalización")

        self._btn_analizar = QPushButton("Analizar")
        self._btn_analizar.setEnabled(False)
        self._btn_analizar.clicked.connect(self._analizar)

        self._btn_exportar = QPushButton("Exportar Excel…")
        self._btn_exportar.setEnabled(False)
        self._btn_exportar.clicked.connect(self._exportar_excel)

        self._btn_json = QPushButton("Exportar JSON…")
        self._btn_json.setEnabled(False)
        self._btn_json.clicked.connect(self._exportar_json)

        self._btn_csv = QPushButton("Exportar CSV…")
        self._btn_csv.setEnabled(False)
        self._btn_csv.clicked.connect(self._exportar_csv)

        cabecera.addWidget(self._lbl_ruta, stretch=1)
        cabecera.addWidget(btn_elegir)
        cabecera.addWidget(self._combo_norm)
        cabecera.addWidget(self._btn_analizar)
        cabecera.addWidget(self._btn_exportar)
        cabecera.addWidget(self._btn_json)
        cabecera.addWidget(self._btn_csv)
        layout.addLayout(cabecera)

        kpis = QHBoxLayout()
        self._kpi_crudas = Tarjeta("Filas crudas", variante="metrica")
        self._kpi_ruido = Tarjeta("Ruido eliminado", variante="metrica")
        self._kpi_limpias = Tarjeta("Filas limpias", variante="metrica")
        self._kpi_aprobadas = Tarjeta("Aprobadas estándar", variante="metrica")
        self._kpi_rechazadas = Tarjeta("Rechazadas", variante="metrica")
        for k in (
            self._kpi_crudas,
            self._kpi_ruido,
            self._kpi_limpias,
            self._kpi_aprobadas,
            self._kpi_rechazadas,
        ):
            kpis.addWidget(k)
        layout.addLayout(kpis)

        self._tabs = QTabWidget()

        self._tabla_crudo = TablaDatos()
        self._tabla_limpio = TablaDatos()
        self._tabla_norm = TablaDatos()
        self._tabla_comp = TablaDatos()
        self._tabla_pair = TablaDatos()
        self._tabla_list = TablaDatos()
        self._tabla_est = TablaDatos()
        self._tabla_aprob = TablaDatos()
        self._tabla_rech = TablaDatos()

        self._consola = Consola()

        self._grafica = QTabWidget()
        self._g_dist = GraficaAnalisis()
        self._g_top = GraficaAnalisis()
        self._g_out = GraficaAnalisis()
        self._g_disp = GraficaAnalisis()
        self._g_delta = GraficaAnalisis()

        self._grafica.addTab(self._g_dist, "Distribución")
        self._grafica.addTab(self._g_top, "Top/Bottom")
        self._grafica.addTab(self._g_out, "Outliers")
        self._grafica.addTab(self._g_disp, "Dispersión")
        self._grafica.addTab(self._g_delta, "Delta por columna")

        self._tabs.addTab(self._grafica, "Gráficas")
        self._tabs.addTab(self._tabla_crudo, "Crudo")
        self._tabs.addTab(self._tabla_limpio, "Limpio")
        self._tabs.addTab(self._tabla_norm, "Normalizado")
        self._tabs.addTab(self._tabla_comp, "Comparativa (col)")
        self._tabs.addTab(self._tabla_pair, "Pairwise")
        self._tabs.addTab(self._tabla_list, "Listwise")
        self._tabs.addTab(self._tabla_est, "Estándar")
        self._tabs.addTab(self._tabla_aprob, "Aprobadas")
        self._tabs.addTab(self._tabla_rech, "Rechazadas")
        self._tabs.addTab(self._consola, "Consola")

        layout.addWidget(self._tabs, stretch=1)

    def _elegir_carpeta(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self, "Selecciona carpeta con imágenes"
        )
        if ruta:
            self._raiz = Path(ruta)
            self._lbl_ruta.setText(str(self._raiz))
            self._btn_analizar.setEnabled(True)

    def _analizar(self) -> None:
        if self._raiz is None:
            return
        self._btn_analizar.setEnabled(False)
        self._consola.log(
            f"Analizando: {self._raiz} "
            f"(norm={self._combo_norm.currentText()})"
        )
        self._worker = _WorkerPipeline(
            self._raiz, self._combo_norm.currentText(), parent=self
        )
        self._worker.progreso.connect(self._consola.log)
        self._worker.terminado.connect(self._al_terminar)
        self._worker.error.connect(self._al_error)
        self._worker.finished.connect(
            lambda: self._btn_analizar.setEnabled(True)
        )
        self._worker.start()

    def _al_terminar(self, resultado: AnalisisResultado) -> None:
        self._resultado = resultado

        self._tabla_crudo.cargar(resultado.crudo)
        self._tabla_limpio.cargar(resultado.limpio)
        self._tabla_norm.cargar(resultado.normalizado)
        self._tabla_comp.cargar(resultado.comparativa)
        self._tabla_pair.cargar(resultado.pairwise)
        self._tabla_list.cargar(resultado.listwise)

        if resultado.estandar:
            self._tabla_est.cargar(
                pd.DataFrame(resultado.estandar.resumen.get("reglas", []))
            )
            self._tabla_aprob.cargar(resultado.estandar.aprobadas)
            self._tabla_rech.cargar(resultado.estandar.rechazadas)

        self._actualizar_kpis(resultado)
        self._dibujar_graficas(resultado)

        self._consola.log(
            f"Listo: {len(resultado.crudo)} crudas → "
            f"{len(resultado.limpio)} limpias.",
            "ok",
        )
        for b in (self._btn_exportar, self._btn_json, self._btn_csv):
            b.setEnabled(True)

    def _al_error(self, mensaje: str) -> None:
        self._consola.log(mensaje, "error")
        QMessageBox.critical(self, "Error", mensaje)

    def _actualizar_kpis(self, r: AnalisisResultado) -> None:
        m = r.metricas
        self._kpi_crudas.actualizar(m.get("filas_originales", "—"))
        self._kpi_ruido.actualizar(m.get("filas_ruido_eliminadas", "—"))
        self._kpi_limpias.actualizar(m.get("filas_finales", "—"))
        if r.estandar:
            self._kpi_aprobadas.actualizar(
                r.estandar.resumen.get("aprobadas", "—")
            )
            self._kpi_rechazadas.actualizar(
                r.estandar.resumen.get("rechazadas", "—")
            )

    def _exportar_excel(self) -> None:
        if self._resultado is None or self._raiz is None:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar análisis como Excel",
            str(self._raiz / "analisis_imagenes.xlsx"),
            "Excel (*.xlsx)",
        )
        if not ruta:
            return
        try:
            pipeline = PipelineAnalisis()
            pipeline.exportar_excel(self._resultado, Path(ruta))
            self._consola.log(f"Excel guardado: {ruta}", "ok")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error al exportar", str(e))
            self._consola.log(f"Export Excel: {e}", "error")

    def _exportar_json(self) -> None:
        if self._resultado is None or self._raiz is None:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar análisis como JSON",
            str(self._raiz / "analisis_imagenes.json"),
            "JSON (*.json)",
        )
        if not ruta:
            return
        try:
            pipeline = PipelineAnalisis()
            pipeline.exportar_json(self._resultado, Path(ruta))
            self._consola.log(f"JSON guardado: {ruta}", "ok")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error al exportar", str(e))
            self._consola.log(f"Export JSON: {e}", "error")

    def _exportar_csv(self) -> None:
        if self._resultado is None or self._raiz is None:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar comparativas como CSV",
            str(self._raiz / "comparativas.csv"),
            "CSV (*.csv)",
        )
        if not ruta:
            return
        try:
            pipeline = PipelineAnalisis()
            pipeline.exportar_csv(self._resultado, Path(ruta))
            self._consola.log("CSV exportado (pairwise + listwise)", "ok")
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Error al exportar", str(e))
            self._consola.log(f"Export CSV: {e}", "error")

    def _dibujar_graficas(self, r: AnalisisResultado) -> None:
        df = r.limpio if not r.limpio.empty else r.crudo
        if df.empty:
            return

        if "clase" in df.columns:
            conteo = df["clase"].value_counts().to_dict()
            if conteo:
                self._g_dist.pastel(conteo, "Distribución por clase")

        if "brillo_medio" in df.columns and df["brillo_medio"].notna().any():
            s = df.dropna(subset=["brillo_medio"]).sort_values("brillo_medio")
            if len(s) >= 2:
                top = s.tail(5)[["ruta", "brillo_medio"]].copy()
                bot = s.head(5)[["ruta", "brillo_medio"]].copy()
                top["ranking"] = [f"top_{i+1}" for i in range(len(top))]
                bot["ranking"] = [f"bot_{i+1}" for i in range(len(bot))]
                datos = pd.concat([bot, top], ignore_index=True)
                self._g_top.barras(
                    dict(zip(datos["ranking"], datos["brillo_medio"])),
                    "Brillo: bottom 5 vs top 5",
                    horizontal=True,
                )

        columnas_num = [
            c
            for c in (
                "brillo_medio",
                "contraste_rms",
                "varianza_laplaciano",
                "ruido_estimado",
                "colorido",
                "hist_entropia",
                "saturacion_media",
                "tamano_bytes",
            )
            if c in df.columns
        ]
        outliers: dict[str, int] = {}
        for col in columnas_num:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) < 4:
                continue
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers[col] = int(((s < lo) | (s > hi)).sum())
        if outliers:
            self._g_out.barras(
                outliers, "Outliers IQR por columna", horizontal=True
            )

        if {"brillo_medio", "ruido_estimado", "clase"} <= set(df.columns):
            self._g_disp.dispersion(
                df,
                "Brillo vs Ruido (coloreado por clase)",
                x="brillo_medio",
                y="ruido_estimado",
                color_por="clase",
            )

        if r.comparativa is not None and not r.comparativa.empty:
            agrup = (
                r.comparativa.groupby("columna")["delta_%"]
                .apply(lambda x: float(x.abs().mean()))
                .sort_values(ascending=False)
                .head(15)
                .to_dict()
            )
            if agrup:
                self._g_delta.barras(
                    agrup,
                    "Δ% medio absoluto (top 15)",
                    horizontal=True,
                )

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(2000)
        super().closeEvent(event)