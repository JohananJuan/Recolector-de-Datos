from __future__ import annotations
from pathlib import Path
import pandas as pd
from core.caracteristicas_imagen import extraer_caracteristicas

EXTENSIONES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


class ServicioExtraccionCaracteristicas:

    def extraer_directorio(
        self, raiz: Path, etiqueta: str | None = None
    ) -> pd.DataFrame:
        raiz = Path(raiz)
        if not raiz.exists():
            return pd.DataFrame()

        imagenes = [
            p for p in raiz.rglob("*")
            if p.is_file() and p.suffix.lower() in EXTENSIONES
        ]
        filas: list[dict] = []
        for ruta in imagenes:
            caract = extraer_caracteristicas(ruta)
            if caract is None:
                continue
            d = caract.a_dict()
            d["ruta"] = str(ruta.relative_to(raiz))
            d["clase"] = etiqueta or ruta.parent.name
            d["archivo"] = ruta.name
            filas.append(d)
        return pd.DataFrame(filas)

    def extraer_con_metadata(self, raiz: Path) -> pd.DataFrame:
        from metadata.repositorio import nuevo_repositorio

        df = self.extraer_directorio(raiz)
        if df.empty:
            return df
        for nombre in ("metadata.csv", "metadata_capturas.csv"):
            p = Path(raiz) / nombre
            if not p.exists():
                continue
            regs = nuevo_repositorio().leer(p)
            if not regs:
                continue
            meta = pd.DataFrame([r.a_dict() for r in regs])
            cols = ["archivo", "licencia", "origen", "consentimiento",
                    "anonimizado", "sesion", "fuente"]
            return df.merge(meta[cols].drop_duplicates("archivo"),
                            on="archivo", how="left")
        return df