"""name: clave API; label: texto; required: obligatorio; secret: contraseña; choices: opciones."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Field:
    """name: clave API; label: texto; required: obligatorio; secret: contraseña; choices: opciones."""
    name: str
    label: str
    required: bool = True
    secret: bool = False
    choices: tuple = ()
