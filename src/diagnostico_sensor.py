import sys
import time
import traceback

print("=" * 60)
print(" DIAGNÓSTICO DEL SENSOR ULTRASÓNICO")
print("=" * 60)

print("\n[1] Verificando pyserial...")
try:
    import serial
    import serial.tools.list_ports as list_ports
    print(f"    ✓ pyserial {serial.__version__} instalado")
except ImportError as e:
    print(f"    ✗ pyserial NO instalado: {e}")
    print("    Solución: pip install pyserial")
    sys.exit(1)

print("\n[2] Puertos seriales detectados por el sistema:")
puertos = list(list_ports.comports())
if not puertos:
    print("    ✗ NINGÚN puerto serial detectado.")
    print("    → Revisa: ¿ESP32 conectada? ¿Driver CH340/CP210x instalado?")
    print("    → Abre Administrador de dispositivos y mira 'Puertos (COM y LPT)'")
    sys.exit(2)

for p in puertos:
    print(f"    • {p.device}")
    print(f"        descripción : {p.description}")
    print(f"        fabricante  : {p.manufacturer}")
    print(f"        hwid        : {p.hwid}")
    print(f"        vid:pid     : {p.vid:04X}:{p.pid:04X}" if p.vid else "        vid:pid     : —")

if len(sys.argv) > 1:
    puerto = sys.argv[1]
else:
    candidatos = [
        p.device for p in puertos
        if any(k in p.description.upper() or k in (p.hwid or "").upper()
               for k in ("USB", "ACM", "CH340", "CP210", "UART", "SERIAL"))
    ]
    puerto = candidatos[0] if candidatos else puertos[0].device

print(f"\n[3] Puerto elegido: {puerto}")

print(f"\n[4] Abriendo {puerto} a 115200 baudios...")
try:
    ser = serial.Serial(puerto, 115200, timeout=2)
    print(f"    ✓ Puerto abierto")
except serial.SerialException as e:
    print(f"    ✗ No se pudo abrir: {e}")
    print("    Causas típicas:")
    print("      - Monitor serie del IDE de Arduino ABIERTO → ciérralo")
    print("      - Otro programa usando el puerto (PuTTY, PlatformIO...)")
    print("      - Driver mal instalado")
    print("      - La ESP32 se está reiniciando (espera 2s y reintenta)")
    sys.exit(3)

print(f"\n[5] Leyendo 8 segundos de datos...")
print("    (Deberías ver líneas tipo: 'Distancia: 123.4 cm | ESTADO: LIBRE')")
print("-" * 60)

try:
    time.sleep(2.5)
    ser.reset_input_buffer()

    t0 = time.time()
    lineas = 0
    lineas_validas = 0
    while time.time() - t0 < 8:
        try:
            linea = ser.readline().decode(errors="replace").rstrip()
        except Exception as e:
            print(f"    ✗ Error leyendo: {e}")
            break
        if not linea:
            continue
        lineas += 1
        print(f"    RAW[{lineas:03d}] {linea!r}")

        import re
        if re.search(r"Distancia:\s*(SIN LECTURA|[\d.]+)", linea):
            lineas_validas += 1

    print("-" * 60)
    print(f"\n[6] Resumen:")
    print(f"    Líneas recibidas : {lineas}")
    print(f"    Líneas con formato válido : {lineas_validas}")
    if lineas == 0:
        print("    ✗ NO llegó ningún dato.")
        print("      → ¿El sketch tiene el Serial.begin(115200) y los Serial.println?")
        print("      → ¿El monitor serie del IDE está cerrado?")
        print("      → Prueba con el Monitor Serie del IDE a 115200: ¿ves texto?")
    elif lineas_validas == 0:
        print("    ✗ Llegaron datos pero con formato distinto.")
        print("      → El sketch en la ESP32 no coincide con el que pegaste.")
        print("      → Revisa las líneas RAW de arriba y adapta el regex.")
    else:
        print("    ✓ Todo OK: el sensor envía datos parseables.")

finally:
    ser.close()
    print("\n[7] Puerto cerrado. Fin del diagnóstico.")