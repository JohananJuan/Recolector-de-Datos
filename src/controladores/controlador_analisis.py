from controladores.analisis_lectura import AnalisisLectura
from controladores.analisis_limpieza import AnalisisLimpieza


class ControladorAnalisis:

    def __init__(self):
        self._lectura = AnalisisLectura()
        self._limpieza = AnalisisLimpieza()

    def cargar_dataframe(self, *a, **kw):
        return self._lectura.cargar_dataframe(*a, **kw)

    def resumen_numerico(self, *a, **kw):
        return self._lectura.resumen_numerico(*a, **kw)

    def extraer_y_limpiar(self, *a, **kw):
        return self._limpieza.extraer_y_limpiar(*a, **kw)

    def analizar_y_exportar(self, raiz, salida_xlsx):
        df_crudo, df_limpio, comparativa, metricas = (
            self._limpieza.extraer_y_limpiar(raiz)
        )
        ruta = self._limpieza.exportar(
            df_crudo, df_limpio, comparativa, metricas, salida_xlsx
        )
        return {
            "ruta_excel": ruta,
            "filas_crudas": len(df_crudo),
            "filas_limpias": len(df_limpio),
            "metricas": metricas,
        }