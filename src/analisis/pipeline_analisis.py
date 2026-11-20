from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

from analisis.comparador import (
    tabla_comparativa,
    comparativa_pairwise, comparativa_listwise,
)
from analisis.estadisticas import resumen_estadistico
from analisis.estandar import EstandarDataset, ResultadoEstandar, estandar_por_defecto
from analisis.exportador_excel import exportar_excel
from analisis.serializador import serializar_analisis, serializar_csv_plano
from limpieza.normalizacion import ResultadoNormalizacion, normalizar
from servicios.extraccion_caracteristicas import ServicioExtraccionCaracteristicas
from analisis.estadisticas_generales import generar_estadisticas_generales


@dataclass
class AnalisisResultado:
    crudo: pd.DataFrame
    limpio: pd.DataFrame
    normalizado: pd.DataFrame | None
    comparativa: pd.DataFrame
    pairwise: pd.DataFrame
    listwise: pd.DataFrame
    estandar: ResultadoEstandar | None
    metricas: dict
    meta_normalizacion: dict = field(default_factory=dict)
    cumplimiento: pd.DataFrame = field(default_factory=pd.DataFrame)
    trazabilidad: list = field(default_factory=list)


class PipelineAnalisis:

    def __init__(
        self,
        servicio_extraccion: ServicioExtraccionCaracteristicas | None = None,
        estandar: EstandarDataset | None = None,
        metodo_normalizacion: str = "zscore",
    ):
        self._extraccion = (
            servicio_extraccion or ServicioExtraccionCaracteristicas()
        )
        self._estandar = estandar or estandar_por_defecto()
        self._metodo_norm = metodo_normalizacion

    def analizar(
        self,
        raiz: Path,
        al_progresar: Callable[[str], None] | None = None,
        etapas_config=None,
    ) -> AnalisisResultado:
        from limpieza.pipeline import PipelinePreprocesamiento
        from limpieza.registro import registro_etapas
        from limpieza.cumplimiento import tabla_cumplimiento

        def _log(msg: str) -> None:
            if al_progresar:
                al_progresar(msg)

        _log(f"Escaneando {raiz} ...")
        crudo = self._extraccion.extraer_con_metadata(raiz)
        _log(f"{len(crudo)} imágenes procesadas.")

        if etapas_config:
            pipe = PipelinePreprocesamiento(
                fabrica=registro_etapas,
                config=etapas_config,
                raiz=raiz,
                on_log=lambda t, m: al_progresar and al_progresar(f"[{t}] {m}"),
                on_progreso=lambda i, n, s: al_progresar and al_progresar(
                    f"({i}/{n}) {s}"
                ),
            )
            resultados_etapas = pipe.ejecutar(crudo)
            previas = [r for r in resultados_etapas if r.tema != "2.3.1"]
            limpio = previas[-1].df if previas else crudo
            metricas = {r.nombre: r.metricas for r in resultados_etapas}
            cumplimiento = tabla_cumplimiento(resultados_etapas)
            trazabilidad = [
                {"etapa": r.nombre, "tema": r.tema, "ok": r.ok,
                 "mensaje": r.mensaje, "metricas": r.metricas}
                for r in resultados_etapas
            ]
        else:
            from limpieza.pipeline import pipeline_limpieza
            _log("Aplicando pipeline de limpieza...")
            limpio, metricas = pipeline_limpieza(crudo)
            cumplimiento = tabla_cumplimiento()
            trazabilidad = []

        _log(f"Normalizando (método={self._metodo_norm})...")
        norm: ResultadoNormalizacion = normalizar(limpio, self._metodo_norm)
        meta_norm = {
            "metodo": norm.metodo,
            "columnas_afectadas": norm.columnas_afectadas,
            "parametros": norm.parametros,
        }

        _log("Evaluando estándar de aceptación...")
        est = self._estandar.evaluar(limpio)

        _log("Comparando pairwise / listwise...")
        comp = tabla_comparativa(crudo, limpio)
        pair = comparativa_pairwise(crudo, limpio)
        listw = comparativa_listwise(crudo, limpio)

        return AnalisisResultado(
            crudo=crudo,
            limpio=limpio,
            normalizado=norm.df,
            comparativa=comp,
            pairwise=pair,
            listwise=listw,
            estandar=est,
            metricas=metricas,
            meta_normalizacion=meta_norm,
            cumplimiento=cumplimiento,
            trazabilidad=trazabilidad,
        )

    def exportar_excel(self, resultado: AnalisisResultado, ruta: Path) -> Path:
        est_resumen = (
            resultado.estandar.resumen if resultado.estandar else None
        )
        estadisticas = generar_estadisticas_generales(
            crudo=resultado.crudo,
            limpio=resultado.limpio,
            metricas=resultado.metricas,
            comparativa=resultado.comparativa,
            pairwise=resultado.pairwise,
            listwise=resultado.listwise,
            meta_normalizacion=resultado.meta_normalizacion,
            estandar_resumen=est_resumen,
        )
        return exportar_excel(
            df_crudo=resultado.crudo,
            df_limpio=resultado.limpio,
            tabla_comparativa=resultado.comparativa,
            metricas=resultado.metricas,
            ruta=ruta,
            df_normalizado=resultado.normalizado,
            normalizacion=resultado.meta_normalizacion,
            pairwise=resultado.pairwise,
            listwise=resultado.listwise,
            estandar=est_resumen,
            df_aprobadas=(
                resultado.estandar.aprobadas if resultado.estandar else None
            ),
            df_rechazadas=(
                resultado.estandar.rechazadas if resultado.estandar else None
            ),
            estadisticas=estadisticas,
            cumplimiento_temario=resultado.cumplimiento,
            trazabilidad_etapas=resultado.trazabilidad,
        )

    def exportar_json(self, resultado: AnalisisResultado, ruta: Path) -> Path:
        est_resumen = (
            resultado.estandar.resumen if resultado.estandar else {}
        )
        return serializar_analisis(
            ruta=ruta,
            metricas=resultado.metricas,
            tabla_comparativa=resultado.comparativa,
            pairwise=resultado.pairwise,
            listwise=resultado.listwise,
            normalizacion=resultado.meta_normalizacion,
            estandar=est_resumen,
            resumen_estadistico=resumen_estadistico(resultado.limpio),
        )

    def exportar_csv(self, resultado: AnalisisResultado, ruta: Path) -> Path:
        return serializar_csv_plano(
            ruta=ruta,
            pairwise=resultado.pairwise,
            listwise=resultado.listwise,
        )