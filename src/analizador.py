import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from controladores.controlador_analisis import ControladorAnalisis
from core.rutas import METADATA_PROCESSED


def main(metadata_path: Path = METADATA_PROCESSED) -> None:
    ctrl = ControladorAnalisis()
    df = ctrl.cargar_dataframe(metadata_path)
    if df is None:
        print(f"[!] Sin registros en {metadata_path}")
        return
    df_crudo, df_limpio, comparativa, metricas = ctrl.extraer_y_limpiar(
        Path(metadata_path).parent
    )
    print("=" * 60)
    print("ANÁLISIS DEL DATASET")
    print("=" * 60)
    for k, v in metricas.items():
        print(f"  {k:25}: {v}")
    print(f"\nComparativa: {len(comparativa)} filas")


if __name__ == "__main__":
    main()