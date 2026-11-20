from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from limpieza.etapas.nucleo import EtapaImagen, ResultadoEtapa


class EtapaMejora(EtapaImagen):
    nombre = "Eliminación de ruido y mejora"
    tema = "3.1.2"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {"filtro": "mediana", "clahe": True}

    @staticmethod
    def _ruido(gris) -> float:
        import cv2
        suave = cv2.GaussianBlur(gris, (5, 5), 0)
        return float(np.std(gris.astype(np.float32) - suave.astype(np.float32)))

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        import cv2

        df_antes = df.copy()
        df = df.copy()
        if "ruta" not in df.columns:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0}, mensaje="Sin columna 'ruta'",
            )

        if "ruta_original" not in df.columns:
            df["ruta_original"] = df["ruta"]

        filtro = self.parametros["filtro"]
        usar_clahe = bool(self.parametros["clahe"])
        antes, despues = [], []
        omitidas = 0

        for idx, ruta in df["ruta"].items():
            p = self._resolver(ruta)
            if not p.exists():
                omitidas += 1
                continue
            img = cv2.imread(str(p))
            if img is None:
                omitidas += 1
                continue

            gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            antes.append(self._ruido(gris))

            if filtro == "gaussiano":
                suave = cv2.GaussianBlur(img, (5, 5), 0)
            elif filtro == "bilateral":
                suave = cv2.bilateralFilter(img, 9, 75, 75)
            else:
                suave = cv2.medianBlur(img, 5)

            if usar_clahe:
                lab = cv2.cvtColor(suave, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
                suave = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

            nueva = self._destino(df, idx, "mejoradas", p.suffix)
            cv2.imwrite(str(nueva), suave)
            df.at[idx, "ruta"] = str(nueva)
            despues.append(self._ruido(cv2.cvtColor(suave, cv2.COLOR_BGR2GRAY)))

        m_antes = float(np.mean(antes)) if antes else 0.0
        m_desp = float(np.mean(despues)) if despues else 0.0

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={
                "filas_afectadas": len(despues),
                "ruido_antes": round(m_antes, 2),
                "ruido_despues": round(m_desp, 2),
                "filtro": filtro, "clahe": usar_clahe,
                "omitidas": omitidas,
            },
            mensaje=f"ruido {m_antes:.2f} → {m_desp:.2f} ({len(despues)} imgs)",
        )