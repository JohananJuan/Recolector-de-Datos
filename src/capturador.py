import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cv2

from core.rutas import CAPTURAS_DIR, CLASES_VALIDAS
from controladores.controlador_captura import ControladorCaptura
from servicios.trigger import EventoTrigger


TECLAS_CLASE = {"1": "papel", "2": "carton", "3": "tela"}
CAMARA_INDICE = 0
RESOLUCION = (1280, 720)
INTERVALO_AUTO_TIEMPO = 3.0


def dibujar_hud(frame, ctrl: ControladorCaptura, clase_actual: str, modo_tiempo: bool):
    alto, ancho = frame.shape[:2]
    cv2.rectangle(frame, (0, 0), (ancho, 110), (30, 30, 30), -1)

    cv2.putText(frame, f"Clase: {clase_actual.upper()}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    modo = []
    if ctrl.auto_habilitado():
        modo.append("SENSOR")
    if modo_tiempo:
        modo.append("TIEMPO")
    texto_modo = "+".join(modo) if modo else "MANUAL"
    cv2.putText(frame, f"Modo: {texto_modo}", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 200, 255) if modo else (200, 200, 200), 2)

    if ctrl.auto_habilitado():
        lectura = ctrl.lectura_sensor()
        if lectura and lectura.valida:
            cv2.putText(frame, f"{lectura.distancia_cm:.1f} cm | {lectura.estado}",
                        (20, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 255, 0), 1)

    y = 150
    cv2.putText(frame, "Capturas propias:", (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    y += 30
    conteo = ctrl.contar_por_clase()
    for clase in CLASES_VALIDAS:
        marcador = ">" if clase == clase_actual else " "
        color = (0, 255, 0) if clase == clase_actual else (200, 200, 200)
        cv2.putText(frame, f"{marcador} {clase:8} {conteo[clase]:4}",
                    (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
        y += 28

    ayuda = " "
    cv2.rectangle(frame, (0, alto - 40), (ancho, alto), (30, 30, 30), -1)
    cv2.putText(frame, ayuda, (20, alto - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    return frame


def capturar(puerto_sensor: str | None = None):
    CAPTURAS_DIR.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(CAMARA_INDICE)
    if not cap.isOpened():
        print("[ERROR] No se pudo abrir la cámara.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUCION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

    ctrl = ControladorCaptura()
    clase_actual = "papel"
    modo_tiempo = False
    ultima_auto_tiempo = 0.0

    print("\n" + "=" * 50)
    print(" CAPTURADOR DE RESIDUOS")
    print("=" * 50)
    print(" ESPACIO  -> capturar")
    print(" 1/2/3    -> papel / carton / tela")
    print(f" A        -> modo automático por tiempo ({INTERVALO_AUTO_TIEMPO:.0f}s)")
    print(" S        -> modo automático por sensor ultrasónico")
    print(" Q        -> salir")
    print("=" * 50 + "\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] No se pudo leer frame.")
                break
            frame = cv2.resize(frame, RESOLUCION)

            evento = ctrl.procesar_frame_auto(frame)
            if evento == EventoTrigger.ACTIVAR:
                print("[SENSOR] Objeto detectado")
            elif evento == EventoTrigger.DESACTIVAR:
                print("[SENSOR] Objeto fuera de rango")
            elif evento == EventoTrigger.CAPTURAR:
                flash = frame.copy()
                cv2.rectangle(flash, (0, 0), RESOLUCION, (255, 255, 255), -1)
                cv2.addWeighted(frame, 0.3, flash, 0.7, 0, frame)

            frame = dibujar_hud(frame, ctrl, clase_actual, modo_tiempo)
            cv2.imshow("Capturador", frame)

            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), ord("Q")):
                break
            elif tecla == ord(" "):
                ruta = ctrl.guardar(frame, clase_actual)
                if ruta:
                    print(f"[OK] Guardado: {ruta.name}")
            elif tecla in (ord("1"), ord("2"), ord("3")):
                clase_actual = TECLAS_CLASE[chr(tecla)]
                print(f"[CLASE] {clase_actual}")
            elif tecla in (ord("a"), ord("A")):
                modo_tiempo = not modo_tiempo
                ultima_auto_tiempo = time.time()
                print(f"[AUTO-TIEMPO] {'ON' if modo_tiempo else 'OFF'}")
            elif tecla in (ord("s"), ord("S")):
                if ctrl.auto_habilitado():
                    ctrl.deshabilitar_auto()
                    print("[AUTO-SENSOR] OFF")
                else:
                    ok = ctrl.habilitar_auto(clase_actual, puerto=puerto_sensor)
                    estado = "ON" if ok else "FALLÓ (¿Arduino conectado?)"
                    print(f"[AUTO-SENSOR] {estado}")

            if modo_tiempo and (time.time() - ultima_auto_tiempo) >= INTERVALO_AUTO_TIEMPO:
                ruta = ctrl.guardar(frame, clase_actual)
                if ruta:
                    print(f"[AUTO-TIEMPO] Guardado: {ruta.name}")
                ultima_auto_tiempo = time.time()
    finally:
        ctrl.deshabilitar_auto()
        cap.release()
        cv2.destroyAllWindows()
        print("\nCapturador cerrado.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", default=None,
                        help="Puerto serial del Arduino (ej. COM3 o /dev/ttyUSB0)")
    args = parser.parse_args()
    capturar(puerto_sensor=args.puerto)