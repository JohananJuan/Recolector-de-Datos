import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"


def ejecutar(script, args=None):
    """Ejecuta un script de src/ como subproceso."""
    cmd = [sys.executable, str(SRC_DIR / script)]
    if args:
        cmd.extend(args)
    print(f"\n>>> Ejecutando: {' '.join(cmd)}\n")
    subprocess.run(cmd, check=False)


def menu():
    while True:
        print("\n" + "=" * 55)
        print(" CLASIFICADOR DE RESIDUOS")
        print("=" * 55)
        print(" 1. Recolectar dataset externo (archive -> processed)")
        print(" 2. Capturar imagenes propias (camara)")
        print(" 3. Validar dataset procesado (publico)")
        print(" 4. Validar capturas propias")
        print(" 5. Analizar dataset procesado")
        print(" 6. Salir")
        print("=" * 55)

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            ejecutar("recolector.py")

        elif opcion == "2":
            ejecutar("capturador.py")

        elif opcion == "3":
            ejecutar("validador.py")

        elif opcion == "4":
            ejecutar("validador.py", [
                "--dir", str(BASE_DIR / "data" / "raw" / "capturas"),
                "--out", str(BASE_DIR / "data" / "raw" / "capturas" / "metadata_capturas.csv"),
                "--fuente", "captura_controlada",
            ])

        elif opcion == "5":
            ejecutar("analizador.py")

        elif opcion == "6":
            print("Saliendo...")
            break

        else:
            print("[!] Opcion no valida.")


if __name__ == "__main__":
    menu()