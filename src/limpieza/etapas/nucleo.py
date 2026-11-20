from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ResultadoEtapa:
    nombre: str
    tema: str
    df: pd.DataFrame
    df_antes: pd.DataFrame | None = None
    metricas: dict[str, Any] = field(default_factory=dict)
    mensaje: str = ""
    ok: bool = True
    error: str | None = None

    @property
    def filas_afectadas(self) -> int:
        return int(self.metricas.get("filas_afectadas", 0))


class EtapaPreprocesamiento(ABC):

    nombre: str = "etapa"
    tema: str = "0.0"
    raiz: Path | None = None

    def __init__(self, **parametros: Any) -> None:
        base = self._parametros_por_defecto()
        base.update(parametros or {})
        self.parametros: dict[str, Any] = base

    @classmethod
    def _parametros_por_defecto(cls) -> dict[str, Any]:
        return {}

    @abstractmethod
    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa: ...

    def descripcion(self) -> str:
        return f"{self.tema} {self.nombre}"

    def reset_parametros(self) -> None:
        self.parametros = self._parametros_por_defecto()

    def _resolver(self, ruta: str) -> Path:
        p = Path(ruta)
        if p.is_absolute() or self.raiz is None:
            return p
        return self.raiz / p

    def _destino(self, df: pd.DataFrame, idx, carpeta: str,
                 ext: str | None = None) -> Path:
        base = self.raiz or Path.cwd()
        rel = Path(str(df.at[idx, "ruta_original"]))
        if rel.is_absolute():
            rel = Path(rel.name)
        destino = base.parent / f"{base.name}_preprocesado" / carpeta / rel
        if ext:
            destino = destino.with_suffix(ext)
        destino.parent.mkdir(parents=True, exist_ok=True)
        return destino


class EtapaTabular(EtapaPreprocesamiento):
    pass


class EtapaImagen(EtapaPreprocesamiento):
    pass