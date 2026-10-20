import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import matplotlib.pyplot as plt

from core.rutas import METADATA_PROCESSED, LOGS_DIR
from metadata.repositorio import nuevo_repositorio
from limpieza.outliers import detectar_outliers


def _resumen_numerico(serie: pd.Series) -> dict:
    return {
        "media": serie.mean(),
        "mediana": serie.median(),
        "moda": serie.mode().iloc[0] if not serie.mode().empty else None,
        "std": serie.std(),
        "min": serie.min(),
        "max": serie.max(),
    }


def analizar_dataset(metadata_path: Path = METADATA_PROCESSED) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    repo = nuevo_repositorio()
    registros = repo.leer(metadata_path)
    if not registros:
        print(f"[!] Sin registros en {metadata_path}")
        return

    df = pd.DataFrame([r.a_dict() for r in registros])

    print("=" * 60)
    print("ANALISIS DEL DATASET")
    print("=" * 60)
    print(f"Registros: {len(df)}  |  Columnas: {len(df.columns)}")

    print("\n-- Valores faltantes --")
    for col, n in df.isnull().sum().items():
        print(f"  {col:20}: {n}")

    print("\n-- Distribucion por clase --")
    for clase, n in df["clase"].value_counts().items():
        print(f"  {clase:10}: {n:5} ({n/len(df)*100:.2f}%)")

    for col in ("ancho", "alto", "tamano_bytes"):
        if col not in df:
            continue
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            continue
        r = _resumen_numerico(s)
        print(f"\n-- {col} --")
        print(f"  media={r['media']:.2f}  mediana={r['mediana']:.2f}  "
              f"moda={r['moda']}  std={r['std']:.2f}  "
              f"min={r['min']}  max={r['max']}")
        out = detectar_outliers(s.tolist())
        print(f"  outliers z-score: {len(out.indices_zscore)}  "
              f"IQR: {len(out.indices_iqr)}  "
              f"interseccion: {len(out.indices_zscore & out.indices_iqr)}")

    print("\n-- Formatos --")
    for fmt, n in df["formato"].value_counts().items():
        print(f"  {fmt}: {n}")

    print("\n-- Motivos --")
    for m, n in df["motivo"].value_counts().items():
        print(f"  {m}: {n}")

    plt.figure(figsize=(8, 5))
    df["clase"].value_counts().plot(kind="bar")
    plt.title("Imagenes por clase")
    plt.tight_layout()
    plt.savefig(LOGS_DIR / "distribucion_clases.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 7))
    df["clase"].value_counts().plot(kind="pie", autopct="%1.1f%%", startangle=90)
    plt.ylabel("")
    plt.title("Distribucion porcentual")
    plt.tight_layout()
    plt.savefig(LOGS_DIR / "distribucion_porcentual.png", dpi=150)
    plt.close()

    print("\nAnalisis completado. Graficas en:", LOGS_DIR)


if __name__ == "__main__":
    analizar_dataset()