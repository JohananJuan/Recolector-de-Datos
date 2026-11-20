from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd

from limpieza.etapas.nucleo import EtapaPreprocesamiento, ResultadoEtapa
from limpieza.reglas import ReglaValidacion, ResultadoRegla


@dataclass
class ConfigEtapa:
    clave: str
    activa: bool = True
    parametros: dict = field(default_factory=dict)


class PipelinePreprocesamiento:

    def __init__(
        self,
        fabrica: dict[str, type[EtapaPreprocesamiento]],
        config: list[ConfigEtapa],
        on_progreso: Callable[[int, int, str], None] | None = None,
        on_log: Callable[[str, str], None] | None = None,
        raiz: Path | None = None,
    ) -> None:
        self.fabrica = fabrica
        self.config = config
        self.on_progreso = on_progreso or (lambda i, n, s: None)
        self.on_log = on_log or (lambda tema, msg: None)
        self.raiz = raiz

    def _instanciar(self, cfg: ConfigEtapa) -> EtapaPreprocesamiento:
        cls = self.fabrica[cfg.clave]
        etapa = cls(**cfg.parametros) if cfg.parametros else cls()
        etapa.raiz = self.raiz
        return etapa

    def ejecutar(self, df: pd.DataFrame) -> list[ResultadoEtapa]:
        activas = [c for c in self.config if c.activa]
        total = len(activas)
        resultados: list[ResultadoEtapa] = []

        for i, cfg in enumerate(activas, start=1):
            etapa = self._instanciar(cfg)
            self.on_progreso(i, total, f"{etapa.tema} {etapa.nombre}")
            try:
                res = etapa.aplicar(df)
            except Exception as e:
                res = ResultadoEtapa(
                    nombre=etapa.nombre, tema=etapa.tema, df=df, ok=False,
                    error=str(e), mensaje=f"Error: {e}",
                )
            resultados.append(res)
            self.on_log(etapa.tema, res.mensaje)
            if res.ok:
                df = res.df
        return resultados

    def ejecutar_solo(self, clave: str, df: pd.DataFrame) -> ResultadoEtapa:
        cfg = next((c for c in self.config if c.clave == clave), None)
        if cfg is None:
            raise KeyError(clave)
        return self._instanciar(cfg).aplicar(df)


def pipeline_limpieza(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    etapa = __import__(
        "limpieza.etapas.limpieza_datos", fromlist=["EtapaLimpieza"]
    ).EtapaLimpieza()
    res = etapa.aplicar(df)
    antes = res.df_antes if res.df_antes is not None else df
    return res.df, {
        "filas_originales": len(antes),
        "filas_ruido_eliminadas": res.metricas.get("filas_ruido_eliminadas", 0),
        "filas_finales": len(res.df),
        "columnas": len(df.columns),
        "celdas_nulas_antes": int(antes.isna().sum().sum()),
        "celdas_nulas_imputadas": res.metricas.get(
            "celdas_nulas_imputadas", 0
        ),
    }


_ORDEN_SEVERIDAD = {"ok": 0, "revisar": 1, "invalida": 2}


class PipelineValidacion:

    def __init__(self, reglas: Iterable[ReglaValidacion]) -> None:
        self._reglas = list(reglas)

    @property
    def reglas(self) -> list[ReglaValidacion]:
        return list(self._reglas)

    def validar_archivo(
        self, archivo: Path, contexto: dict | None = None
    ) -> ResultadoRegla:
        contexto = contexto if contexto is not None else {}
        peor = ResultadoRegla("ok", "OK")
        extras: dict = {}

        for regla in self._reglas:
            try:
                r = regla.evaluar(archivo, contexto)
            except Exception as e:
                r = ResultadoRegla(
                    "invalida", f"Error en {regla.nombre}: {e}"
                )
            extras.update(r.extras)
            if _ORDEN_SEVERIDAD[r.severidad] > _ORDEN_SEVERIDAD[peor.severidad]:
                peor = r

        return ResultadoRegla(
            severidad=peor.severidad,
            motivo=peor.motivo,
            extras=extras,
        )