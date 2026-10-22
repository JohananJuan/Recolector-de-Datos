# src/test_controlador_sensor.py
import time
from controladores.controlador_captura import ControladorCaptura

print("[TEST] Creando controlador...")
ctrl = ControladorCaptura()
print(f"[TEST] auto_habilitado antes = {ctrl.auto_habilitado()}")

print("[TEST] Activando sensor (autodetección)...")
ok = ctrl.habilitar_auto("papel", puerto=None)
print(f"[TEST] habilitar_auto → {ok}")
print(f"[TEST] auto_habilitado ahora = {ctrl.auto_habilitado()}")

if ok:
    print("[TEST] Leyendo 10 segundos de sensor...")
    for i in range(100):
        lectura = ctrl.lectura_sensor()
        if lectura:
            print(f"  t={i*0.1:.1f}s  {lectura.distancia_cm} cm | {lectura.estado}")
        else:
            print(f"  t={i*0.1:.1f}s  (sin lectura)")
        time.sleep(0.1)
    ctrl.deshabilitar_auto()
    print("[TEST] Fin")
else:
    print("[TEST] No se pudo activar. Revisa logs arriba.")