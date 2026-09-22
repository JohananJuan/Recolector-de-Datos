from pathlib import Path
import shutil


# Directorio raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorio donde esta el dataset original
RAW_DIR = BASE_DIR / "data" / "raw" / "archive"

# Directorio donde guardaremos las clases seleccionadas
PROCESSED_DIR = BASE_DIR / "data" / "processed"


# Relacion entre las carpetas originales y nuestras clases
CLASES = {
    "1-Cardboard": "carton",
    "6-Paper": "papel",
    "8-Textile Trash": "tela",
}


# Extensiones de imagenes que aceptaremos
EXTENSIONES_VALIDAS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def recolectar_datos():

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"No se encontro el dataset en: {RAW_DIR}"
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    total = 0

    for carpeta_original, clase_destino in CLASES.items():

        origen = RAW_DIR / carpeta_original
        destino = PROCESSED_DIR / clase_destino

        if not origen.exists():
            print(f"[ADVERTENCIA] No existe: {origen}")
            continue

        destino.mkdir(parents=True, exist_ok=True)

        archivos = [
            archivo
            for archivo in origen.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower() in EXTENSIONES_VALIDAS
        ]

        print(f"\nClase: {clase_destino}")
        print(f"Origen: {origen}")
        print(f"Imagenes encontradas: {len(archivos)}")

        for numero, archivo in enumerate(archivos, start=1):

            nuevo_nombre = f"{clase_destino}_{numero:05d}{archivo.suffix.lower()}"

            destino_archivo = destino / nuevo_nombre

            shutil.copy2(archivo, destino_archivo)

            total += 1

        print(f"Imagenes copiadas: {len(archivos)}")

    print(f"TOTAL DE IMAGENES RECOLECTADAS: {total}")


if __name__ == "__main__":
    recolectar_datos()
