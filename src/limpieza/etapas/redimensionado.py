from __future__ import annotations

from pathlib import Path

import pandas as pd

from limpieza.etapas.nucleo import EtapaImagen, ResultadoEtapa


class EtapaRedimensionado(EtapaImagen):
    nombre = "Optimización de tamaño y calidad"
    tema = "3.1.1"

    @classmethod
    def _parametros_por_defecto(cls) -> dict:
        return {"ancho": 224, "alto": 224, "modo": "recortar",
                "formato": "JPEG", "calidad": 85}

    def aplicar(self, df: pd.DataFrame) -> ResultadoEtapa:
        from PIL import Image, ImageOps

        df_antes = df.copy()
        df = df.copy()
        if "ruta" not in df.columns:
            return ResultadoEtapa(
                nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
                metricas={"filas_afectadas": 0}, mensaje="Sin columna 'ruta'",
            )

        if "ruta_original" not in df.columns:
            df["ruta_original"] = df["ruta"]

        w = int(self.parametros["ancho"])
        h = int(self.parametros["alto"])
        modo = self.parametros["modo"]
        fmt = self.parametros["formato"].upper()
        calidad = int(self.parametros["calidad"])
        ext = ".jpg" if fmt == "JPEG" else ".png"

        mb_antes = 0.0
        mb_despues = 0.0
        procesadas = 0
        omitidas = 0

        for idx, ruta in df["ruta"].items():
            p = self._resolver(ruta)
            if not p.exists():
                omitidas += 1
                continue
            mb_antes += p.stat().st_size / (1024 * 1024)
            nueva = self._destino(df, idx, "optimizadas", ext)
            with Image.open(p) as im:
                im = ImageOps.exif_transpose(im).convert("RGB")
                if modo == "rellenar":
                    im = ImageOps.pad(im, (w, h), color=(0, 0, 0))
                elif modo == "estirar":
                    im = im.resize((w, h), Image.Resampling.LANCZOS)
                else:
                    im = ImageOps.fit(im, (w, h), Image.Resampling.LANCZOS)
                if fmt == "JPEG":
                    im.save(nueva, "JPEG", quality=calidad, optimize=True)
                else:
                    im.save(nueva, "PNG", optimize=True)
            mb_despues += nueva.stat().st_size / (1024 * 1024)
            df.at[idx, "ruta"] = str(nueva)
            procesadas += 1

        return ResultadoEtapa(
            nombre=self.nombre, tema=self.tema, df=df, df_antes=df_antes,
            metricas={
                "filas_afectadas": procesadas,
                "mb_antes": round(mb_antes, 3),
                "mb_despues": round(mb_despues, 3),
                "formato": fmt, "calidad": calidad, "tamano": (w, h),
            },
            mensaje=(f"{mb_antes:.1f} MB → {mb_despues:.1f} MB "
                     f"({procesadas} imgs, {omitidas} no encontradas)"),
        )