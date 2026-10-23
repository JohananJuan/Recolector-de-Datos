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
            d["etiqueta"] = etiqueta or ruta.parent.name
            filas.append(d)
        return pd.DataFrame(filas)