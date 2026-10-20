import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rutas import METADATA_PROCESSED
from metadata.repositorio import RepositorioMetadata, nuevo_repositorio
from limpieza.outliers import detectar_outliers


CAMPOS_NUMERICOS = ("ancho", "alto", "tamano_bytes")
_VALORES_NULOS = {"", "none", "nan", "null", "na"}


def marcar_outliers(metadata_path: Path = METADATA_PROCESSED,
                    repo: RepositorioMetadata | None = None) -> dict:
    repo = repo or nuevo_repositorio()
    registros = repo.leer(metadata_path)
    if not registros:
        print("[!] Sin registros para analizar.")
        return {}

    reporte = {}
    for campo in CAMPOS_NUMERICOS:
        valores = []
        indices_validos = []
        for i, r in enumerate(registros):
            v = getattr(r, campo, "")
            s = str(v).strip()
            if s.lower() in _VALORES_NULOS:
                continue
            try:
                valores.append(float(s))
                indices_validos.append(i)
            except (TypeError, ValueError):
                continue

        out = detectar_outliers(valores)
        candidatos = out.indices_zscore & out.indices_iqr
        reporte[campo] = {
            "zscore": len(out.indices_zscore),
            "iqr": len(out.indices_iqr),
            "candidatos": len(candidatos),
            "media": out.media,
            "mediana": out.mediana,
            "moda": out.moda,
        }

        for idx_local in candidatos:
            idx_real = indices_validos[idx_local]
            r = registros[idx_real]
            if r.motivo == "OK":
                r.motivo = f"Revisar: outlier {campo}"

    repo.escribir(registros, metadata_path)

    print("=" * 55)
    print("MARCADO DE OUTLIERS (metadatos)")
    print("=" * 55)
    for campo, r in reporte.items():
        print(f"\n{campo}")
        print(f"  media={r['media']:.2f}  mediana={r['mediana']:.2f}  moda={r['moda']}")
        print(f"  outliers z-score: {r['zscore']}")
        print(f"  outliers IQR:     {r['iqr']}")
        print(f"  marcados (interseccion): {r['candidatos']}")
    print(f"\nMotivos actualizados en: {metadata_path}")
    return reporte


if __name__ == "__main__":
    marcar_outliers()