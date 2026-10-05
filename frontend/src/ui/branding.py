"""Carga el logo en el login, navegación e iconos de ventana."""
from pathlib import Path
from PIL import Image, ImageTk

LOGO_PATH = Path(__file__).resolve().parents[1] / 'assets' / 'img' / 'Logo Fixify.png'


def load_logo(master, size):
    """master: widget Tk propietario; size: ancho y alto máximos en píxeles."""

    with Image.open(LOGO_PATH) as source:
        logo = source.convert('RGBA')
        logo.thumbnail(size, Image.Resampling.LANCZOS)

    return ImageTk.PhotoImage(logo, master=master)


def set_window_icon(window):
    """window: ventana; conserva la imagen para que Tk no elimine el icono."""

    window._fixify_icon = load_logo(window, (64, 64))
    window.iconphoto(False, window._fixify_icon)
