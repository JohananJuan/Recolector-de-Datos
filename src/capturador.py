import sys
import time
import hashlib
from pathlib import Path

import cv2
from PIL import Image

# Aseguramos que se pueda importar metadata.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
import metadata


# Directorio raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Donde guardamos las capturas propias
CAPTURAS_DIR = BASE_DIR / "data" / "raw" / "capturas"

# Metadata exclusiva de las capturas
METADATA_CAPTURAS = CAPTURAS_DIR / "metadata_capturas.csv"

# Clases disponibles y su tecla de acceso
CLASES = {
    "1": "papel",
    "2": "carton",
    "3": "tela",
}

CLASES_ORDEN = ["papel", "carton", "tela"]

# Fuente por defecto (cambia a "prototipo" cuando uses la cinta)
FUENTE_DEFECTO = "captura_controlada"

# Indice de camara (0 = integrada)
CAMARA_INDICE = 0

# Extension y calidad de guardado
EXTENSION = ".jpg"
CALIDAD_JPEG = 95

# Resolucion deseada
RESOLUCION = (1280, 720)

# Segundos entre capturas en modo automatico
INTERVALO_AUTO = 3.0


def calcular_hash(archivo):
    """SHA-256 del archivo."""
    sha256 = hashlib.sha256()
    with open(archivo, "rb") as f:
        for bloque in iter(lambda: f.read(8192), b""):
            sha256.update(bloque)
    return sha256.hexdigest()


def siguiente_numero(clase):
    """
    Devuelve el siguiente numero disponible para nombrar archivos
    de esa clase, mirando los que ya existen con sufijo _cap_.
    """
    carpeta = CAPTURAS_DIR / clase
    carpeta.mkdir(parents=True, exist_ok=True)

    prefijo = f"{clase}_cap_"
    existentes = [
        f for f in carpeta.iterdir()
        if f.is_file() and f.suffix.lower() == EXTENSION
        and f.stem.startswith(prefijo)
    ]

    if not existentes:
        return 1

    numeros = []
    for f in existentes:
        resto = f.stem[len(prefijo):]
        if resto.isdigit():
            numeros.append(int(resto))

    return max(numeros) + 1 if numeros else 1


def contar_por_clase():
    """Devuelve {clase: cantidad} de capturas existentes."""
    conteo = {}
    prefijo = None
    for clase in CLASES_ORDEN:
        carpeta = CAPTURAS_DIR / clase
        if not carpeta.exists():
            conteo[clase] = 0
            continue
        prefijo = f"{clase}_cap_"
        conteo[clase] = sum(
            1 for f in carpeta.iterdir()
            if f.is_file()
            and f.suffix.lower() == EXTENSION
            and f.stem.startswith(prefijo)
        )
    return conteo


def guardar_captura(frame, clase):
    """
    Guarda el frame como jpg y registra el metadata.
    Devuelve la ruta guardada o None si fallo.
    """
    carpeta = CAPTURAS_DIR / clase
    carpeta.mkdir(parents=True, exist_ok=True)

    numero = siguiente_numero(clase)
    nombre = f"{clase}_cap_{numero:05d}{EXTENSION}"
    destino = carpeta / nombre

    ok = cv2.imwrite(
        str(destino),
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, CALIDAD_JPEG],
    )

    if not ok:
        print(f"[ERROR] No se pudo guardar {destino}")
        return None

    with Image.open(destino) as img:
        ancho, alto = img.size
        formato = img.format

    tamano = destino.stat().st_size
    hash_archivo = calcular_hash(destino)

    fecha, hora = metadata.ahora()

    registro = metadata.crear_registro(
        archivo=nombre,
        clase=clase,
        ruta=str(destino.relative_to(BASE_DIR)),
        fuente=FUENTE_DEFECTO,
        ancho=ancho,
        alto=alto,
        formato=formato,
        tamano_bytes=tamano,
        hash_archivo=hash_archivo,
        valido=True,
        motivo="OK",
        fecha_captura=fecha,
        hora_captura=hora,
    )

    # Append al CSV de capturas
    registros = metadata.leer_metadata(METADATA_CAPTURAS)
    registros.append(registro)
    metadata.escribir_metadata(registros, METADATA_CAPTURAS)

    return destino


def dibujar_hud(frame, clase_actual, conteo, modo_auto):
    """Dibuja la interfaz sobre el frame."""
    alto, ancho = frame.shape[:2]

    # Barra superior
    cv2.rectangle(frame, (0, 0), (ancho, 100), (30, 30, 30), -1)

    cv2.putText(
        frame,
        f"Clase: {clase_actual.upper()}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2,
    )

    modo_texto = "AUTO" if modo_auto else "MANUAL"
    color_modo = (0, 200, 255) if modo_auto else (200, 200, 200)
    cv2.putText(
        frame,
        f"Modo: {modo_texto}",
        (20, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color_modo,
        2,
    )

    # Conteos
    y = 140
    cv2.putText(
        frame, "Capturas propias:", (20, y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
    )
    y += 30
    for clase in CLASES_ORDEN:
        marcador = ">" if clase == clase_actual else " "
        color = (0, 255, 0) if clase == clase_actual else (200, 200, 200)
        cv2.putText(
            frame,
            f"{marcador} {clase:8} {conteo[clase]:4}",
            (30, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            1,
        )
        y += 28

    # Ayuda inferior
    ayuda = "ESPACIO: capturar | 1/2/3: clase | A: auto | Q: salir"
    cv2.rectangle(frame, (0, alto - 40), (ancho, alto), (30, 30, 30), -1)
    cv2.putText(
        frame, ayuda, (20, alto - 12),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1,
    )

    return frame


def capturar():
    CAPTURAS_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(CAMARA_INDICE)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la camara.")
        print("Verifica que no este siendo usada por otra app.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

    clase_actual = "papel"
    modo_auto = False
    ultima_auto = 0.0

    print("\n" + "=" * 50)
    print(" CAPTURADOR DE RESIDUOS")
    print("=" * 50)
    print(" ESPACIO  -> capturar")
    print(" 1/2/3    -> papel / carton / tela")
    print(f" A        -> modo automatico (cada {INTERVALO_AUTO:.0f}s)")
    print(" Q        -> salir")
    print("=" * 50 + "\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] No se pudo leer frame de la camara.")
                break

            frame = cv2.resize(frame, RESOLUCION)

            conteo = contar_por_clase()
            frame = dibujar_hud(frame, clase_actual, conteo, modo_auto)

            cv2.imshow("Capturador", frame)

            tecla = cv2.waitKey(1) & 0xFF

            if tecla == ord("q") or tecla == ord("Q"):
                break

            elif tecla == ord(" "):
                ruta = guardar_captura(frame, clase_actual)
                if ruta:
                    print(f"[OK] Guardado: {ruta.name}")
                    flash = frame.copy()
                    cv2.rectangle(
                        flash, (0, 0),
                        (RESOLUCION[0], RESOLUCION[1]),
                        (255, 255, 255), -1,
                    )
                    mezcla = cv2.addWeighted(frame, 0.3, flash, 0.7, 0)
                    cv2.imshow("Capturador", mezcla)
                    cv2.waitKey(80)

            elif tecla in (ord("1"), ord("2"), ord("3")):
                clase_actual = CLASES[chr(tecla)]
                print(f"[CLASE] {clase_actual}")

            elif tecla == ord("a") or tecla == ord("A"):
                modo_auto = not modo_auto
                ultima_auto = time.time()
                estado = "ACTIVADO" if modo_auto else "DESACTIVADO"
                print(f"[AUTO] Modo automatico {estado}")

            if modo_auto and (time.time() - ultima_auto) >= INTERVALO_AUTO:
                ruta = guardar_captura(frame, clase_actual)
                if ruta:
                    print(f"[AUTO] Guardado: {ruta.name}")
                ultima_auto = time.time()

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\nCapturador cerrado.")


if __name__ == "__main__":
    capturar()