import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.rutas import BASE_DIR, CLASES_VALIDAS
from metadata.repositorio import RepositorioMetadata
from metadata.dominio import RegistroMetadata, ruta_relativa
from limpieza.pipeline import PipelineValidacion


class ServicioValidacion:
    def __init__(self, pipeline: PipelineValidacion, repo: RepositorioMetadata):
        self._pipeline = pipeline
        self._repo = repo

    def validar_directorio(self, directorio: Path, salida: Path, fuente: str) -> dict:
        directorio = Path(directorio)
        salida = Path(salida)

        if not directorio.exists():
            raise FileNotFoundError(f"No existe el directorio: {directorio}")

        previos = {r.archivo: r for r in self._repo.leer(salida)}
        if previos:
            print(f"[INFO] Metadata previa: {len(previos)} registros (se preservara trazabilidad)")

        registros: list[RegistroMetadata] = []

        # ✅ Estado compartido: UNA sola instancia para todo el run.
        # Las reglas mutan estos objetos in-place y el estado sobrevive
        # aunque un archivo corte el pipeline antes de deduplicar.
        estado: dict = {"hashes_sha": {}, "hashes_phash": []}

        total = validas = invalidas = revisar = 0

        for clase_dir in sorted(directorio.iterdir()):
            if not clase_dir.is_dir() or clase_dir.name not in CLASES_VALIDAS:
                continue
            clase = clase_dir.name
            print(f"Validando clase: {clase}")

            for archivo in sorted(clase_dir.iterdir()):
                if not archivo.is_file():
                    continue
                total += 1

                # ctx comparte referencias con `estado` para los acumuladores
                ctx = {
                    "hashes_sha": estado["hashes_sha"],
                    "hashes_phash": estado["hashes_phash"],
                    "clase": clase,
                    "ruta_rel": ruta_relativa(archivo, BASE_DIR),
                    "fuente": fuente,
                }
                resultado = self._pipeline.validar_archivo(archivo, ctx)

                previo = previos.get(archivo.name)
                reg = RegistroMetadata(
                    archivo=archivo.name,
                    clase=clase,
                    ruta=ctx["ruta_rel"],
                    fuente=(previo.fuente if previo and previo.fuente else fuente),
                    fecha_captura=(previo.fecha_captura if previo else ""),
                    hora_captura=(previo.hora_captura if previo else ""),
                    camara=(previo.camara if previo else ""),
                    sesion=(previo.sesion if previo else ""),
                    version_dataset=(previo.version_dataset if previo else ""),
                    ancho=resultado.extras.get("ancho", ""),
                    alto=resultado.extras.get("alto", ""),
                    formato=resultado.extras.get("formato", ""),
                    tamano_bytes=archivo.stat().st_size,
                    hash=resultado.extras.get("hash", ""),
                    phash=resultado.extras.get("phash", ""),
                    valido=resultado.valido,
                    motivo=resultado.motivo,
                )
                registros.append(reg)

                if resultado.severidad == "invalida":
                    invalidas += 1
                elif resultado.severidad == "revisar":
                    revisar += 1
                    validas += 1
                else:
                    validas += 1

        self._repo.escribir(registros, salida)

        resumen = {
            "directorio": str(directorio),
            "salida": str(salida),
            "total": total,
            "validas": validas,
            "invalidas": invalidas,
            "revisar": revisar,
        }
        self._imprimir_resumen(resumen)
        return resumen

    @staticmethod
    def _imprimir_resumen(r: dict) -> None:
        print("\n" + "=" * 55)
        print("RESULTADO DE VALIDACION")
        print("=" * 55)
        print(f"Directorio:            {r['directorio']}")
        print(f"Total de archivos:     {r['total']}")
        print(f"Validas:               {r['validas']}")
        print(f"  - marcadas revisar:  {r['revisar']}")
        print(f"Invalidas:             {r['invalidas']}")
        print(f"Metadata escrita en:   {r['salida']}")
        print("=" * 55)