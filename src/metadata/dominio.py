from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

from .esquema import CAMPOS, FUENTES_VALIDAS, ahora


@dataclass
class RegistroMetadata:
    archivo: str = ""
    clase: str = ""
    ruta: str = ""
    fuente: str = ""
    fecha_captura: str = ""
    hora_captura: str = ""
    camara: str = ""
    sesion: str = ""
    version_dataset: str = ""
    ancho: Any = ""
    alto: Any = ""
    formato: str = ""
    tamano_bytes: Any = ""
    hash: str = ""
    phash: str = ""
    valido: Any = True
    motivo: str = "OK"

    def __post_init__(self):
        if not self.fecha_captura or not self.hora_captura:
            f, h = ahora()
            self.fecha_captura = self.fecha_captura or f
            self.hora_captura = self.hora_captura or h
        if self.fuente and self.fuente not in FUENTES_VALIDAS:
            raise ValueError(f"Fuente invalida: {self.fuente}")

    def a_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def desde_dict(cls, d: dict) -> "RegistroMetadata":
        limpio = {k: d.get(k, "") for k in CAMPOS}
        v = limpio.get("valido", True)
        if isinstance(v, str):
            limpio["valido"] = v.strip().lower() in ("true", "1", "yes", "si", "sí")
        return cls(**limpio)

    def es_valido(self) -> bool:
        v = self.valido
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes", "si", "sí")
        return bool(v)


def ruta_relativa(archivo: Path, base: Path) -> str:
    try:
        return str(archivo.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(archivo)