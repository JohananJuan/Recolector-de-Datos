from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Prediccion:
    clase: str
    confianza: float
    scores: dict[str, float]


class Clasificador(ABC):
    @abstractmethod
    def predecir(self, frame_bgr) -> Prediccion | None:
        ...

    @property
    @abstractmethod
    def clases(self) -> tuple[str, ...]:
        ...