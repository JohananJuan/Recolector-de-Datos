from __future__ import annotations

import pandas as pd

from limpieza.etapas.nucleo import EtapaTabular, ResultadoEtapa


class EtapaDiscretizacion(EtapaTabular):
    nombre = "Discretización (binning)"
    tema = "2.3.2"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {
            "columna": "brillo_medio",
            "bins": 3,
            "estrategia": "ancho",
            "etiquetas": ["oscuro", "medio", "claro"],
        }

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        df_antes = df.copy()
        df = df.copy()
        col = self.parametros["columna"]
        if col not in df.columns:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0},
                mensaje=f"Columna '{col}' ausente",
            )

        bins = int(self.parametros["bins"])
        etiquetas = list(self.parametros["etiquetas"])
        if len(etiquetas) != bins:
            etiquetas = [f"bin_{i + 1}" for i in range(bins)]
        nueva = f"{col}_discreto"

        try:
            if self.parametros["estrategia"] == "frecuencia":
                _, cortes = pd.qcut(
                    df[col], q=bins, retbins=True, duplicates="drop"
                )
                n_reales = len(cortes) - 1
                df[nueva] = pd.qcut(
                    df[col], q=bins,
                    labels=etiquetas[:n_reales],
                    duplicates="drop",
                )
            else:
                _, cortes = pd.cut(df[col], bins=bins, retbins=True)
                df[nueva] = pd.cut(df[col], bins=bins, labels=etiquetas)
        except Exception as e:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df_antes,
                df_antes=df_antes,
                metricas={"filas_afectadas": 0},
                ok=False, error=str(e),
                mensaje=f"Discretización falló: {e}",
            )

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={
                "filas_afectadas": int(df[nueva].notna().sum()),
                "cortes": [round(float(c), 4) for c in cortes],
                "conteo": df[nueva].value_counts(dropna=False).to_dict(),
                "columna_creada": nueva,
                "estrategia": self.parametros["estrategia"],
            },
            mensaje=f"{col} → {bins} bins ({self.parametros['estrategia']})",
        )