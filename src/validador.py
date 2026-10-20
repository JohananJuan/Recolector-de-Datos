import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.rutas import PROCESSED_DIR, CAPTURAS_DIR, METADATA_CAPTURAS
from metadata.esquema import FUENTES_VALIDAS
from metadata.repositorio import nuevo_repositorio
from limpieza.reglas import reglas_por_defecto
from limpieza.pipeline import PipelineValidacion
from servicios.validacion import ServicioValidacion


def parsear_argumentos():
    p = argparse.ArgumentParser(description="Valida imagenes y genera metadata.csv")
    p.add_argument("--dir", type=str, default=str(PROCESSED_DIR))
    p.add_argument("--out", type=str, default=None)
    p.add_argument("--fuente", type=str, default="dataset_publico",
                   choices=sorted(FUENTES_VALIDAS))
    return p.parse_args()


if __name__ == "__main__":
    args = parsear_argumentos()
    dir_path = Path(args.dir)
    out_path = Path(args.out) if args.out else dir_path / "metadata.csv"

    repo = nuevo_repositorio()
    pipeline = PipelineValidacion(reglas_por_defecto())
    servicio = ServicioValidacion(pipeline, repo)
    servicio.validar_directorio(dir_path, out_path, args.fuente)