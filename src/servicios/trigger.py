from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from core.sensor import LecturaSensor


class EventoTrigger(Enum):
    ACTIVAR = auto()
    CAPTURAR = auto()
    DESACTIVAR = auto()


class FaseTrigger(Enum):
    ESPERANDO = auto()
    DETECTADO = auto()
    CERCA = auto()
    CAPTURADO = auto()


@dataclass(frozen=True)
class ConfigTrigger:
    dist_deteccion_cm: float = 40.0
    dist_cerca_cm: float = 25.0
    dist_captura_cm: float = 10.0
    dist_apagado_cm: float = 50.0
    lecturas_estables: int = 3
    cooldown_s: float = 1.0
    timeout_sin_lectura_s: float = 5.0

    def __post_init__(self):
        if not (self.dist_captura_cm < self.dist_cerca_cm < self.dist_deteccion_cm):
            raise ValueError(
                "Debe cumplirse dist_captura_cm < dist_cerca_cm < dist_deteccion_cm"
            )
        if self.dist_apagado_cm <= self.dist_deteccion_cm:
            raise ValueError(
                "dist_apagado_cm debe ser mayor que dist_deteccion_cm"
            )
        if self.lecturas_estables < 1:
            raise ValueError("lecturas_estables debe ser >= 1")


class EstrategiaTrigger(ABC):
    @abstractmethod
    def procesar(
        self, lectura: Optional[LecturaSensor], ahora: float
    ) -> Optional[EventoTrigger]:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...

    @property
    @abstractmethod
    def fase(self) -> FaseTrigger:
        ...


class TriggerPorDistancia(EstrategiaTrigger):
    def __init__(self, config: Optional[ConfigTrigger] = None):
        self._cfg = config or ConfigTrigger()
        self._fase = FaseTrigger.ESPERANDO
        self._candidata: Optional[FaseTrigger] = None
        self._contador = 0
        self._ultima_foto = 0.0
        self._ultima_lectura_valida = 0.0

    @property
    def fase(self) -> FaseTrigger:
        return self._fase

    def reset(self) -> None:
        self._fase = FaseTrigger.ESPERANDO
        self._candidata = None
        self._contador = 0
        self._ultima_foto = 0.0
        self._ultima_lectura_valida = 0.0

    def procesar(
        self, lectura: Optional[LecturaSensor], ahora: float
    ) -> Optional[EventoTrigger]:
        if lectura is None or not lectura.valida:
            return self._manejar_sin_lectura(ahora)

        self._ultima_lectura_valida = ahora
        distancia = lectura.distancia_cm
        assert distancia is not None

        candidata = self._clasificar(distancia)

        if candidata == self._candidata:
            self._contador += 1
        else:
            self._candidata = candidata
            self._contador = 1
        if self._contador < self._cfg.lecturas_estables:
            return None

        if candidata == self._fase:
            if distancia <= self._cfg.dist_captura_cm:
                return self._decidir_evento(self._fase, candidata, distancia, ahora)
            return None

        anterior, self._fase = self._fase, candidata
        return self._decidir_evento(anterior, candidata, distancia, ahora)

    def _manejar_sin_lectura(self, ahora: float) -> Optional[EventoTrigger]:
        if (
            self._ultima_lectura_valida > 0
            and ahora - self._ultima_lectura_valida >= self._cfg.timeout_sin_lectura_s
            and self._fase != FaseTrigger.ESPERANDO
        ):
            self._fase = FaseTrigger.ESPERANDO
            self._candidata = None
            self._contador = 0
            return EventoTrigger.DESACTIVAR
        return None

    def _clasificar(self, d: float) -> FaseTrigger:
        if d > self._cfg.dist_apagado_cm:
            return FaseTrigger.ESPERANDO
        if d <= self._cfg.dist_captura_cm:
            return FaseTrigger.CERCA
        if d <= self._cfg.dist_cerca_cm:
            return FaseTrigger.CERCA
        return FaseTrigger.DETECTADO

    def _decidir_evento(
        self, anterior: FaseTrigger, nueva: FaseTrigger,
        distancia: float, ahora: float,
    ) -> Optional[EventoTrigger]:
        if nueva == FaseTrigger.ESPERANDO and anterior != FaseTrigger.ESPERANDO:
            return EventoTrigger.DESACTIVAR

        if anterior == FaseTrigger.ESPERANDO and nueva != FaseTrigger.ESPERANDO:
            return EventoTrigger.ACTIVAR

        en_rango_disparo = distancia <= self._cfg.dist_captura_cm
        puede_disparar = ahora - self._ultima_foto >= self._cfg.cooldown_s
        if en_rango_disparo and puede_disparar:
            self._ultima_foto = ahora
            self._fase = FaseTrigger.CAPTURADO
            return EventoTrigger.CAPTURAR

        return None