import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt5.QtWidgets import QApplication, QDesktopWidget
from ui.estilos import QSS
from ui.ventana_principal import VentanaPrincipal


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(QSS)
    win = VentanaPrincipal()

    pantalla = QDesktopWidget().availableGeometry()
    marco = win.frameGeometry()
    marco.moveCenter(pantalla.center())
    win.move(marco.topLeft())

    win.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())