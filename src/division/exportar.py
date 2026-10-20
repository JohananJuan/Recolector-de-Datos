import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rutas import SPLITS_DIR, METADATA_PROCESSED
from metadata.repositorio import RepositorioMetadata, nuevo_repositorio
from metadata.dominio import RegistroMetadata
from division.split import split_por_grupo


def exportar_splits(metadata_path: Path = METADATA_PROCESSED,
                    salida_dir: Path = SPLITS_DIR,
                    campo_grupo: str = "sesion",
                    repo: RepositorioMetadata | None = None) -> dict[str, int]:
    repo = repo or nuevo_repositorio()
    registros_dom = repo.leer(metadata_path)
    if not registros_dom:
        print("[!] Sin registros para dividir.")
        return {}

    sin_sesion = sum(1 for r in registros_dom if not (r.sesion or "").strip())
    if campo_grupo == "sesion" and sin_sesion == len(registros_dom):
        print("[ADVERTENCIA] Ningun registro tiene 'sesion'.")
        print("              El split agrupara por clase; no habra fuga entre clases,")
        print("              pero tampoco separacion por objeto fisico.")
        print("              Recomendado: recaptura con capturador.py o asigna 'sesion' manualmente.\n")

    registros = [r.a_dict() for r in registros_dom]
    partes = split_por_grupo(registros, campo_grupo=campo_grupo)

    salida_dir = Path(salida_dir)
    salida_dir.mkdir(parents=True, exist_ok=True)

    conteo = {}
    for nombre, filas in partes.items():
        registros_split = [RegistroMetadata.desde_dict(f) for f in filas]
        destino = salida_dir / f"{nombre}.csv"
        repo.escribir(registros_split, destino)
        conteo[nombre] = len(registros_split)
        print(f"{nombre:6}: {len(registros_split):5} -> {destino}")

    return conteo


if __name__ == "__main__":
    exportar_splits()