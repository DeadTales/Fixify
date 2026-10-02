"""Construye los servicios con una sola sesión HTTP compartida."""
from services.api_client import ApiClient
from services.discovery import service_classes


class Services:
    """Contenedor inyectable para evitar clientes globales en las vistas."""

    def __init__(self, api=None):
        """api: transporte opcional; si se omite utiliza la configuración local."""

        self.api = api if api is not None else ApiClient()

        # Cada archivo *_service.py aporta un ModuleService. Todos reciben la
        # misma API; añadir un servicio no exige editar este contenedor.
        for name, service_class in service_classes().items():
            if hasattr(self, name):
                raise ValueError(f'Nombre de servicio reservado: {name}')

            setattr(self, name, service_class(self.api))
