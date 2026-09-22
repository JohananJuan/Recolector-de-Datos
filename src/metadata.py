from pathlib import Path
from datetime import datetime
import csv


# Directorio raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# Esquema oficial del CSV. El orden importa.
CAMPOS = [
    "archivo",
    "clase",
    "ruta",
    "fuente",
    "fecha_captura",
    "hora_captura",
    "ancho",
    "alto",
    "formato",
    "tamano_bytes",
    "hash",
    "valido",
    "motivo",
]


# Valores permitidos para el campo "fuente"
FUENTES_VALIDAS = {
    "dataset_publico",
    "captura_controlada",
    "prototipo",
}


def ahora():

    momento = datetime.now()
    return momento.strftime("%Y-%m-%d"), momento.strftime("%H:%M:%S")


def registro_vacio():

    return {campo: "" for campo in CAMPOS}


def crear_registro(
    archivo,
    clase,
    ruta,
    fuente,
    ancho="",
    alto="",
    formato="",
    tamano_bytes="",
    hash_archivo="",
    valido=True,
    motivo="OK",
    fecha_captura=None,
    hora_captura=None,
):

    if fecha_captura is None or hora_captura is None:
        fecha_auto, hora_auto = ahora()
        fecha_captura = fecha_captura or fecha_auto
        hora_captura = hora_captura or hora_auto

    if fuente not in FUENTES_VALIDAS:
        raise ValueError(
            f"Fuente '{fuente}' no valida. "
            f"Usa una de: {sorted(FUENTES_VALIDAS)}"
        )

    return {
        "archivo": archivo,
        "clase": clase,
        "ruta": ruta,
        "fuente": fuente,
        "fecha_captura": fecha_captura,
        "hora_captura": hora_captura,
        "ancho": ancho,
        "alto": alto,
        "formato": formato,
        "tamano_bytes": tamano_bytes,
        "hash": hash_archivo,
        "valido": valido,
        "motivo": motivo,
    }


def escribir_metadata(registros, destino):

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with open(destino, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        escritor.writeheader()
        for registro in registros:
            escritor.writerow(registro)

    return destino


def leer_metadata(origen):

    origen = Path(origen)

    if not origen.exists():
        return []

    with open(origen, "r", newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        return list(lector)


def leer_hashes(origen):

    hashes = {}
    for registro in leer_metadata(origen):
        valido = str(registro.get("valido", "")).lower() in ("true", "1", "yes")
        if valido and registro.get("hash"):
            hashes[registro["hash"]] = registro["archivo"]
    return hashes


def parsear_bool(valor):

    return str(valor).strip().lower() in ("true", "1", "yes", "si", "sí")