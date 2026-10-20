from collections import deque
from dataclasses import dataclass, field

from .interfaz import Clasificador
from .nulo import ClasificadorNulo


@dataclass
class EstadoClasificacion:
    clase: str = "—"
    confianza: float = 0.0
    estable: bool = False
    scores: dict[str, float] = field(default_factory=dict)


class ServicioClasificacion:
    def __init__(self, clasificador: Clasificador,
                 tamano_buffer: int = 8,
                 umbral_confianza: float = 0.55,
                 frames_consenso: int = 5):
        self._clf = clasificador
        self._buffer = deque(maxlen=tamano_buffer)
        self._umbral = umbral_confianza
        self._frames_consenso = frames_consenso
        self._estado = EstadoClasificacion()

    @property
    def clases(self) -> tuple[str, ...]:
        return self._clf.clases

    @property
    def tiene_modelo(self) -> bool:
        return not isinstance(self._clf, ClasificadorNulo)

    def procesar(self, frame_bgr) -> EstadoClasificacion:
        pred = self._clf.predecir(frame_bgr)
        if pred is None:
            self._buffer.clear()
            self._estado = EstadoClasificacion()
            return self._estado

        self._buffer.append(pred)

        conteo: dict[str, int] = {}
        confianza: dict[str, float] = {}
        for p in self._buffer:
            conteo[p.clase] = conteo.get(p.clase, 0) + 1
            confianza[p.clase] = confianza.get(p.clase, 0.0) + p.confianza

        clase_dom = max(conteo, key=conteo.get)
        n = len(self._buffer)
        ratio = conteo[clase_dom] / n
        conf_prom = confianza[clase_dom] / conteo[clase_dom]

        estable = (ratio >= 0.6 and conf_prom >= self._umbral
                   and conteo[clase_dom] >= self._frames_consenso)
        self._estado = EstadoClasificacion(
            clase=clase_dom,
            confianza=conf_prom,
            estable=estable,
            scores=pred.scores,
        )
        return self._estado

    def reset(self) -> None:
        self._buffer.clear()
        self._estado = EstadoClasificacion()