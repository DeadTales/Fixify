"""Construye los servicios con una sola sesión HTTP compartida."""
from services.api_client import ApiClient
from services.auth_service import AuthService
from services.clients_service import ClientsService
from services.equipment_service import EquipmentService
from services.users_service import UsersService


class Services:
    """Contenedor inyectable para evitar clientes globales en las vistas."""

    def __init__(self, api=None):
        """api: transporte opcional; si se omite utiliza la configuración local."""
        self.api = api if api is not None else ApiClient()
        self.auth = AuthService(self.api)
        self.clients = ClientsService(self.api)
        self.equipment = EquipmentService(self.api)
        self.users = UsersService(self.api)
