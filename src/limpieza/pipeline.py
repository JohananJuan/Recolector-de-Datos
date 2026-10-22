from pathlib import Path
from dataclasses import dataclass, field
from typing import Sequence

from .reglas import ReglaValidacion, Severidad


@dataclass
class RegistroValidado:
    archivo: str
    clase: str
    ruta: str
    fuente: str
    severidad: Severidad
    motivo: str
    extras: dict = field(default_factory=dict)

    @property
    def valido(self) -> bool:
        return self.severidad != "invalida"


class PipelineValidacion:
    def __init__(self, reglas: Sequence[ReglaValidacion]):
        self._reglas = list(reglas)

    def validar_archivo(self, archivo: Path, contexto: dict) -> RegistroValidado:
        extras: dict = {}
        severidad: Severidad = "ok"
        motivo = "OK"

        for regla in self._reglas:
            r = regla.evaluar(archivo, contexto)
            extras.update(r.extras)
            if r.severidad == "invalida":
                return RegistroValidado(
                    archivo.name, contexto["clase"], contexto["ruta_rel"],
                    contexto["fuente"], "invalida", r.motivo, extras,
                )
            if r.severidad == "revisar" and severidad == "ok":
                severidad = "revisar"
                motivo = r.motivo

        return RegistroValidado(
            archivo.name, contexto["clase"], contexto["ruta_rel"],
            contexto["fuente"], severidad, motivo, extras,
        )