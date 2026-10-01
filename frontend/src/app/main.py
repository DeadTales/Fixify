# app/main.py

import sys
import os

# Obtener la ruta absoluta de la carpeta 'src' y ponerla al inicio de la búsqueda
RUTA_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RUTA_SRC not in sys.path:
    sys.path.insert(0, RUTA_SRC)

from ui.login import VentanaLogin

if __name__ == "__main__":
    app = VentanaLogin()
    app.mainloop()