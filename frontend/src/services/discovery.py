"""Encuentra servicios locales para construir el contenedor Services.

Cada archivo *_service.py define una clase de ModuleService. service_name
indica su atributo público; si falta, se usa el nombre del archivo sin sufijo.
Solo descubre clases: Services las instancia con el ApiClient compartido.
Los imports ejecutan código de módulo; mantener estos archivos sin efectos
secundarios. Un error de importación se propaga para detectar fallos al iniciar.
"""
from importlib import import_module
from pkgutil import iter_modules

from services.api_client import ModuleService


def service_classes():
    """Retorna dict de clave pública -> clase; no recibe parámetros.

    Lanza ValueError para claves inválidas o duplicadas. Una clase importada
    desde otro módulo se ignora para no registrar el mismo servicio dos veces.
    Ejemplo: orders_service.py + OrdersService -> {'orders': OrdersService}.
    """
    # Import local: Services importa discovery durante su propia inicialización.
    import services

    found = {}

    for entry in sorted(iter_modules(services.__path__), key=lambda item: item.name):
        if not entry.name.endswith('_service'):
            continue

        module = import_module(f'services.{entry.name}')

        # __module__ distingue las clases propias de las que solo se importaron.
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, ModuleService)
                and value.__module__ == module.__name__
            ):
                name = getattr(
                    value,
                    'service_name',
                    entry.name.removesuffix('_service'),
                )

                # La clave debe poder usarse como services.nombre y no ocultar api.
                if (
                    not isinstance(name, str)
                    or not name.isidentifier()
                    or name.startswith('_')
                    or name == 'api'
                ):
                    raise ValueError(f'Nombre de servicio inválido: {name!r}')

                if name in found:
                    raise ValueError(f'Servicio duplicado: {name}')

                found[name] = value

    return found
