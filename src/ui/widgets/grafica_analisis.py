from __future__ import annotations

from typing import Mapping, Sequence

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QSizePolicy, QVBoxLayout, QWidget


class GraficaAnalisis(QWidget):

    FONDO = "#181825"
    EJE = "#45475a"
    TEXTO = "#cdd6f4"
    PALETA = ["#89b4fa", "#a6e3a1", "#f9e2af", "#f38ba8",
              "#cba6f7", "#94e2d5", "#fab387", "#b4befe"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._figura = Figure(figsize=(6, 3.2), dpi=100, facecolor=self.FONDO)
        self._canvas = FigureCanvasQTAgg(self._figura)
        self._canvas.setStyleSheet(f"background:{self.FONDO};")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

    def barras(self, conteos: Mapping[str, float], titulo: str,
               horizontal: bool = False) -> None:
        self._figura.clear()
        ax = self._figura.add_subplot(111)
        ax.set_facecolor(self.FONDO)

        etiquetas = list(conteos.keys())
        valores = list(conteos.values())
        color = self.PALETA[0]

        if horizontal:
            barras = ax.barh(etiquetas, valores, color=color)
            for b, v in zip(barras, valores):
                ax.text(v, b.get_y() + b.get_height() / 2,
                        f" {v:.2f}" if isinstance(v, float) else f" {v}",
                        va="center", color=self.TEXTO, fontsize=8)
            ax.invert_yaxis()
        else:
            barras = ax.bar(etiquetas, valores, color=color)
            for b, v in zip(barras, valores):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                        f"{v:.2f}" if isinstance(v, float) else f"{v}",
                        ha="center", va="bottom",
                        color=self.TEXTO, fontsize=8)

        self._estilizar(ax, titulo)

    def pastel(self, conteos: Mapping[str, float], titulo: str) -> None:
        self._figura.clear()
        ax = self._figura.add_subplot(111)
        ax.set_facecolor(self.FONDO)

        etiquetas = list(conteos.keys())
        valores = list(conteos.values())
        wedges, texts, autotexts = ax.pie(
            valores, labels=etiquetas, autopct="%1.1f%%",
            colors=self.PALETA[:len(valores)],
            textprops={"color": self.TEXTO, "fontsize": 9},
            startangle=90,
        )
        for a in autotexts:
            a.set_color("#1e1e2e")
            a.set_fontweight("bold")

        ax.set_title(titulo, color=self.TEXTO, fontsize=11, pad=10)
        ax.axis("equal")
        self._figura.tight_layout()
        self._canvas.draw_idle()

    def lineas(self, datos: pd.DataFrame, titulo: str,
               x: str, y_cols: Sequence[str]) -> None:
        self._figura.clear()
        ax = self._figura.add_subplot(111)
        ax.set_facecolor(self.FONDO)

        for i, col in enumerate(y_cols):
            if col not in datos.columns:
                continue
            ax.plot(datos[x], datos[col],
                    color=self.PALETA[i % len(self.PALETA)],
                    marker="o", markersize=3, label=col)

        ax.legend(facecolor=self.FONDO, edgecolor=self.EJE,
                  labelcolor=self.TEXTO, fontsize=8)
        self._estilizar(ax, titulo, xlabel=x)

    def dispersion(self, datos: pd.DataFrame, titulo: str,
                   x: str, y: str, color_por: str | None = None) -> None:
        self._figura.clear()
        ax = self._figura.add_subplot(111)
        ax.set_facecolor(self.FONDO)

        if color_por and color_por in datos.columns:
            for i, (nombre, grupo) in enumerate(datos.groupby(color_por)):
                ax.scatter(grupo[x], grupo[y],
                           color=self.PALETA[i % len(self.PALETA)],
                           label=str(nombre), alpha=0.7, s=20)
            ax.legend(facecolor=self.FONDO, edgecolor=self.EJE,
                      labelcolor=self.TEXTO, fontsize=8)
        else:
            ax.scatter(datos[x], datos[y],
                       color=self.PALETA[0], alpha=0.7, s=20)

        self._estilizar(ax, titulo, xlabel=x, ylabel=y)

    def histograma(self, serie: pd.Series, titulo: str, bins: int = 30) -> None:
        self._figura.clear()
        ax = self._figura.add_subplot(111)
        ax.set_facecolor(self.FONDO)

        ax.hist(serie.dropna(), bins=bins,
                color=self.PALETA[0], edgecolor=self.EJE)
        self._estilizar(ax, titulo, ylabel="Frecuencia")

    def _estilizar(self, ax, titulo: str,
                   xlabel: str = "", ylabel: str = "") -> None:
        ax.set_title(titulo, color=self.TEXTO, fontsize=11, pad=10)
        ax.tick_params(colors=self.TEXTO, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(self.EJE)
        if xlabel:
            ax.set_xlabel(xlabel, color=self.TEXTO, fontsize=9)
        if ylabel:
            ax.set_ylabel(ylabel, color=self.TEXTO, fontsize=9)
        ax.grid(axis="y", color=self.EJE, linestyle="--", alpha=0.3)
        ax.set_axisbelow(True)
        self._figura.tight_layout()
        self._canvas.draw_idle()