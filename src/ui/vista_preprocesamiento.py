from __future__ import annotations

from pathlib import Path

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from limpieza.registro import registro_etapas
from ui.widgets.consola import Consola
from ui.widgets.tabla_datos import TablaDatos
from ui.widgets.tarjeta import TarjetaEtapa

GRUPOS = {
    "Fundamentos": ["legal", "texto"],
    "Estructurados": [
        "limpieza",
        "correlacion",
        "score_calidad",
        "normalizacion",
        "discretizacion",
    ],
    "No estructurados": ["redimensionado", "mejora", "caracteristicas"],
}


class _Tarea(QThread):
    terminado = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            self.terminado.emit(self._fn())
        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")


class _DialogoAntesDespues(QDialog):
    def __init__(
        self, titulo: str, antes: pd.DataFrame, despues: pd.DataFrame, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(1100, 600)
        lay = QVBoxLayout(self)
        tabs = QTabWidget()

        a = antes.select_dtypes("number").mean()
        d = despues.select_dtypes("number").mean()
        cmp = pd.concat([a.rename("antes"), d.rename("después")], axis=1)
        cmp["delta_%"] = (
            (cmp["después"] - cmp["antes"]) / (cmp["antes"].abs() + 1e-9) * 100
        )
        t_cmp = TablaDatos()
        t_cmp.cargar(cmp.rename_axis("columna").reset_index())
        tabs.addTab(t_cmp, "Medias antes → después")
        for nombre, df in (("Antes", antes), ("Después", despues)):
            t = TablaDatos()
            t.cargar(df)
            tabs.addTab(t, f"{nombre} ({len(df)} filas)")
        lay.addWidget(tabs)


class VistaPreprocesamiento(QWidget):
    _senal_log = pyqtSignal(str, str)
    _senal_progreso = pyqtSignal(int, int, str)

    def __init__(self, controlador, parent=None):
        super().__init__(parent)
        self.controlador = controlador
        self.tarjetas: dict[str, TarjetaEtapa] = {}
        self._tarea: _Tarea | None = None

        self.controlador.conectar(self._senal_log.emit, self._senal_progreso.emit)
        self._senal_log.connect(self._on_log)
        self._senal_progreso.connect(self.actualizar_progreso)
        self._construir_ui()

    def _construir_ui(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(18, 18, 18, 18)
        raiz.setSpacing(12)

        titulo = QLabel("Preprocesamiento de datos no estructurados")
        titulo.setObjectName("titulo")
        sub = QLabel(
            "Elige una carpeta, ajusta cada etapa y ejecútalas una por una "
            "(vista previa) o todas en el orden del temario."
        )
        sub.setObjectName("subtitulo")
        raiz.addWidget(titulo)
        raiz.addWidget(sub)

        fila = QHBoxLayout()
        self._lbl_ruta = QLabel("Sin carpeta seleccionada")
        self._lbl_ruta.setObjectName("rutaSeleccionada")
        self._btn_carpeta = QPushButton("1 · Elegir carpeta…")
        self._btn_carpeta.clicked.connect(self._elegir_carpeta)
        self._btn_todo = QPushButton("2 · Ejecutar etapas activas")
        self._btn_todo.setObjectName("exito")
        self._btn_todo.setEnabled(False)
        self._btn_todo.setToolTip("Primero elige una carpeta")
        self._btn_todo.clicked.connect(self._ejecutar_todo)
        fila.addWidget(self._lbl_ruta, stretch=1)
        fila.addWidget(self._btn_carpeta)
        fila.addWidget(self._btn_todo)
        raiz.addLayout(fila)

        self.lbl_etapa = QLabel("Listo.")
        self.progreso = QProgressBar()
        self.progreso.setRange(0, 1)
        self.progreso.setValue(0)
        self.progreso.setFormat("Etapa %v/%m")
        raiz.addWidget(self.lbl_etapa)
        raiz.addWidget(self.progreso)

        self._tabs = QTabWidget()
        for grupo, claves in GRUPOS.items():
            self._tabs.addTab(self._tab(claves), grupo)
        raiz.addWidget(self._tabs, stretch=1)

        grupo = QGroupBox("Registro")
        gl = QVBoxLayout(grupo)
        self._consola = Consola()
        self._consola.setMaximumHeight(140)
        gl.addWidget(self._consola)
        raiz.addWidget(grupo)

    def _tab(self, claves: list[str]) -> QWidget:
        contenedor = QWidget()
        v = QVBoxLayout(contenedor)
        for clave in claves:
            instancia = registro_etapas[clave]()
            tarjeta = TarjetaEtapa(
                clave=clave,
                tema=instancia.tema,
                nombre=instancia.nombre,
                descripcion=instancia.descripcion(),
                parametros=instancia.parametros,
                on_toggle=self.controlador.toggle_etapa,
                on_ejecutar=self._ejecutar_una,
                on_reset=self._restablecer,
                on_ver=self._ver,
            )
            self.tarjetas[clave] = tarjeta
            v.addWidget(tarjeta)
        v.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(contenedor)
        return scroll

    def config_etapas(self):
        self._sincronizar()
        return self.controlador.config_activa()

    def _sincronizar(self) -> None:
        for clave, t in self.tarjetas.items():
            self.controlador.set_parametros(clave, t.parametros_actuales())

    def _ocupado(self, si: bool) -> None:
        self._btn_carpeta.setEnabled(not si)
        self._btn_todo.setEnabled(not si and self.controlador.tiene_datos())
        self._tabs.setEnabled(not si)

    def _lanzar(self, fn, al_terminar, mensaje: str) -> None:
        if self._tarea is not None and self._tarea.isRunning():
            return
        self._ocupado(True)
        self._consola.log(mensaje)
        self._tarea = _Tarea(fn, self)
        self._tarea.terminado.connect(al_terminar)
        self._tarea.error.connect(self._al_error)
        self._tarea.finished.connect(lambda: self._ocupado(False))
        self._tarea.start()

    def _hay_datos(self) -> bool:
        if self.controlador.tiene_datos():
            return True
        QMessageBox.information(
            self,
            "Falta la carpeta",
            "Primero elige una carpeta con imágenes (paso 1).",
        )
        return False

    def _elegir_carpeta(self) -> None:
        ruta = QFileDialog.getExistingDirectory(self, "Selecciona carpeta con imágenes")
        if ruta:
            self._lanzar(
                lambda: self.controlador.cargar_carpeta(Path(ruta)),
                self._carpeta_cargada,
                f"Leyendo imágenes de {ruta}…",
            )

    def _carpeta_cargada(self, n: int) -> None:
        self._lbl_ruta.setText(str(self.controlador.raiz))
        self._btn_todo.setToolTip("")
        self._consola.log(f"{n} imágenes leídas.", "ok" if n else "warn")

    def _ejecutar_una(self, clave: str) -> None:
        if not self._hay_datos():
            return
        self._sincronizar()
        self._lanzar(
            lambda: self.controlador.ejecutar_solo(clave),
            lambda r: self._mostrar_una(clave, r),
            f"Ejecutando {clave}…",
        )

    def _ver(self, clave: str) -> None:
        if not self._hay_datos():
            return
        self._sincronizar()

        def listo(res):
            self._mostrar_una(clave, res)
            antes = res.df_antes.copy() if res.df_antes is not None else res.df.copy()
            despues = res.df.copy()
            _DialogoAntesDespues(
                f"{res.tema} {res.nombre}", antes, despues, self
            ).exec_()

        self._lanzar(
            lambda: self.controlador.ejecutar_solo(clave),
            listo,
            f"Calculando antes/después de {clave}…",
        )

    def _restablecer(self, clave: str) -> None:
        defaults = self.controlador.reset_etapa(clave)
        self.tarjetas[clave].establecer_parametros(defaults)

    def _ejecutar_todo(self) -> None:
        if not self._hay_datos():
            return
        self._sincronizar()
        self._lanzar(
            self.controlador.ejecutar_todo,
            self._todo_listo,
            "Ejecutando etapas activas…",
        )

    def _mostrar_una(self, clave: str, res) -> None:
        self.mostrar_resultado(clave, res)
        self._consola.log(f"[{res.tema}] {res.mensaje}", "ok" if res.ok else "error")

    def _todo_listo(self, pares) -> None:
        if not pares:
            self._consola.log("No hay etapas activas.", "warn")
            return
        for clave, res in pares:
            self.mostrar_resultado(clave, res)
        raiz = self.controlador.raiz
        salida = raiz.parent / f"{raiz.name}_preprocesado"
        fallidas = [c for c, r in pares if not r.ok]
        self._consola.log(
            f"{len(pares)} etapas ({len(fallidas)} con error). "
            f"Imágenes procesadas en: {salida}",
            "warn" if fallidas else "ok",
        )

    def _on_log(self, tema: str, msg: str) -> None:
        self._consola.log(f"[{tema}] {msg}")

    def _al_error(self, msg: str) -> None:
        self._consola.log(msg, "error")
        QMessageBox.critical(self, "Error", msg)

    def actualizar_progreso(self, i: int, n: int, etapa: str) -> None:
        self.progreso.setMaximum(max(n, 1))
        self.progreso.setValue(i)
        self.lbl_etapa.setText(f"Ejecutando: {etapa}")

    def mostrar_resultado(self, clave: str, res) -> None:
        if clave in self.tarjetas and res:
            self.tarjetas[clave].mostrar_resultado(res)
