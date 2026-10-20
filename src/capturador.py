import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cv2

from core.rutas import CAPTURAS_DIR, METADATA_CAPTURAS, CLASES_VALIDAS
from metadata.repositorio import nuevo_repositorio
from servicios.captura import ServicioCaptura


TECLAS_CLASE = {"1": "papel", "2": "carton", "3": "tela"}
CAMARA_INDICE = 0
RESOLUCION = (1280, 720)
INTERVALO_AUTO = 3.0


def dibujar_hud(frame, clase_actual, conteo, modo_auto):
    alto, ancho = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (ancho, 100), (30, 30, 30), -1)
    cv2.putText(frame, f"Clase: {clase_actual.upper()}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    modo_texto = "AUTO" if modo_auto else "MANUAL"
    color_modo = (0, 200, 255) if modo_auto else (200, 200, 200)
    cv2.putText(frame, f"Modo: {modo_texto}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_modo, 2)

    y = 140
    cv2.putText(frame, "Capturas propias:", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    y += 30
    for clase in CLASES_VALIDAS:
        marcador = ">" if clase == clase_actual else " "
        color = (0, 255, 0) if clase == clase_actual else (200, 200, 200)
        cv2.putText(frame, f"{marcador} {clase:8} {conteo[clase]:4}", (30, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        y += 28

    ayuda = "ESPACIO: capturar | 1/2/3: clase | A: auto | Q: salir"
    cv2.rectangle(frame, (0, alto - 40), (ancho, alto), (30, 30, 30), -1)
    cv2.putText(frame, ayuda, (20, alto - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return frame


def capturar():
    CAPTURAS_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(CAMARA_INDICE)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la camara.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

    repo = nuevo_repositorio()
    servicio = ServicioCaptura(repo, METADATA_CAPTURAS, camara="webcam_0")

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
                print("[ERROR] No se pudo leer frame.")
                break
            frame = cv2.resize(frame, RESOLUCION)
            conteo = servicio.contar_por_clase()
            frame = dibujar_hud(frame, clase_actual, conteo, modo_auto)
            cv2.imshow("Capturador", frame)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), ord("Q")):
                break
            elif tecla == ord(" "):
                ruta = servicio.guardar(frame, clase_actual)
                if ruta:
                    print(f"[OK] Guardado: {ruta.name}")
                    flash = frame.copy()
                    cv2.rectangle(flash, (0, 0), RESOLUCION, (255, 255, 255), -1)
                    mezcla = cv2.addWeighted(frame, 0.3, flash, 0.7, 0)
                    cv2.imshow("Capturador", mezcla)
                    cv2.waitKey(80)
            elif tecla in (ord("1"), ord("2"), ord("3")):
                clase_actual = TECLAS_CLASE[chr(tecla)]
                print(f"[CLASE] {clase_actual}")
            elif tecla in (ord("a"), ord("A")):
                modo_auto = not modo_auto
                ultima_auto = time.time()
                estado = "ACTIVADO" if modo_auto else "DESACTIVADO"
                print(f"[AUTO] Modo automatico {estado}")

            if modo_auto and (time.time() - ultima_auto) >= INTERVALO_AUTO:
                ruta = servicio.guardar(frame, clase_actual)
                if ruta:
                    print(f"[AUTO] Guardado: {ruta.name}")
                ultima_auto = time.time()
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\nCapturador cerrado.")


if __name__ == "__main__":
    capturar()