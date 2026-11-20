from __future__ import annotations
import pandas as pd
from limpieza.etapas.limpieza_datos import EtapaLimpieza
from limpieza.etapas.correlacion import EtapaCorrelacion
from limpieza.etapas.discretizacion import EtapaDiscretizacion
from limpieza.etapas.texto import EtapaTexto
from limpieza.etapas.normalizacion_etapa import EtapaNormalizacion


def _df_ejemplo() -> pd.DataFrame:
    return pd.DataFrame({
        "ruta": [f"img_{i}.jpg" for i in range(10)],
        "brillo_medio": [50, 60, 70, 80, 90, 100, 110, 120, 130, 140],
        "varianza_laplaciano": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        "ruido_estimado": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "clase": ["Botella", "botella ", "BOTELLA"] * 3 + ["Botella"],
    })


def test_limpieza_devuelve_df():
    df = _df_ejemplo()
    res = EtapaLimpieza().aplicar(df)
    assert res.ok
    assert isinstance(res.df, pd.DataFrame)


def test_correlacion_detecta_pares():
    df = _df_ejemplo()
    df["copia_brillo"] = df["brillo_medio"]
    res = EtapaCorrelacion(umbral=0.9).aplicar(df)
    pares = res.metricas["pares_correlacionados"]
    assert any(p["a"] == "brillo_medio" and p["b"] == "copia_brillo" for p in pares)


def test_correlacion_elimina_columnas_si_se_pide():
    df = _df_ejemplo()
    df["copia_brillo"] = df["brillo_medio"]
    res = EtapaCorrelacion(umbral=0.9, eliminar=True).aplicar(df)
    assert "copia_brillo" not in res.df.columns


def test_discretizacion_agrega_columna_discreta():
    df = _df_ejemplo()
    res = EtapaDiscretizacion(columna="brillo_medio", bins=3).aplicar(df)
    assert "brillo_medio_discreto" in res.df.columns
    assert res.df["brillo_medio_discreto"].notna().any()


def test_normalizacion_zscore():
    df = _df_ejemplo()
    res = EtapaNormalizacion(metodo="zscore").aplicar(df)
    assert abs(res.df["brillo_medio"].mean()) < 1e-6


def test_texto_normaliza_clase():
    df = _df_ejemplo()
    res = EtapaTexto(columna="clase").aplicar(df)
    assert "clase_norm" in res.df.columns
    assert set(res.df["clase_norm"].unique()) == {"botella"}