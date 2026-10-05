"""Entrada de escritorio: python frontend/src/app/main.py desde la raíz."""
from pathlib import Path
import sys

# Permite imports de app, services y ui al ejecutar este archivo directamente.
RUTA_SRC = str(Path(__file__).resolve().parents[1])
if RUTA_SRC not in sys.path:
    sys.path.insert(0, RUTA_SRC)

from ui.login import VentanaLogin


if __name__ == '__main__':
    app = VentanaLogin()
    app.mainloop()
