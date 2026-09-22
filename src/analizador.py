from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# Directorio raiz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

METADATA_FILE = BASE_DIR / "data" / "processed" / "metadata.csv"

REPORT_DIR = BASE_DIR / "logs"


def analizar_dataset():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(METADATA_FILE)

    print("ANALISIS DEL DATASET")


    print("\nINFORMACION GENERAL")

    print(f"Total de registros: {len(df)}")
    print(f"Columnas: {len(df.columns)}")


    print("\nVALORES FALTANTES")

    faltantes = df.isnull().sum()

    for columna, cantidad in faltantes.items():
        print(f"{columna}: {cantidad}")


    conteo_clases = df["clase"].value_counts()

    print("\nDISTRIBUCION POR CLASE")

    for clase, cantidad in conteo_clases.items():
        porcentaje = (cantidad / len(df)) * 100

        print(
            f"{clase:10} : "
            f"{cantidad:4} imagenes "
            f"({porcentaje:.2f}%)"
        )


    print("\nDIMENSIONES DE LAS IMAGENES")

    print(
        f"Ancho minimo:  {df['ancho'].min()}"
    )

    print(
        f"Ancho maximo:  {df['ancho'].max()}"
    )

    print(
        f"Ancho promedio: {df['ancho'].mean():.2f}"
    )

    print(
        f"Alto minimo:   {df['alto'].min()}"
    )

    print(
        f"Alto maximo:   {df['alto'].max()}"
    )

    print(
        f"Alto promedio: {df['alto'].mean():.2f}"
    )


    print("\nFORMATOS")

    formatos = df["formato"].value_counts()

    for formato, cantidad in formatos.items():
        print(f"{formato}: {cantidad}")


    print("\nTAMANO DE LOS ARCHIVOS")

    promedio_bytes = df["tamano_bytes"].mean()

    promedio_mb = promedio_bytes / (1024 ** 2)

    print(f"Tamano promedio: {promedio_mb:.2f} MB")


    plt.figure(figsize=(8, 5))

    conteo_clases.plot(kind="bar")

    plt.title("Cantidad de imagenes por clase")
    plt.xlabel("Clase")
    plt.ylabel("Cantidad de imagenes")
    plt.xticks(rotation=0)
    plt.tight_layout()

    grafica_clases = REPORT_DIR / "distribucion_clases.png"

    plt.savefig(grafica_clases, dpi=150)
    plt.close()


    plt.figure(figsize=(7, 7))

    conteo_clases.plot(
        kind="pie",
        autopct="%1.1f%%",
        startangle=90
    )

    plt.title("Distribucion porcentual del dataset")
    plt.ylabel("")
    plt.tight_layout()

    grafica_porcentaje = REPORT_DIR / "distribucion_porcentual.png"

    plt.savefig(grafica_porcentaje, dpi=150)
    plt.close()


    print("ANALISIS COMPLETADO")

    print(f"Grafica de clases: {grafica_clases}")
    print(f"Grafica porcentual: {grafica_porcentaje}")

    print("\nProceso terminado correctamente.")


if __name__ == "__main__":
    analizar_dataset()
