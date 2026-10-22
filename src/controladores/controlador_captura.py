from __future__ import annotations

from pathlib import Path
from typing import Optional

from core.rutas import CAPTURAS_DIR, METADATA_CAPTURAS, CLASES_VALIDAS
from core.puerto_sensor import crear_fuente_distancia
from core.sensor import LecturaSensor
from metadata.repositorio import nuevo_repositorio
from servicios.captura import ServicioCaptura
from servicios.captura_automatica import ServicioCapturaAutomatica
from servicios.clasificacion.factory import crear_clasificador
from servicios.clasificacion.servicio import (
    ServicioClasificacion,
    EstadoClasificacion,
)
from servicios.trigger import (
    ConfigTrigger,
    EventoTrigger,
    FaseTrigger,
    TriggerPorDistancia,
)


class ControladorCaptura:
    def __init__(
        self,
        modelo_preferido: str = "yolo",
        config_trigger: Optional[ConfigTrigger] = None,
    ):
        self._repo = nuevo_repositorio()
        self._captura = ServicioCaptura(
            self._repo, METADATA_CAPTURAS, camara="webcam_0"
        )
        self._clasificacion = ServicioClasificacion(
            crear_clasificador(modelo_preferido)
        )
        self._auto: Optional[ServicioCapturaAutomatica] = None
        self._config_trigger = config_trigger or ConfigTrigger()
        self._clase_auto: str = CLASES_VALIDAS[0]
        self._auto_habilitado: bool = False

    def guardar(self, frame, clase: str) -> Optional[Path]:
        return self._captura.guardar(frame, clase)

    def contar_por_clase(self) -> dict[str, int]:
        return self._captura.contar_por_clase()

    def sesion_actual(self) -> str:
        return self._captura.sesion

    def clasificar(self, frame) -> EstadoClasificacion:
        return self._clasificacion.procesar(frame)

    def reiniciar_clasificacion(self) -> None:
        self._clasificacion.reset()

    def tiene_modelo(self) -> bool:
        return self._clasificacion.tiene_modelo

    def habilitar_auto(
        self,
        clase: Optional[str] = None,
        puerto: Optional[str] = None,
    ) -> bool:
        if clase:
            if clase not in CLASES_VALIDAS:
                raise ValueError(f"Clase inválida: {clase}")
            self._clase_auto = clase

        print(f"[CTRL] habilitar_auto(clase={self._clase_auto!r}, puerto={puerto!r})")

        if self._auto is not None:
            self._cerrar_sensor_silencioso()

        fuente = crear_fuente_distancia(puerto_preferido=puerto)
        trigger = TriggerPorDistancia(self._config_trigger)
        self._auto = ServicioCapturaAutomatica(fuente, trigger)

        ok = self._auto.iniciar()
        self._auto_habilitado = ok
        print(f"[CTRL] habilitar_auto → {ok}")
        return ok

    def deshabilitar_auto(self) -> None:
        print("[CTRL] deshabilitar_auto()")
        self._auto_habilitado = False
        self._cerrar_sensor_silencioso()
        print("[CTRL] deshabilitar_auto() → OK")

    def auto_habilitado(self) -> bool:
        return self._auto_habilitado

    def fase_auto(self) -> Optional[FaseTrigger]:
        return self._auto.fase if self._auto is not None else None

    def lectura_sensor(self) -> Optional[LecturaSensor]:
        return self._auto.lectura_actual() if self._auto is not None else None

    def procesar_frame_auto(self, frame) -> Optional[EventoTrigger]:
        if not self._auto_habilitado or self._auto is None:
            return None
        return self._auto.procesar_frame(
            frame, callback_captura=self._capturar_auto
        )

    def _capturar_auto(self, frame) -> bool:
        ruta = self._captura.guardar(frame, self._clase_auto)
        if ruta:
            print(f"[AUTO-SENSOR] Guardado: {ruta.name} ({self._clase_auto})")
            return True
        return False

    def _cerrar_sensor_silencioso(self) -> None:
        if self._auto is None:
            return
        try:
            self._auto.detener()
        except Exception as e:
            print(f"[CTRL] Error al detener sensor: {e}")
        self._auto = None

    @property
    def clases(self) -> tuple[str, ...]:
        return CLASES_VALIDAS

    @property
    def directorio(self) -> Path:
        return CAPTURAS_DIR