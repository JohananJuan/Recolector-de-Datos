from __future__ import annotations

import time
import traceback
from enum import Enum, auto

import cv2
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QScrollArea, QComboBox,
)

from controladores.controlador_captura import ControladorCaptura
from core.sensor import listar_puertos_seriales
from servicios.trigger import ConfigTrigger, EventoTrigger, FaseTrigger
from ui.widgets.consola import Consola
from ui.widgets.tarjeta import Tarjeta
from ui.widgets.video import WidgetVideo


class EstadoVideo(Enum):
    ESPERANDO = auto()
    EN_VIVO = auto()


class VistaCaptura(QWidget):
    RESOLUCION = (1280, 720)
    INTERVALO_AUTO_MS = 3000
    CLASES_COLOR = {
        "papel": (166, 227, 161),
        "carton": (249, 226, 175),
        "tela": (137, 180, 250),
        "—": (148, 160, 180),
    }
    FASE_UI: dict[FaseTrigger, tuple[str, tuple[int, int, int]]] = {
        FaseTrigger.ESPERANDO: ("Esperando objeto…", (148, 160, 180)),
        FaseTrigger.DETECTADO: ("Objeto detectado · acércate", (137, 180, 250)),
        FaseTrigger.CERCA: ("¡Más cerca! Listo para captura", (249, 226, 175)),
        FaseTrigger.CAPTURADO: ("Capturado · retira el objeto", (166, 227, 161)),
    }

    def __init__(self, controlador: ControladorCaptura,
                 config_trigger: ConfigTrigger | None = None):
        super().__init__()
        self._ctrl = controlador
        self._config_trigger = config_trigger or ConfigTrigger()

        self._cap = None
        self._clase_actual = "papel"
        self._modo_auto = False
        self._modo_reconocer = False
        self._auto_capturar_consenso = False
        self._estado_clf = None
        self._ultimo_guardado_auto = 0.0
        self._sensor_activo = False
        self._flash_hasta = 0.0
        self._camara_autoencendida = False
        self._estado_video = EstadoVideo.ESPERANDO

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._loop)
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._capturar_manual)

        self._construir_ui()
        self._aplicar_estado_video(EstadoVideo.ESPERANDO)

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

        sub = QLabel(
            # "ESPACIO captura · 1/2/3 cambia clase · A alterna automático · "
            # "S activa sensor (cámara ON a <40 cm, OFF a >50 cm, captura ≤10 cm)"
        )
        sub.setObjectName("subtitulo")
        layout.addWidget(sub)

        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(12)

        self._video = WidgetVideo(self.RESOLUCION, "Esperando objeto…")
        cuerpo.addWidget(self._video, stretch=4)

        lateral = QVBoxLayout()
        lateral.setSpacing(8)

        self._tarjeta_pred = Tarjeta("Predicción", "—")
        lateral.addWidget(self._tarjeta_pred)
        self._tarjeta_conf = Tarjeta("Confianza", "0%")
        lateral.addWidget(self._tarjeta_conf)
        self._tarjeta_dist = Tarjeta("Distancia", "—")
        lateral.addWidget(self._tarjeta_dist)
        self._lbl_sensor = QLabel("Sensor: inactivo")
        self._lbl_sensor.setObjectName("subtitulo")
        lateral.addWidget(self._lbl_sensor)

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

        layout.addLayout(self._fila_clase())
        layout.addLayout(self._fila_botones())
        layout.addLayout(self._fila_sensor())

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

    def _fila_clase(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        fila.setSpacing(8)
        fila.addWidget(QLabel("Clase actual:"))
        self._lbl_clase = QLabel(self._clase_actual.upper())
        self._lbl_clase.setObjectName("clase_actual")
        fila.addWidget(self._lbl_clase)
        fila.addStretch()
        for tecla, clase in [("1", "papel"), ("2", "carton"), ("3", "tela")]:
            b = QPushButton(f"{tecla} · {clase}")
            b.clicked.connect(lambda _, c=clase: self._set_clase(c))
            fila.addWidget(b)
        return fila

    def _fila_botones(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        fila.setSpacing(8)

        self._btn_iniciar = QPushButton("▶ Iniciar cámara")
        self._btn_iniciar.clicked.connect(self._iniciar_manual)
        self._btn_detener = QPushButton("■ Detener")
        self._btn_detener.setObjectName("peligro")
        self._btn_detener.clicked.connect(self._detener)
        self._btn_detener.setEnabled(False)

        self._btn_captura = QPushButton("Capturar")
        self._btn_captura.setObjectName("exito")
        self._btn_captura.clicked.connect(self._capturar_manual)
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
            fila.addWidget(b)
        fila.addStretch()
        return fila

    def _fila_sensor(self) -> QHBoxLayout:
        fila = QHBoxLayout()
        fila.setSpacing(8)
        fila.addWidget(QLabel("Sensor:"))

        self._combo_puerto = QComboBox()
        self._combo_puerto.setMinimumWidth(180)
        self._refrescar_puertos()
        fila.addWidget(self._combo_puerto)

        btn_refrescar = QPushButton("⟳")
        btn_refrescar.setFixedWidth(40)
        btn_refrescar.setToolTip("Refrescar puertos seriales")
        btn_refrescar.clicked.connect(self._refrescar_puertos)
        fila.addWidget(btn_refrescar)

        self._btn_sensor = QPushButton("S · Activar sensor")
        self._btn_sensor.setCheckable(True)
        self._btn_sensor.clicked.connect(self._toggle_sensor)
        fila.addWidget(self._btn_sensor)

        fila.addStretch()
        return fila

    def _refrescar_puertos(self) -> None:
        self._combo_puerto.clear()
        puertos = listar_puertos_seriales()
        if not puertos:
            self._combo_puerto.addItem("(sin puertos)")
            self._combo_puerto.setEnabled(False)
        else:
            self._combo_puerto.addItems(puertos)
            self._combo_puerto.setEnabled(True)

    def _puerto_seleccionado(self) -> str | None:
        if not self._combo_puerto.isEnabled() or self._combo_puerto.count() == 0:
            self._refrescar_puertos()
        texto = self._combo_puerto.currentText()
        return None if texto in ("", "(sin puertos)") else texto

    def _set_clase(self, clase: str) -> None:
        self._clase_actual = clase
        self._lbl_clase.setText(clase.upper())
        self._consola.log(f"Clase activa: {clase}")
        if self._sensor_activo:
            if self._ctrl.habilitar_auto(clase, puerto=self._puerto_seleccionado()):
                self._consola.log(f"Sensor reasignado a clase: {clase}", "ok")
            else:
                self._sensor_activo = False
                self._btn_sensor.setChecked(False)
                self._btn_sensor.setText("S · Activar sensor")
                self._consola.log("Sensor se desconectó al cambiar clase.", "warn")

    def _aplicar_estado_video(self, estado: EstadoVideo) -> None:
        self._estado_video = estado
        if estado == EstadoVideo.ESPERANDO:
            mensaje = (
                "Esperando objeto…"
                if self._sensor_activo
                else "Cámara detenida"
            )
            self._video.mostrar_espera(mensaje)

    def _iniciar_manual(self) -> None:
        self._iniciar_camara()
        if self._cap is not None:
            self._consola.log("Cámara iniciada.", "ok")

    def _iniciar_camara(self) -> None:
        if self._cap is not None:
            return
        try:
            self._cap = cv2.VideoCapture(0)
            if not self._cap.isOpened():
                self._consola.log("No se pudo abrir la cámara.", "error")
                self._cap = None
                return
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.RESOLUCION[0])
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.RESOLUCION[1])
            self._estado_video = EstadoVideo.EN_VIVO
            if not self._timer.isActive():         
                self._timer.start(30)
            self._btn_iniciar.setEnabled(False)
            self._btn_detener.setEnabled(True)
            self._btn_captura.setEnabled(True)
            self._btn_auto.setEnabled(True)
            self._btn_reconocer.setEnabled(True)
        except Exception as e:
            traceback.print_exc()
            self._consola.log(f"Error al iniciar cámara: {e}", "error")

    def _detener(self) -> None:
        try:
            self._timer.stop()
            self._auto_timer.stop()
        except Exception:
            pass

        self._modo_auto = False
        self._modo_reconocer = False
        self._btn_auto.setText("A · Auto")
        self._btn_reconocer.setText("Reconocer")
        self._btn_consenso.setChecked(False)

        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

        self._btn_iniciar.setEnabled(True)
        self._btn_detener.setEnabled(False)
        self._btn_captura.setEnabled(False)
        self._btn_auto.setEnabled(False)
        self._btn_reconocer.setEnabled(False)
        self._btn_consenso.setEnabled(False)
        self._aplicar_estado_video(EstadoVideo.ESPERANDO)
        self._tarjeta_dist.actualizar("—")
        if not self._sensor_activo:
            self._lbl_sensor.setText("Sensor: inactivo")
        self._camara_autoencendida = False
        self._consola.log("Cámara detenida.")

    def _toggle_sensor(self) -> None:
        if self._sensor_activo:
            self._ctrl.deshabilitar_auto()
            self._sensor_activo = False
            self._btn_sensor.setText("S · Activar sensor")
            self._tarjeta_dist.actualizar("—")
            self._lbl_sensor.setText("Sensor: inactivo")
            self._consola.log("Sensor ultrasónico desactivado.")
            if self._camara_autoencendida:
                self._detener()
            else:
                self._aplicar_estado_video(EstadoVideo.ESPERANDO)
            return

        puerto = self._puerto_seleccionado()
        self._consola.log(f"Activando sensor (puerto={puerto or 'auto'})...")
        if self._ctrl.habilitar_auto(self._clase_actual, puerto=puerto):
            self._sensor_activo = True
            self._btn_sensor.setText("S · Sensor ✔ (auto)")
            self._consola.log(
                "Sensor activo. Cámara ON a <40 cm, OFF a >50 cm. "
                "Captura cada 1 s a ≤10 cm.", "ok",
            )
            self._aplicar_estado_video(EstadoVideo.ESPERANDO)
            self._timer.start(30)
        else:
            self._sensor_activo = False
            self._btn_sensor.setChecked(False)
            self._consola.log(
                "No se pudo activar el sensor. ¿Puerto ocupado o ESP32 desconectada?",
                "error",
            )

    def _loop(self) -> None:
        try:
            frame = None
            if self._cap is not None and self._estado_video == EstadoVideo.EN_VIVO:
                ret, frame_leido = self._cap.read()
                if ret:
                    frame = cv2.resize(frame_leido, self.RESOLUCION)

            evento = self._ctrl.procesar_frame_auto(frame)
            self._reaccionar_evento(evento)
            self._actualizar_estado_sensor()

            if self._estado_video != EstadoVideo.EN_VIVO or frame is None:
                return

            if self._modo_reconocer:
                self._estado_clf = self._ctrl.clasificar(frame)
                self._actualizar_paneles()
                self._tal_vez_auto_capturar(frame)

            frame = self._dibujar_hud(self._aplicar_flash(frame))
            self._video.mostrar_frame(frame)
        except Exception:
            print("[CRASH] _loop falló:")
            traceback.print_exc()
            self._timer.stop()

    def _reaccionar_evento(self, evento: EventoTrigger | None) -> None:
        if evento == EventoTrigger.CAPTURAR:
            self._flash_hasta = time.time() + 0.15
            self._refrescar_conteo()
            self._consola.log("[sensor] Captura automática", "ok")
        elif evento == EventoTrigger.ACTIVAR:
            if self._cap is None:
                self._consola.log("🎥 Objeto detectado → encendiendo cámara.", "ok")
                self._iniciar_camara()
                self._camara_autoencendida = True
        elif evento == EventoTrigger.DESACTIVAR:
            self._consola.log("[sensor] Objeto fuera de rango → apagando cámara.")
            if self._camara_autoencendida:
                self._detener_camara_auto()

    def _detener_camara_auto(self) -> None:
        try:
            self._timer.stop()
        except Exception:
            pass
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None
        self._aplicar_estado_video(EstadoVideo.ESPERANDO)
        self._btn_iniciar.setEnabled(True)
        self._btn_detener.setEnabled(False)
        self._btn_captura.setEnabled(False)
        self._btn_auto.setEnabled(False)
        self._btn_reconocer.setEnabled(False)
        self._btn_consenso.setEnabled(False)
        self._tarjeta_dist.actualizar("—")
        self._camara_autoencendida = False
        self._consola.log("Cámara apagada automáticamente.", "warn")
        if self._sensor_activo:
            self._timer.start(30)

    def _actualizar_estado_sensor(self) -> None:
        if not self._sensor_activo:
            return
        lectura = self._ctrl.lectura_sensor()
        if lectura and lectura.valida:
            self._tarjeta_dist.actualizar(f"{lectura.distancia_cm:.1f} cm")
            fase = self._ctrl.fase_auto()
            texto, _ = self.FASE_UI.get(fase, ("Sensor: —", (255, 255, 255)))
            self._lbl_sensor.setText(texto)
        else:
            self._tarjeta_dist.actualizar("—")
            self._lbl_sensor.setText("Sensor: sin lectura")

    def _aplicar_flash(self, frame):
        if time.time() >= self._flash_hasta:
            return frame
        flash = frame.copy()
        cv2.rectangle(flash, (0, 0), self.RESOLUCION, (255, 255, 255), -1)
        return cv2.addWeighted(frame, 0.3, flash, 0.7, 0)

    def _dibujar_hud(self, frame):
        alto, ancho = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (ancho, 130), (30, 30, 30), -1)
        cv2.putText(frame, f"Clase: {self._clase_actual.upper()}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        modos = []
        if self._modo_auto:
            modos.append("AUTO-TIEMPO")
        if self._sensor_activo:
            modos.append("SENSOR")
        texto_modo = " + ".join(modos) if modos else "MANUAL"
        color_modo = (0, 200, 255) if modos else (200, 200, 200)
        cv2.putText(frame, f"Modo: {texto_modo}", (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_modo, 2)

        if self._sensor_activo:
            lectura = self._ctrl.lectura_sensor()
            if lectura and lectura.valida:
                fase = self._ctrl.fase_auto()
                _, color = self.FASE_UI.get(fase, ("", (255, 255, 255)))
                cv2.putText(frame,
                            f"{lectura.distancia_cm:.1f} cm | {lectura.estado}",
                            (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            color, 2)
            else:
                cv2.putText(frame, "--- cm | sin lectura", (20, 110),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (243, 139, 168), 2)

        if self._modo_reconocer and self._estado_clf:
            clase = self._estado_clf.clase
            color = self.CLASES_COLOR.get(clase, (200, 200, 200))
            cv2.putText(frame,
                        f"Pred: {clase} ({self._estado_clf.confianza*100:.0f}%)",
                        (20, alto - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
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

    def _capturar_manual(self) -> None:
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
        self._consola.log(
            f"Auto-captura por consenso {'activada' if activo else 'desactivada'}."
        )

    def _refrescar_conteo(self) -> None:
        conteo = self._ctrl.contar_por_clase()
        for clase, tarjeta in self._tarjetas.items():
            tarjeta.actualizar(str(conteo.get(clase, 0)))

    def closeEvent(self, event) -> None:
        try:
            self._timer.stop()
            self._auto_timer.stop()
        except Exception:
            pass
        try:
            if self._sensor_activo:
                self._ctrl.deshabilitar_auto()
                self._sensor_activo = False
        except Exception:
            pass
        try:
            if self._cap:
                self._cap.release()
                self._cap = None
        except Exception:
            pass
        time.sleep(0.3)
        super().closeEvent(event)