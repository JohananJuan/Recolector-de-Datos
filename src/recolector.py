import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.rutas import METADATA_PROCESSED
from metadata.repositorio import nuevo_repositorio
from servicios.recoleccion import ServicioRecoleccion


def recolectar_datos():
    repo = nuevo_repositorio()
    servicio = ServicioRecoleccion(repo, METADATA_PROCESSED)
    servicio.recolectar()


if __name__ == "__main__":
    recolectar_datos()