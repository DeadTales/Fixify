"""Encuentra vistas locales y prepara las entradas del menú según el rol.

Una vista hereda AsyncFrame y declara menu_label, allowed_roles y,
opcionalmente, menu_order. No crea widgets ni instancias de las vistas.
Los módulos se importan: evitar efectos secundarios al nivel del archivo.
Este filtro controla presentación; la API debe autorizar cada operación.
"""
from importlib import import_module
from pkgutil import iter_modules

from ui.components import AsyncFrame


def available_views(role):
    """role: código API como admin, recepcion o tecnico.

    Retorna lista de (etiqueta, clase), ordenada por menu_order y etiqueta.
    Sin etiqueta o sin el rol en allowed_roles, la vista no se muestra.
    menu_order vale 100 si se omite. Los errores de importación se propagan.
    """
    import ui.views

    views = []

    for entry in iter_modules(ui.views.__path__):
        if entry.name.startswith('_') or entry.name == 'discovery':
            continue

        # Ignora módulos internos y este descubridor para evitar autorregistro.
        module = import_module(f'ui.views.{entry.name}')

        for cls in vars(module).values():
            if (
                isinstance(cls, type)
                and issubclass(cls, AsyncFrame)
                and cls.__module__ == module.__name__
                and getattr(cls, 'menu_label', None)
                and role in getattr(cls, 'allowed_roles', ())
            ):
                views.append(cls)

    views.sort(key=lambda cls: (getattr(cls, 'menu_order', 100), cls.menu_label))
    return [(cls.menu_label, cls) for cls in views]
