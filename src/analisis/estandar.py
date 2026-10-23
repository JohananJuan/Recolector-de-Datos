from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class ResultadoReglaEstandar:
    nombre: str
    columna: str
    cumple: pd.Series         
    detalle: str = ""
    parametros: dict = field(default_factory=dict)

    @property
    def n_ok(self) -> int:
        return int(self.cumple.sum())

    @property
    def n_total(self) -> int:
        return int(len(self.cumple))


class ReglaEstandar(ABC):
    nombre: str = "base"

    @abstractmethod
    def evaluar(self, df: pd.DataFrame) -> ResultadoReglaEstandar: ...


class ReglaRango(ReglaEstandar):

    def __init__(self, columna: str, minimo: float, maximo: float,
                 nombre: str | None = None):
        self.columna = columna
        self.minimo = minimo
        self.maximo = maximo
        self.nombre = nombre or f"{columna}∈[{minimo},{maximo}]"

    def evaluar(self, df: pd.DataFrame) -> ResultadoReglaEstandar:
        if self.columna not in df:
            vacio = pd.Series(False, index=df.index)
            return ResultadoReglaEstandar(
                self.nombre, self.columna, vacio,
                detalle=f"columna ausente: {self.columna}",
                parametros={"min": self.minimo, "max": self.maximo},
            )
        serie = pd.to_numeric(df[self.columna], errors="coerce")
        cumple = serie.between(self.minimo, self.maximo).fillna(False)
        return ResultadoReglaEstandar(
            self.nombre, self.columna, cumple,
            detalle=f"Rango [{self.minimo}, {self.maximo}]",
            parametros={"min": self.minimo, "max": self.maximo},
        )


class ReglaNoNulo(ReglaEstandar):

    def __init__(self, columna: str, nombre: str | None = None):
        self.columna = columna
        self.nombre = nombre or f"{columna} no nulo"

    def evaluar(self, df: pd.DataFrame) -> ResultadoReglaEstandar:
        if self.columna not in df:
            vacio = pd.Series(False, index=df.index)
            return ResultadoReglaEstandar(
                self.nombre, self.columna, vacio,
                detalle=f"columna ausente: {self.columna}",
            )
        cumple = df[self.columna].notna()
        return ResultadoReglaEstandar(
            self.nombre, self.columna, cumple,
            detalle="Valor presente",
        )


class ReglaZScoreMax(ReglaEstandar):

    def __init__(self, columna: str, umbral: float = 3.0,
                 nombre: str | None = None):
        self.columna = columna
        self.umbral = umbral
        self.nombre = nombre or f"{columna} |z|≤{umbral}"

    def evaluar(self, df: pd.DataFrame) -> ResultadoReglaEstandar:
        if self.columna not in df:
            vacio = pd.Series(False, index=df.index)
            return ResultadoReglaEstandar(
                self.nombre, self.columna, vacio,
                detalle=f"columna ausente: {self.columna}",
            )
        serie = pd.to_numeric(df[self.columna], errors="coerce")
        mu = serie.mean()
        sigma = serie.std(ddof=0)
        if sigma == 0 or pd.isna(sigma):
            cumple = pd.Series(True, index=df.index)
        else:
            z = ((serie - mu) / sigma).abs()
            cumple = (z <= self.umbral).fillna(False)
        return ResultadoReglaEstandar(
            self.nombre, self.columna, cumple,
            detalle=f"Umbral |z| ≤ {self.umbral}",
            parametros={"umbral": self.umbral},
        )


class ReglaPersonalizada(ReglaEstandar):

    def __init__(self, nombre: str, columna: str,
                 predicado, detalle: str = ""):
        self.nombre = nombre
        self.columna = columna
        self._predicado = predicado
        self._detalle = detalle

    def evaluar(self, df: pd.DataFrame) -> ResultadoReglaEstandar:
        if self.columna not in df:
            vacio = pd.Series(False, index=df.index)
            return ResultadoReglaEstandar(
                self.nombre, self.columna, vacio,
                detalle=f"columna ausente: {self.columna}",
            )
        cumple = self._predicado(df[self.columna]).fillna(False)
        return ResultadoReglaEstandar(
            self.nombre, self.columna, cumple,
            detalle=self._detalle or "Predicado personalizado",
        )


@dataclass
class ResultadoEstandar:
    reglas: list[ResultadoReglaEstandar]
    cumple_global: pd.Series           
    aprobadas: pd.DataFrame            
    rechazadas: pd.DataFrame            
    resumen: dict = field(default_factory=dict)


class EstandarDataset:

    def __init__(self, nombre: str, reglas: list[ReglaEstandar]):
        self.nombre = nombre
        self._reglas = list(reglas)

    @property
    def reglas(self) -> list[ReglaEstandar]:
        return list(self._reglas)

    def agregar_regla(self, regla: ReglaEstandar) -> None:
        self._reglas.append(regla)

    def evaluar(self, df: pd.DataFrame) -> ResultadoEstandar:
        resultados: list[ResultadoReglaEstandar] = []
        cumple_global = pd.Series(True, index=df.index)

        for regla in self._reglas:
            r = regla.evaluar(df)
            resultados.append(r)
            cumple_global &= r.cumple

        aprobadas = df.loc[cumple_global].copy()
        rechazadas = df.loc[~cumple_global].copy()

        resumen = {
            "estandar": self.nombre,
            "total_filas": len(df),
            "aprobadas": int(cumple_global.sum()),
            "rechazadas": int((~cumple_global).sum()),
            "porcentaje_aprobacion": (
                float(cumple_global.mean() * 100) if len(df) else 0.0
            ),
            "reglas": [
                {
                    "nombre": r.nombre,
                    "columna": r.columna,
                    "aprobadas": r.n_ok,
                    "total": r.n_total,
                    "porcentaje": (r.n_ok / r.n_total * 100) if r.n_total else 0.0,
                    "detalle": r.detalle,
                    "parametros": r.parametros,
                }
                for r in resultados
            ],
        }
        return ResultadoEstandar(
            reglas=resultados,
            cumple_global=cumple_global,
            aprobadas=aprobadas,
            rechazadas=rechazadas,
            resumen=resumen,
        )


def estandar_por_defecto() -> EstandarDataset:
    return EstandarDataset(
        nombre="Estandar por defecto",
        reglas=[
            ReglaNoNulo("ancho"),
            ReglaNoNulo("alto"),
            ReglaNoNulo("tamano_bytes"),
            ReglaRango("ancho", 320, 4096),
            ReglaRango("alto", 240, 4096),
            ReglaRango("brillo_medio", 20, 235),
            ReglaRango("varianza_laplaciano", 50, 5000),
            ReglaRango("ruido_estimado", 0, 25),
            ReglaZScoreMax("tamano_bytes", umbral=3.5),
        ],
    )