from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from core.imagen import inspeccionar_imagen, EXTENSIONES_VALIDAS
from core.hashing import sha256_archivo, phash_imagen, distancia_hamming
from core.calidad import calcular_metricas

Severidad = Literal["ok", "revisar", "invalida"]


@dataclass
class ResultadoRegla:
    severidad: Severidad
    motivo: str
    extras: dict = field(default_factory=dict)

    @property
    def valido(self) -> bool:
        return self.severidad != "invalida"


class ReglaValidacion(ABC):
    nombre: str = "base"

    @abstractmethod
    def evaluar(self, archivo: Path, contexto: dict) -> ResultadoRegla: ...


class ReglaExtension(ReglaValidacion):
    nombre = "extension"

    def evaluar(self, archivo, contexto):
        ok = archivo.suffix.lower() in EXTENSIONES_VALIDAS
        if ok:
            return ResultadoRegla("ok", "OK")
        return ResultadoRegla("invalida", "Extension no valida")


class ReglaDecodificacion(ReglaValidacion):
    nombre = "decodificacion"

    def evaluar(self, archivo, contexto):
        info = inspeccionar_imagen(archivo)
        if not info.valida:
            return ResultadoRegla("invalida", info.motivo)
        return ResultadoRegla("ok", "OK", {
            "ancho": info.ancho, "alto": info.alto,
            "formato": info.formato, "modo": info.modo,
        })


class ReglaDuplicadoSHA(ReglaValidacion):
    nombre = "duplicado_sha"

    def evaluar(self, archivo, contexto):
        h = sha256_archivo(archivo)
        vistos = contexto.setdefault("hashes_sha", {})
        if h in vistos:
            return ResultadoRegla("invalida", f"Duplicada SHA de {vistos[h]}", {"hash": h})
        vistos[h] = archivo.name
        return ResultadoRegla("ok", "OK", {"hash": h})


class ReglaDuplicadoPHash(ReglaValidacion):
    nombre = "duplicado_phash"
    UMBRAL = 6

    def evaluar(self, archivo, contexto):
        ph = phash_imagen(archivo)
        if ph is None:
            return ResultadoRegla("ok", "OK: phash omitido (imagehash no instalado)",
                                  {"phash": ""})
        vistos = contexto.setdefault("hashes_phash", [])
        for otro_ph, otro_nombre in vistos:
            if distancia_hamming(ph, otro_ph) <= self.UMBRAL:
                return ResultadoRegla(
                    "invalida", f"Duplicada visual de {otro_nombre}", {"phash": str(ph)}
                )
        vistos.append((ph, archivo.name))
        return ResultadoRegla("ok", "OK", {"phash": str(ph)})


class ReglaCalidadVisual(ReglaValidacion):
    nombre = "calidad_visual"

    def evaluar(self, archivo, contexto):
        m = calcular_metricas(archivo)
        if m is None:
            return ResultadoRegla("invalida", "No se pudo calcular calidad")
        extras = {
            "laplaciano_var": m.laplaciano_var,
            "luminancia_media": m.luminancia_media,
            "luminancia_mediana": m.luminancia_mediana,
            "luminancia_std": m.luminancia_std,
        }
        if m.imagen_vacia:
            return ResultadoRegla("invalida", "Imagen vacia o casi uniforme", extras)
        if m.borrosa:
            return ResultadoRegla("revisar", "Revisar: posible borrosidad", extras)
        return ResultadoRegla("ok", "OK", extras)


def reglas_por_defecto() -> list[ReglaValidacion]:
    return [
        ReglaExtension(),
        ReglaDecodificacion(),
        ReglaDuplicadoSHA(),
        ReglaDuplicadoPHash(),
        ReglaCalidadVisual(),
    ]