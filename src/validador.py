import sys
import argparse
import hashlib
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata


BASE_DIR = Path(__file__).resolve().parent.parent

DIR_DEFECTO = BASE_DIR / "data" / "processed"
FUENTE_DEFECTO = "dataset_publico"

CLASES_VALIDAS = {"carton", "papel", "tela"}

EXTENSIONES_VALIDAS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def calcular_hash(archivo):
    """SHA-256 del archivo."""
    sha256 = hashlib.sha256()
    with open(archivo, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            sha256.update(bloque)
    return sha256.hexdigest()


def validar_imagen(archivo):
    """Devuelve (valido, motivo, ancho, alto, formato)."""
    try:
        with Image.open(archivo) as imagen:
            imagen.verify()

        with Image.open(archivo) as imagen:
            ancho, alto = imagen.size
            formato = imagen.format

        if ancho <= 0 or alto <= 0:
            return False, "Dimensiones invalidas", None, None, None

        return True, "OK", ancho, alto, formato

    except Exception as error:
        return False, str(error), None, None, None


def buscar_metadata_existente(directorio):
    """
    Si ya existe metadata en el directorio, lo leemos para preservar
    fuente/fecha/hora originales de cada archivo.
    """
    candidatos = [
        directorio / "metadata.csv",
        directorio / "metadata_capturas.csv",
    ]
    for c in candidatos:
        if c.exists():
            registros = metadata.leer_metadata(c)
            return {r["archivo"]: r for r in registros}
    return {}


def validar_dataset(directorio, salida, fuente):
    directorio = Path(directorio)
    salida = Path(salida)

    if not directorio.exists():
        print(f"[ERROR] No existe el directorio: {directorio}")
        return

    previos = buscar_metadata_existente(directorio)
    if previos:
        print(f"[INFO] Metadata previa: {len(previos)} registros")
        print("[INFO] Se preservaran fuente/fecha/hora conocidas\n")

    registros = []
    hashes = {}

    total = 0
    validas = 0
    invalidas = 0
    duplicadas = 0

    for clase_dir in sorted(directorio.iterdir()):
        if not clase_dir.is_dir():
            continue
        if clase_dir.name not in CLASES_VALIDAS:
            continue

        clase = clase_dir.name
        print(f"Validando clase: {clase}")

        for archivo in sorted(clase_dir.iterdir()):
            if not archivo.is_file():
                continue

            total += 1
            extension = archivo.suffix.lower()

            previo = previos.get(archivo.name, {})
            fecha = previo.get("fecha_captura") or None
            hora = previo.get("hora_captura") or None
            fuente_registro = previo.get("fuente") or fuente

            if extension not in EXTENSIONES_VALIDAS:
                reg = metadata.crear_registro(
                    archivo=archivo.name,
                    clase=clase,
                    ruta=str(archivo.relative_to(BASE_DIR)),
                    fuente=fuente_registro,
                    tamano_bytes=archivo.stat().st_size,
                    valido=False,
                    motivo="Extension no valida",
                    fecha_captura=fecha,
                    hora_captura=hora,
                )
                registros.append(reg)
                invalidas += 1
                continue

            valido, motivo, ancho, alto, formato = validar_imagen(archivo)
            hash_archivo = ""

            if valido:
                hash_archivo = calcular_hash(archivo)

                if hash_archivo in hashes:
                    duplicadas += 1
                    motivo = f"Duplicada de {hashes[hash_archivo]}"
                else:
                    hashes[hash_archivo] = archivo.name

                validas += 1
            else:
                invalidas += 1

            reg = metadata.crear_registro(
                archivo=archivo.name,
                clase=clase,
                ruta=str(archivo.relative_to(BASE_DIR)),
                fuente=fuente_registro,
                ancho=ancho if ancho else "",
                alto=alto if alto else "",
                formato=formato if formato else "",
                tamano_bytes=archivo.stat().st_size,
                hash_archivo=hash_archivo,
                valido=valido,
                motivo=motivo,
                fecha_captura=fecha,
                hora_captura=hora,
            )
            registros.append(reg)

    metadata.escribir_metadata(registros, salida)

    print("\n" + "=" * 50)
    print("RESULTADO DE VALIDACION")
    print("=" * 50)
    print(f"Directorio:              {directorio}")
    print(f"Total de archivos:       {total}")
    print(f"Imagenes validas:        {validas}")
    print(f"Imagenes invalidas:      {invalidas}")
    print(f"Duplicados detectados:   {duplicadas}")
    print(f"Metadatos escritos en:   {salida}")
    print("=" * 50)


def parsear_argumentos():
    parser = argparse.ArgumentParser(
        description="Valida imagenes y genera metadata.csv"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=str(DIR_DEFECTO),
        help="Directorio con subcarpetas de clases (default: data/processed)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Archivo CSV de salida (default: <dir>/metadata.csv)",
    )
    parser.add_argument(
        "--fuente",
        type=str,
        default=FUENTE_DEFECTO,
        choices=sorted(metadata.FUENTES_VALIDAS),
        help="Fuente asignada a archivos nuevos (default: dataset_publico)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parsear_argumentos()

    dir_path = Path(args.dir)
    out_path = Path(args.out) if args.out else dir_path / "metadata.csv"

    validar_dataset(dir_path, out_path, args.fuente)