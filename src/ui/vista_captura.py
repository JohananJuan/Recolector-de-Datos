import time

import cv2
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QScrollArea, QSizePolicy,
)

from controladores.controlador_captura import ControladorCaptura
from ui.widgets.consola import Consola
from ui.widgets.tarjeta import Tarjeta


class VistaCaptura(QWidget):
    RESOLUCION = (1280, 720)
    INTERVALO_AUTO_MS = 3000
    CLASES_COLOR = {
        "papel": (166, 227, 161),
        "carton": (249, 226, 175),
        "tela": (137, 180, 250),
        "—": (148, 160, 180),
    }

    def __init__(self, controlador: ControladorCaptura):
        super().__init__()
        self._ctrl = controlador
        self._cap = None
        self._clase_actual = "papel"
        self._modo_auto = False
        self._modo_reconocer = False
        self._auto_capturar_consenso = False
        self._estado_clf = None
        self._ultimo_guardado_auto = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._loop)
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._capturar)
        self._construir_ui()

    def _construir_ui(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(12)

        titulo = QLabel("Captura en vivo")
        titulo.setObjectName("titulo")
        layout.addWidget(titulo)

        sub = QLabel("ESPACIO captura · 1/2/3 cambia clase · A alterna automático")
        sub.setObjectName("subtitulo")
        layout.addWidget(sub)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)

        self._video = QLabel("Cámara detenida")
        self._video.setAlignment(Qt.AlignCenter)
        self._video.setMinimumSize(720, 405)
        self._video.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._video.setStyleSheet(
            "background:#11111b; border:1px solid #313244; border-radius:8px; color:#6c7086;"
        )
        cuerpo.addWidget(self._video, stretch=4)

        lateral = QVBoxLayout()
        lateral.setSpacing(8)

        self._tarjeta_pred = Tarjeta("Predicción", "—")
        lateral.addWidget(self._tarjeta_pred)

        self._tarjeta_conf = Tarjeta("Confianza", "0%")
        lateral.addWidget(self._tarjeta_conf)

        lbl = QLabel("Capturas por clase")
        lbl.setObjectName("subtitulo")
        lateral.addWidget(lbl)

        self._tarjetas: dict[str, Tarjeta] = {}
        for clase in self._ctrl.clases:
            t = Tarjeta(clase.capitalize(), "0")
            self._tarjetas[clase] = t
            lateral.addWidget(t)

        lateral.addStretch()
        cuerpo.addLayout(lateral, stretch=1)

        layout.addLayout(cuerpo)

        fila_clase = QHBoxLayout()
        fila_clase.setSpacing(8)
        fila_clase.addWidget(QLabel("Clase actual:"))
        self._lbl_clase = QLabel(self._clase_actual.upper())
        self._lbl_clase.setObjectName("clase_actual")
        fila_clase.addWidget(self._lbl_clase)
        fila_clase.addStretch()

        for tecla, clase in [("1", "papel"), ("2", "carton"), ("3", "tela")]:
            b = QPushButton(f"{tecla} · {clase}")
            b.clicked.connect(lambda _, c=clase: self._set_clase(c))
            fila_clase.addWidget(b)

        layout.addLayout(fila_clase)

        controles = QHBoxLayout()
        controles.setSpacing(8)
        self._btn_iniciar = QPushButton("▶ Iniciar cámara")
        self._btn_iniciar.clicked.connect(self._iniciar)
        self._btn_detener = QPushButton("■ Detener")
        self._btn_detener.setObjectName("peligro")
        self._btn_detener.clicked.connect(self._detener)
        self._btn_detener.setEnabled(False)

        self._btn_captura = QPushButton("Capturar")
        self._btn_captura.setObjectName("exito")
        self._btn_captura.clicked.connect(self._capturar)
        self._btn_captura.setEnabled(False)

        self._btn_auto = QPushButton("A · Auto")
        self._btn_auto.clicked.connect(self._toggle_auto)
        self._btn_auto.setEnabled(False)

        self._btn_reconocer = QPushButton("Reconocer")
        self._btn_reconocer.clicked.connect(self._toggle_reconocer)
        self._btn_reconocer.setEnabled(False)
        if not self._ctrl.tiene_modelo():
            self._btn_reconocer.setToolTip(
                "No hay modelo en models/. Copia clasificador.pt (YOLO) "
                "o mobilenet_v3.pth y reinicia la app."
            )

        self._btn_consenso = QPushButton("Auto-captura")
        self._btn_consenso.setCheckable(True)
        self._btn_consenso.toggled.connect(self._toggle_consenso)
        self._btn_consenso.setEnabled(False)

        for b in (self._btn_iniciar, self._btn_detener, self._btn_captura,
                  self._btn_auto, self._btn_reconocer, self._btn_consenso):
            controles.addWidget(b)
        controles.addStretch()
        layout.addLayout(controles)

        grupo = QGroupBox("Registro")
        gl = QVBoxLayout(grupo)
        self._consola = Consola()
        self._consola.setMinimumHeight(120)
        gl.addWidget(self._consola)
        layout.addWidget(grupo)

        layout.addStretch()

        scroll.setWidget(contenido)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        self._refrescar_conteo()
        if self._ctrl.tiene_modelo():
            self._consola.log("Modelo cargado.", "ok")
        else:
            self._consola.log("Sin modelo. Captura manual disponible.", "warn")

    def _set_clase(self, clase: str) -> None:
        self._clase_actual = clase
        self._lbl_clase.setText(clase.upper())
        self._consola.log(f"Clase activa: {clase}")

    def _iniciar(self) -> None:
        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._consola.log("No se pudo abrir la cámara.", "error")
            self._cap = None
            return
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.RESOLUCION[0])
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.RESOLUCION[1])
        self._timer.start(30)
        self._btn_iniciar.setEnabled(False)
        self._btn_detener.setEnabled(True)
        self._btn_captura.setEnabled(True)
        self._btn_auto.setEnabled(True)
        self._btn_reconocer.setEnabled(True)
        self._consola.log("Cámara iniciada.", "ok")

    def _detener(self) -> None:
        self._timer.stop()
        self._auto_timer.stop()
        self._modo_auto = False
        self._modo_reconocer = False
        self._btn_auto.setText("A · Auto")
        self._btn_reconocer.setText("Reconocer")
        self._btn_consenso.setChecked(False)
        if self._cap:
            self._cap.release()
            self._cap = None
        self._btn_iniciar.setEnabled(True)
        self._btn_detener.setEnabled(False)
        self._btn_captura.setEnabled(False)
        self._btn_auto.setEnabled(False)
        self._btn_reconocer.setEnabled(False)
        self._btn_consenso.setEnabled(False)
        self._video.setText("Cámara detenida")
        self._consola.log("Cámara detenida.")

    def _loop(self) -> None:
        if not self._cap:
            return
        ret, frame = self._cap.read()
        if not ret:
            return
        frame = cv2.resize(frame, self.RESOLUCION)

        if self._modo_reconocer:
            self._estado_clf = self._ctrl.clasificar(frame)
            self._actualizar_paneles()
            self._tal_vez_auto_capturar(frame)

        frame = self._dibujar_hud(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self._video.setPixmap(QPixmap.fromImage(img).scaled(
            self._video.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _dibujar_hud(self, frame):
        alto, ancho = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (ancho, 90), (30, 30, 30), -1)
        cv2.putText(frame, f"Clase: {self._clase_actual.upper()}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.putText(frame, f"Modo: {'AUTO' if self._modo_auto else 'MANUAL'}", (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

        if self._modo_reconocer and self._estado_clf:
            clase = self._estado_clf.clase
            color = self.CLASES_COLOR.get(clase, (200, 200, 200))
            texto = f"Pred: {clase} ({self._estado_clf.confianza*100:.0f}%)"
            cv2.putText(frame, texto, (20, alto - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            barra_w = int((ancho - 40) * self._estado_clf.confianza)
            cv2.rectangle(frame, (20, alto - 45),
                          (20 + barra_w, alto - 30), color, -1)
            cv2.rectangle(frame, (20, alto - 45),
                          (ancho - 20, alto - 30), (80, 80, 80), 1)
        return frame

    def _actualizar_paneles(self) -> None:
        if not self._estado_clf:
            return
        subt = "estable ✔" if self._estado_clf.estable else ""
        self._tarjeta_pred.actualizar(self._estado_clf.clase, subt)
        self._tarjeta_conf.actualizar(f"{self._estado_clf.confianza*100:.0f}%")

    def _tal_vez_auto_capturar(self, frame) -> None:
        if not self._auto_capturar_consenso:
            return
        if not self._estado_clf or not self._estado_clf.estable:
            return
        ahora = time.time()
        if ahora - self._ultimo_guardado_auto < 2.0:
            return
        clase = self._estado_clf.clase
        ruta = self._ctrl.guardar(frame, clase)
        if ruta:
            self._consola.log(f"[auto] {clase} → {ruta.name}", "ok")
            self._refrescar_conteo()
            self._ultimo_guardado_auto = ahora

    def _capturar(self) -> None:
        if not self._cap:
            return
        ret, frame = self._cap.read()
        if not ret:
            self._consola.log("Frame no disponible.", "warn")
            return
        frame = cv2.resize(frame, self.RESOLUCION)
        clase = self._clase_actual
        if self._modo_reconocer and self._estado_clf and self._estado_clf.clase != "—":
            clase = self._estado_clf.clase
        ruta = self._ctrl.guardar(frame, clase)
        if ruta:
            self._consola.log(f"Guardado: {ruta.name}", "ok")
            self._refrescar_conteo()
        else:
            self._consola.log("Falló el guardado.", "error")

    def _toggle_auto(self) -> None:
        self._modo_auto = not self._modo_auto
        if self._modo_auto:
            self._auto_timer.start(self.INTERVALO_AUTO_MS)
            self._consola.log("Automático activado (cada 3s).", "warn")
            self._btn_auto.setText("A · Auto ✔")
        else:
            self._auto_timer.stop()
            self._consola.log("Automático desactivado.")
            self._btn_auto.setText("A · Auto")

    def _toggle_reconocer(self) -> None:
        self._modo_reconocer = not self._modo_reconocer
        if self._modo_reconocer:
            self._btn_reconocer.setText("Reconocer ✔")
            self._btn_consenso.setEnabled(True)
            self._consola.log("Reconocimiento activado.", "warn")
        else:
            self._btn_reconocer.setText("Reconocer")
            self._btn_consenso.setEnabled(False)
            self._btn_consenso.setChecked(False)
            self._ctrl.reiniciar_clasificacion()
            self._tarjeta_pred.actualizar("—")
            self._tarjeta_conf.actualizar("0%")
            self._consola.log("Reconocimiento desactivado.")

    def _toggle_consenso(self, activo: bool) -> None:
        self._auto_capturar_consenso = activo
        self._consola.log(f"Auto-captura por consenso {'activada' if activo else 'desactivada'}.")

    def _refrescar_conteo(self) -> None:
        conteo = self._ctrl.contar_por_clase()
        for clase, tarjeta in self._tarjetas.items():
            tarjeta.actualizar(str(conteo.get(clase, 0)))

    def closeEvent(self, event) -> None:
        self._detener()
        super().closeEvent(event)