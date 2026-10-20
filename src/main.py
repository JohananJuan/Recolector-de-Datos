import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.rutas import BASE_DIR, CAPTURAS_DIR, METADATA_CAPTURAS

SRC_DIR = BASE_DIR / "src"


def ejecutar_modulo(modulo: str, args: list[str] | None = None) -> None:
    cmd = [sys.executable, "-m", modulo]
    if args:
        cmd.extend(args)
    print(f"\n>>> Ejecutando: {' '.join(cmd)}  (cwd={SRC_DIR})\n")
    subprocess.run(cmd, cwd=str(SRC_DIR), check=False)


def menu() -> None:
    while True:
        print("\n" + "=" * 60)
        print(" CLASIFICADOR DE RESIDUOS")
        print("=" * 60)
        print(" 1. Recolectar dataset externo (archive -> processed)")
        print(" 2. Capturar imagenes propias (camara)")
        print(" 3. Validar dataset procesado (publico)")
        print(" 4. Validar capturas propias")
        print(" 5. Analizar dataset procesado")
        print(" 6. Marcar outliers en metadata (no elimina)")
        print(" 7. Exportar splits train/val/test por sesion")
        print(" 8. Salir")
        print("=" * 60)

        opcion = input("Seleccione una opcion: ").strip()

        if opcion == "1":
            ejecutar_modulo("recolector")
        elif opcion == "2":
            ejecutar_modulo("capturador")
        elif opcion == "3":
            ejecutar_modulo("validador")
        elif opcion == "4":
            ejecutar_modulo("validador", [
                "--dir", str(CAPTURAS_DIR),
                "--out", str(METADATA_CAPTURAS),
                "--fuente", "captura_controlada",
            ])
        elif opcion == "5":
            ejecutar_modulo("analizador")
        elif opcion == "6":
            ejecutar_modulo("limpieza.marcar_outliers")
        elif opcion == "7":
            ejecutar_modulo("division.exportar")
        elif opcion == "8":
            print("Saliendo...")
            break
        else:
            print("[!] Opcion no valida.")


if __name__ == "__main__":
    menu()