from __future__ import annotations

import time
import traceback
from typing import Callable, Optional

from core.sensor import FuenteDistancia, LecturaSensor
from servicios.trigger import (
    EstrategiaTrigger,
    EventoTrigger,
    FaseTrigger,
)


CallbackCaptura = Callable[[object], bool]


class ServicioCapturaAutomatica:
    def __init__(
        self,
        fuente: FuenteDistancia,
        trigger: EstrategiaTrigger,
    ):
        self._fuente = fuente
        self._trigger = trigger

    @property
    def fase(self) -> FaseTrigger:
        return self._trigger.fase

    def lectura_actual(self) -> Optional[LecturaSensor]:
        return self._fuente.ultima_lectura()

    def iniciar(self) -> bool:
        return self._fuente.iniciar()

    def detener(self) -> None:
        self._fuente.detener()

    def reset(self) -> None:
        self._trigger.reset()

    def procesar_frame(
        self,
        frame: object,
        callback_captura: CallbackCaptura,
        ahora: Optional[float] = None,
    ) -> Optional[EventoTrigger]:
        ahora = ahora if ahora is not None else time.time()
        try:
            lectura = self._fuente.ultima_lectura()
            evento = self._trigger.procesar(lectura, ahora)
            if evento is None:
                return None
            if evento == EventoTrigger.CAPTURAR:
                if frame is None:
                    return None
                if not callback_captura(frame):
                    return None
            return evento
        except Exception:
            print("[CRASH] procesar_frame falló:")
            traceback.print_exc()
            return None