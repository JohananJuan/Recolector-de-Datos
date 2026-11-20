from __future__ import annotations

import pandas as pd

from limpieza.etapas.nucleo import EtapaImagen, ResultadoEtapa


class EtapaCaracteristicas(EtapaImagen):
    nombre = "Extracción de características (imágenes)"
    tema = "3.2.1"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {}

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        from core.caracteristicas_imagen import extraer_caracteristicas

        df_antes = df.copy()
        df = df.copy()
        if "ruta" not in df.columns:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0}, mensaje="Sin columna 'ruta'",
            )

        filas = {}
        omitidas = 0
        for idx, ruta in df["ruta"].items():
            c = extraer_caracteristicas(self._resolver(ruta))
            if c is not None:
                filas[idx] = c.a_dict()
            else:
                omitidas += 1

        nuevas = pd.DataFrame.from_dict(filas, orient="index")
        if not nuevas.empty:
            df = df.drop(columns=[c for c in nuevas.columns if c in df.columns])
            df = df.join(nuevas)

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={"filas_afectadas": len(nuevas), "omitidas": omitidas},
            mensaje=f"{len(nuevas)} imágenes re-analizadas ({omitidas} omitidas)",
        )