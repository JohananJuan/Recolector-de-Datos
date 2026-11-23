from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Callable

import pandas as pd

from limpieza.etapas.nucleo import ResultadoEtapa
from limpieza.pipeline import ConfigEtapa, PipelinePreprocesamiento
from limpieza.registro import etapas_por_defecto, registro_etapas
from servicios.extraccion_caracteristicas import ServicioExtraccionCaracteristicas


class ControladorPreprocesamiento:
    def __init__(
        self,
        raiz: Path | None = None,
        on_log: Callable[[str, str], None] | None = None,
        on_progreso: Callable[[int, int, str], None] | None = None,
    ):
        self._raiz = raiz
        self._on_log = on_log
        self._on_progreso = on_progreso
        self._df_original: pd.DataFrame | None = None
        self._config: dict[str, ConfigEtapa] = {
            c.clave: c for c in etapas_por_defecto()
        }

    def conectar(self, on_log, on_progreso) -> None:
        self._on_log = on_log
        self._on_progreso = on_progreso

    @property
    def raiz(self) -> Path | None:
        return self._raiz

    def tiene_datos(self) -> bool:
        return self._df_original is not None and not self._df_original.empty

    def cargar_carpeta(self, raiz: Path) -> int:
        raiz = Path(raiz)
        self._df_original = ServicioExtraccionCaracteristicas().extraer_con_metadata(
            raiz
        )
        self._raiz = raiz
        return len(self._df_original)

    def toggle_etapa(self, clave: str, activa: bool) -> None:
        if clave in self._config:
            self._config[clave].activa = activa

    def set_parametros(self, clave: str, parametros: dict) -> None:
        if clave in self._config:
            self._config[clave].parametros = dict(parametros)

    def reset_etapa(self, clave: str) -> dict:
        defaults = dict(registro_etapas[clave]._parametros_por_defecto())
        self._config[clave].parametros = defaults
        return defaults

    def config_activa(self) -> list[ConfigEtapa]:
        return deepcopy(list(self._config.values()))

    def _pipeline(self, config: list[ConfigEtapa]) -> PipelinePreprocesamiento:
        return PipelinePreprocesamiento(
            fabrica=registro_etapas,
            config=config,
            on_log=self._on_log,
            on_progreso=self._on_progreso,
            raiz=self._raiz,
        )

    def _exigir_datos(self) -> None:
        if not self.tiene_datos():
            raise RuntimeError("Primero elige una carpeta con imágenes")

    def ejecutar_solo(self, clave: str) -> ResultadoEtapa:
        self._exigir_datos()
        try:
            df_copia = self._df_original.copy(deep=True)
            return self._pipeline([self._config[clave]]).ejecutar_solo(clave, df_copia)
        except Exception as e:
            cls = registro_etapas[clave]
            return ResultadoEtapa(
                nombre=cls.nombre,
                tema=cls.tema,
                df=self._df_original,
                ok=False,
                error=str(e),
                mensaje=f"Error: {e}",
            )

    def ejecutar_todo(self) -> list[tuple[str, ResultadoEtapa]]:
        self._exigir_datos()
        activas = [c for c in self._config.values() if c.activa]
        df_copia = self._df_original.copy(deep=True)
        resultados = self._pipeline(activas).ejecutar(df_copia)
        return list(zip((c.clave for c in activas), resultados))
